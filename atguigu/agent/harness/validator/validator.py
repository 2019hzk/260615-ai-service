"""
职责：负责校验LLM的输出


"""
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from atguigu.agent.harness.tools.catalog import ToolCategory, TOOL_CATALOG

from atguigu.agent.llm.output import AgentOutput
from atguigu.app.models.enums import ReplyType, ToolResultCode
from atguigu.app.models.models import AgentToolCall

BUSINESS_FAILURE_MESSAGE = ("暂时无法查询到可靠的订单、商品、物流或售后信息，请您稍后重试，"
                            "或直接发送“转人工”由人工客服为您处理。")


class ValidateOutputError(ValueError):
    pass


from atguigu.agent.harness.validator.action import validate_page_action
from atguigu.agent.harness.validator.anwser import validate_answer

class Validator:

    def __init__(self, session: AsyncSession):
        self._session = session

    async def validate(self,
                       agent_output: AgentOutput,
                       skill_code: str | None,
                       trace_id: str) -> dict[str, Any]:
        """
        职责：根据四种回复类型，分别进行校验，核心校验的回复类型是ANSWER(1.校验active_skill_code 2. 校验回复 3. 页面动作)
        三种回复类型,不需要校验【DECLINE】
        两种：CLARIFY（构建澄清选项） REQUEST_HANDOFF（校验摘要）

        :param agent_output:
        :param skill_code:
        :param trace_id:
        :return:
        """
        # 1. 获取业务事实
        stmt = select(AgentToolCall).where(AgentToolCall.trace_id == trace_id).order_by(AgentToolCall.created_at)
        tool_calls = list((await  self._session.scalars(stmt)).all())
        reply_type = agent_output.reply_type

        # 2. 校验回复类型是ANSWER(可靠的答案)
        if reply_type == ReplyType.ANSWER:

            # 2.1 查询所有的业务类型工具（特殊的工具类型不需要，搜索工具类型目前不校验(可扩展)）
            business_tool_calls = [
                bs_call for bs_call in tool_calls
                if TOOL_CATALOG.get_category(bs_call.tool_name) == ToolCategory.BUSINESS
            ]

            # 2.2 获取所有业务工具已经调用电商接口成功的
            complete_tool_calls = [cs_call for cs_call in business_tool_calls if
                                   cs_call.result['code'] != ToolResultCode.TOOL_CALL_FAILED]

            # 2.3 校验skill-tools的闭环
            if skill_code is not None and not business_tool_calls:
                raise ValidateOutputError(
                    f"已加载技能 {skill_code}，但尚未调用任何查询工具获取数据，请先调用对应工具再回答"
                )
            # 没有调用skill【普通寒暄 需要检验】 or 携带skill && 且调用工具【校验】
            # 2.4 校验answer
            validate_answer(agent_output.text, complete_tool_calls)

            # 2.5 校验page_action
            validated_page_action: dict[str, Any] = validate_page_action(agent_output.page_action, complete_tool_calls)

            # 2.6 构建输出
            return self._build_output(ReplyType.ANSWER,
                                      agent_output.text,
                                      page_action=validated_page_action)

        # 3. 检验回复类型是【转人工请求】REQUEST_HANDOFF
        if reply_type == ReplyType.REQUEST_HANDOFF:
            if agent_output.handoff_summary is None:
                raise ValidateOutputError(f"请求转人工必须提供 handoff_summary")
            return self._build_output(ReplyType.REQUEST_HANDOFF, text=agent_output.text,
                                      handoff_summary=agent_output.handoff_summary
                                      )

        # 4. 校验回复类型是【反问澄清】CLARIFY
        if reply_type == ReplyType.CLARIFY:
            choices = self._build_clarify_choices(tool_calls)
            return self._build_output(ReplyType.CLARIFY, text=agent_output.text, choices=choices)

        # 5. 校验回复类型是【拒绝降级兜底】DECLINE
        return self._build_output(ReplyType.DECLINE, text=BUSINESS_FAILURE_MESSAGE)

    @staticmethod
    def _build_output(
            reply_type: ReplyType,
            text: str,
            *,
            handoff_summary: str | None = None,
            page_action: dict[str, Any] | None = None,
            choices: list[dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        """
        职责：构建AI_Service最终返回给customer-service的结果结构
        :param reply_type:
        :param text:
        :param handoff_summary:
        :param page_action:
        :param choices:
        :return:
        """
        return {
            "reply_type": reply_type,
            "text": text,
            "handoff_summary": handoff_summary,
            "page_action": page_action,
            "choices": choices
        }

    def _build_clarify_choices(self, tool_calls: list[AgentToolCall]) -> list[dict[str, Any]] | None:
        for call in tool_calls:
            if call.tool_name == "list_orders" and call.success:
                return [
                    {
                        "object_type": "order",
                        "object_id": order["id"],
                        "label": f"{order['id']} · {'、'.join(item['product_name'] for item in order['items'])}",
                        "description": f"¥{order['total_amount']} · {order['status_label']}",
                    }
                    for order in call.result['data'][:5]
                ]
        return None
