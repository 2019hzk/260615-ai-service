import json
from dataclasses import dataclass
from typing import Any
from typing_extensions import NotRequired

from langchain.agents import AgentState
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from atguigu.agent.harness.rules.skill import SKILL_CATALOG, SkillCode
from atguigu.app.schemas import AgentRunRequest
from atguigu.common.settings import get_settings


@dataclass(slots=True, frozen=True)  # slots:提高存储和查询速度 frozen： 冻结对象的属性个数
class AgentRuntimeContext:
    access_token: str
    trace_id: str


class AgentRuntimeState(AgentState):
    active_skill_code: NotRequired[str]


def build_messages(payload: AgentRunRequest, skill_code: SkillCode | None = None) -> list[BaseMessage]:
    """
    职责：构建Agent运行时需要的消息
    1. 历史消息：多条、角色【USER / AI / HUMAN】
    2. 当前轮次的消息:有可能有多条、角色【USER】
    3. 预加载技能规则：若前置匹配到领域技能，注入对应指导规则
    :return:
    """

    # 1. 构建历史消息
    history_messages: list[dict[str, Any]] = _build_history_messages(payload.history)

    # 2. 标准化消息对象为LangChain统一的消息对象
    messages = [
        HumanMessage(content=_format_message(message))
        if message['role'] == "USER"
        else AIMessage(content=_format_message(message))
        for message in history_messages
    ]

    # 3. 构建当前轮次消息
    current_messages = _build_current_messages(payload.messages)
    messages.append(HumanMessage(content=current_messages))

    # 4. 若匹配到领域技能，将对应技能规则注入上下文
    if skill_code is not None:
        skill_definition = SKILL_CATALOG.get_definition(skill_code)
        skill_guidance = "\n".join(f"- {guidance}" for guidance in skill_definition.guidance)
        messages.append(
            SystemMessage(content=f"已经成功加载技能{skill_code}，请遵循以下规则:{skill_guidance}")
        )

    # 5. 返回组合后的消息列表
    return messages


def _build_history_messages(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    职责：构建历史消息【历史消息的裁剪】
    裁剪历史消息的策略：
    策略1：条数
    策略2：字符数
    策略3：
    :param history:
    :return:
    """
    settings = get_settings()

    # 1. 获取候选的消息条数
    candidate_history_messages = history[-settings.history_message_limit:]

    # 2. 计算候选历史消息的字符数（优先选择最近的消息计算字符数） len(message.content)
    usages_total = 0
    messages = []
    for message in reversed(candidate_history_messages):
        message_content_len = len(_format_message(message))
        if message_content_len + usages_total > settings.history_character_budget:
            break

        messages.append(message)
        usages_total += message_content_len

    # 3. 反转为正序
    messages.reverse()

    # 4. 从消息列表中预留第一条消息角色是用户的开始  生成器对象就是一个迭代器对象--->迭代器表达式()  （列表推导式）[]
    user_role_message_index = next((index for index, message in enumerate(messages) if message['role'] == "USER"),
                                   None)

    # 5. 切片返回
    return messages if user_role_message_index is None else messages[user_role_message_index:]


def _format_message(message: dict[str, Any]) -> str:
    """
    职责：格式化单条消息的内容
    消息类型：文本类型、对象【商品、订单】类型
    :param message:
    :return:
    """

    # 1. 消息类型是文本的
    if message['type'] == "text":
        return str(message['content'].get('text'))

    # 2. 消息类型对象的
    message_content = message['content']

    return "该消息是一个对象结构:\n" + json.dumps(message_content, ensure_ascii=False)


def _build_current_messages(messages: list[dict[str, Any]]) -> str:
    """
    职责: 构建当前轮次的用户角色消息
    假设轮次只有一条用户消息：{"role":"USER","type":"object or text","content":"xxxx"}----->"content对应的字符串"
      假设轮次只有一条用户消息：[
                                {"role":"USER","type":"object or text","content":"xxxx"},
                                {"role":"USER","type":"object or text","content":"yyyy"},
                            ]----->"1. xxxx
                                    2. yyyy"

    :param messages:
    :return:
    """
    # 1. 获取当前轮次消息的内容列表
    messages_content = [_format_message(message) for message in messages]

    # 2. 当前轮次只有一条消息
    if len(messages_content) == 1:
        return messages_content[0]

    # 3. 当前轮次有多条消息
    items = "\n".join(f"{i}. {message_content}" for i, message_content in enumerate(messages_content, start=1))

    return "当前用户发送了多条消息，请你作为一个整体来理解，最新轮次的消息是:\n" + items


if __name__ == '__main__':
    list_container = [1, 2, 3, 4]

    print(list_container[4:])
