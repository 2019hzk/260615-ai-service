import logging
import time
from typing import Any

from langchain_core.messages import BaseMessage, SystemMessage
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from langchain_core.callbacks import UsageMetadataCallbackHandler

from atguigu.agent.harness.run.context import AgentRuntimeContext, build_messages
from atguigu.agent.harness.validator.validator import Validator, ValidateOutputError
from atguigu.app.models.enums import AgentTraceStatus
from atguigu.app.models.models import AgentTrace
from atguigu.app.schemas import AgentRunRequest
from atguigu.common.settings import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentExecutor:

    def __init__(self, session: AsyncSession, agent: Any):
        self._settings = get_settings()
        self._session = session
        self._agent = agent
        self._validator = Validator(session)

    async def start_run(self, payload: AgentRunRequest, access_token: str) -> dict[str, Any]:
        """
        职责：
        1. 保存运行轨迹
        2. 执行Agent(完成Agent推理)
        :param payload:
        :param access_token:
        :return:
        """

        # 1. 初始化AgentTrace
        agent_trace = AgentTrace(
            conversation_id=payload.conversation_id,
            status=AgentTraceStatus.RUNNING,
            model_name=self._settings.llm_model,
            prompt_version=self._settings.prompt_version,
        )

        self._session.add(agent_trace)
        await self._session.commit()

        # 2. 构建Agent运行时上下文
        start_time = time.perf_counter()
        runtime_context = AgentRuntimeContext(
            access_token=access_token,
            trace_id=agent_trace.id
        )
        # 3. 执行Agent
        try:
            run_result, input_tokens, output_tokens = await self._execute_agent(runtime_context, payload)
        except Exception as exc:
            logger.exception("Agent执行会话conversation_id=%s,失败原因exc=%s", payload.conversation_id, str(exc))
            agent_trace.status = AgentTraceStatus.FAILED
            agent_trace.result = {"text": f"Agent执行失败，原因：{str(exc)}"}
            agent_trace.latency_ms = int((time.perf_counter() - start_time) * 1000)
            await self._session.commit()
            raise HTTPException(status_code=500, detail="AI 服务调用失败") from exc

        # 3. 正常执行完Agent
        agent_trace.status = AgentTraceStatus.COMPLETED
        agent_trace.result = run_result
        agent_trace.latency_ms = int((time.perf_counter() - start_time) * 1000)
        agent_trace.input_tokens = input_tokens
        agent_trace.output_tokens = output_tokens
        await self._session.commit()

        # 4. 返回Agent运行后的结果
        return run_result

    async def _execute_agent(self,
                             runtime_context: AgentRuntimeContext,
                             payload: AgentRunRequest) -> tuple[dict[str, Any], int, int]:
        """
        职责：执行Agent 返回Agent运行后的结果以及tokens用量（输入tokens用量、输出tokens用量）
        :param runtime_context:
        :param payload:
        :return:
        _agent.invoke()返回的结果：dict结构
            字典结构中有:所有的消息【Human/System/AI】元数据（usage_metadata:tokens用量）
            如果指定了response_format,还可以获取到结构化的输出对象
            如果指定了state_schema，还可以获取到修改后的状态
        """
        # 1. 构建消息
        messages: list[BaseMessage] = build_messages(payload)

        # 2. 创建回调处理器
        call_back = UsageMetadataCallbackHandler()
        validated_result: dict[str, Any] = {}

        # 3. 执行Agent推理
        for attempt in range(self._settings.agent_max_attempts):
            try:
                state: dict[str, Any] = await self._agent.ainvoke(
                    {"messages": messages},
                    context=runtime_context,
                    config={"callbacks": [call_back]}
                )
                validated_result: dict[str, Any] = await self._validator.validate(
                    state['structured_response'],
                    state['active_skill_code'],
                    runtime_context.trace_id
                )
                break

            # 4. 推理期间出错(重试)
            except ValidateOutputError as exc:
                if attempt == self._settings.agent_max_attempts - 1:
                    raise
                messages = [
                    *state["messages"],
                    SystemMessage(
                        content=f"上一次回复未通过校验：{exc}，请修正后重新回复。"
                    ),
                ]

        # 5. 构建输入输出的token用量
        input_tokens, output_tokens = self._summarize_tokens(call_back)

        # 6. 返回最终Agent结果以及token用量
        return validated_result, input_tokens, output_tokens

    @staticmethod
    def _summarize_tokens(call_back: UsageMetadataCallbackHandler) -> tuple[int, int]:

        all_model_metadata: list[dict[str, Any]] = list(call_back.usage_metadata.values())

        input_tokens = sum(model_metadata.get('input_tokens', 0) for model_metadata in all_model_metadata)
        output_tokens = sum(model_metadata.get('output_tokens', 0) for model_metadata in all_model_metadata)

        return input_tokens, output_tokens
