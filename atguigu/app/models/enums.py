from enum import StrEnum


class AgentTraceStatus(StrEnum):
    """AgentTrace 执行轨迹状态"""

    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
