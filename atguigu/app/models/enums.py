from enum import StrEnum


class AgentTraceStatus(StrEnum):
    """AgentTrace 执行轨迹状态"""

    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ReplyType(StrEnum):
    """Agent 本轮生成的回复类型枚举。"""

    ANSWER = "ANSWER"
    CLARIFY = "CLARIFY"
    DECLINE = "DECLINE"
    REQUEST_HANDOFF = "REQUEST_HANDOFF"


class ToolResultCode(StrEnum):
    """工具执行结果状态码枚举。"""

    KNOWLEDGE_SEARCH_COMPLETED = "KNOWLEDGE_SEARCH_COMPLETED"
    TOOL_CALL_FAILED = "TOOL_CALL_FAILED"
