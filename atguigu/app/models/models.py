from typing import Any
from datetime import datetime

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text

from atguigu.app.models.enums import AgentTraceStatus
from atguigu.common.utils import get_uid, get_utcnow


class Base(DeclarativeBase):
    pass


class AgentTrace(Base):
    """记录 AI 对一次轮次的执行轨迹和最终结果。"""

    __tablename__ = "agent_traces"

    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: get_uid("trace"))
    conversation_id: Mapped[str] = mapped_column(String(80), index=True)
    status: Mapped[str] = mapped_column(String(30), default=AgentTraceStatus.RUNNING, index=True)
    model_name: Mapped[str] = mapped_column(String(120))
    prompt_version: Mapped[str] = mapped_column(String(80))
    result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utcnow)


class AgentToolCall(Base):
    """记录一次 Agent 业务工具调用及其执行结果。"""

    __tablename__ = "agent_tool_calls"

    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: get_uid("tool"))
    trace_id: Mapped[str] = mapped_column(ForeignKey("agent_traces.id"), index=True)
    tool_call_id: Mapped[str] = mapped_column(String(120))
    tool_name: Mapped[str] = mapped_column(String(80), index=True)
    arguments: Mapped[dict[str, Any]] = mapped_column(JSON)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    success: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utcnow)


class KnowledgeChunk(Base):
    """存储上传的 PDF 知识文档内容。"""

    __tablename__ = "knowledge_chunks"

    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: get_uid("kb"))
    file_name: Mapped[str] = mapped_column(String(200), index=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utcnow)
