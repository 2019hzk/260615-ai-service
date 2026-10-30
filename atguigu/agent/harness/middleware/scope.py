from typing import Callable, Awaitable

from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse

from atguigu.agent.harness.rules.skill import SKILL_CATALOG
from atguigu.agent.harness.run.context import AgentRuntimeContext, AgentRuntimeState
from atguigu.agent.llm.output import AgentOutput


class SkillScopeMiddleware(AgentMiddleware[AgentRuntimeContext, AgentRuntimeState, AgentOutput]):

    async def awrap_model_call(
            self,
            request: ModelRequest[AgentRuntimeContext],
            handler: Callable[[ModelRequest[AgentRuntimeContext]], Awaitable[ModelResponse[AgentOutput]]]
    ) -> ModelResponse[AgentOutput]:
        """
        职责：选择指定技能对应的工具
        :param request:
        :param handler:
        :return:
        """

        # 1. 指定技能更新的特殊工具
        allow_tool_name = ["load_skill"]

        # 2. 获取技能码
        skill_code = request.state.get("active_skill_code")

        # 3. 判断技能码
        if skill_code is not None:
            skill_definition = SKILL_CATALOG.get_definition(skill_code)

            allow_tool_name.extend(skill_definition.tools)

        # 4. 选择留下技能对应的工具
        visible_tools = [tool for tool in request.tools if tool.name in allow_tool_name]

        # 5. 更新请求
        return await handler(request.override(tools=visible_tools,model_settings={"parallel_tool_calls": False}))
