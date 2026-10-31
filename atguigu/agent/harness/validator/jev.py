import logging
from typing import Any

from typesafe_sdk import Choice, Noul, Score

from atguigu.agent.harness.rules.skill import SKILL_CATALOG, SkillCode
from atguigu.agent.harness.validator.validator import ValidateOutputError
from atguigu.agent.llm.adapter import get_jev_client
from atguigu.app.models.models import AgentToolCall

logger = logging.getLogger(__name__)

async def check_input(messages: list[dict[str, Any]]) -> tuple[bool, SkillCode | None, int, int]:
    """
    前置检查用户输入：
    返回 (need_handoff, skill_code, input_tokens, output_tokens)：
    - need_handoff : 用户要求转人工或情绪非常愤怒时为 True
    - skill_code   : 匹配到的领域技能码，日常寒暄时为 None
    - input_tokens : Jev 模型消耗的输入 Token 数
    - output_tokens: Jev 模型消耗的输出 Token 数
    """
    skill_options = {
        skill.skill_code.value: skill.description
        for skill in SKILL_CATALOG.definitions.values()
    }
    skill_options["none"] = "日常礼貌寒暄、打招呼或与电商无关的话题"

    async with get_jev_client() as client:
        response = await client.system_one(
            state=messages,
            questions={
                "skill": Choice(
                    instructions="用户最新问题属于哪个电商客服领域？",
                    criteria=skill_options,
                ),
                "anger": Score(
                    instructions="买家的情绪焦急或愤怒程度如何？",
                    criteria=[
                        "平静正常的业务咨询",
                        "有些焦急或催促",
                        "非常愤怒、投诉或强烈不满",
                    ],
                ),
                "handoff": Noul(
                    instructions="买家明确要求转接人工客服，或遇到严重交易争议需人工介入",
                )
            }
        )

    skill = response.choices["skill"].choice
    anger_score = response.scores["anger"].score
    anger_confidence = response.scores["anger"].confidence
    handoff = response.nouls["handoff"].noul

    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens

    logger.info("Jev 前置检查结果: skill=%s, anger_score=%.2f, anger_confidence=%.2f,handoff=%.2f", skill, anger_score,
                anger_confidence, handoff)

    if (
        handoff >= 0.8
        or anger_score >= 1.5
        or (anger_score >= 1.0 and anger_confidence < 0.4)
    ):
        return True, None, input_tokens, output_tokens

    skill_code = None if skill == "none" else SkillCode(skill)
    return False, skill_code, input_tokens, output_tokens


async def check_output(text: str, complete_tool_calls: list[AgentToolCall]):
    """
    后置语义护栏检查：
    1. readonly  : 客服回复中没有违规承诺已代用户完成取消订单、修改地址或退款等写操作
    2. consistent: 客服回复内容与工具返回的业务数据保持一致，没有捏造或张冠李戴
    """
    state = {
        "evidence": [call.result["data"] for call in complete_tool_calls],
        "reply": text
    }

    async with get_jev_client() as client:
        response = await client.system_one(
            state=state,
            questions={
                "readonly": Noul(
                    instructions="客服回复中没有声称已经代用户完成了取消订单、修改收货地址或办理退款等写操作",
                ),
                "consistent": Noul(
                    instructions="若 evidence 不为空，客服回复中的业务事实与 evidence 完全一致；若 evidence 为空，客服回复仅为日常礼貌寒暄或引导，未编造任何具体业务数据",
                )
            }
        )

    readonly = response.nouls["readonly"].noul
    consistent = response.nouls["consistent"].noul
    logger.info("Jev 后置检查结果: readonly=%.2f, consistent=%.2f", readonly, consistent)

    if readonly < 0.5:
        raise ValidateOutputError("客服只有只读查询权限，不得声称已代用户执行取消订单、修改地址或退款操作")

    if consistent < 0.5:
        raise ValidateOutputError("回复内容在语义上与工具返回结果不符，请严格依据工具结果重新回答")
