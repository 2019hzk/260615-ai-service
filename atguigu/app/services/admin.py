from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from atguigu.app.models.models import AgentTrace, AgentToolCall


class AdminService:
    """提供管理员观测 Agent 执行轨迹（AgentTrace）的查询能力。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_metrics(self) -> dict:
        """返回 AgentTrace 汇总指标。"""
        return {
            "agent_runs": await self._scalar(func.count(AgentTrace.id)),
            "average_latency_ms": await self._scalar(func.avg(AgentTrace.latency_ms)),
            "input_tokens": await self._scalar(func.sum(AgentTrace.input_tokens)),
            "output_tokens": await self._scalar(func.sum(AgentTrace.output_tokens)),
        }

    async def _scalar(self, expr):
        return await self.session.scalar(select(expr))

    async def list_runs(self, limit: int) -> list[dict]:
        """返回最近的 Agent 执行轨迹列表。"""
        traces = (
            await self.session.scalars(select(AgentTrace).order_by(AgentTrace.created_at.desc()).limit(limit))).all()
        return [
            {
                "id": trace.id,
                "conversation_id": trace.conversation_id,
                "state": (trace.result or {}).get("reply_type") or trace.status,
                "model_name": trace.model_name,
                "latency_ms": trace.latency_ms,
                "input_tokens": trace.input_tokens,
                "output_tokens": trace.output_tokens
            }
            for trace in traces
        ]

    async def get_run(self, trace_id: str) -> dict:
        """返回一条 AgentTrace 及其关联的工具调用记录。"""
        trace = await self.session.get(AgentTrace, trace_id)
        tool_calls = (
            await self.session.scalars(
                select(AgentToolCall).where(AgentToolCall.trace_id == trace_id).order_by(AgentToolCall.created_at))
        ).all()
        return {
            "run": {
                "id": trace.id,
                "state": (trace.result or {}).get("reply_type") or trace.status,
                "prompt_version": trace.prompt_version,
                "outcome": trace.result,
                "input_tokens": trace.input_tokens,
                "output_tokens": trace.output_tokens
            },
            "tool_calls": [
                {
                    "tool_call_id": call.tool_call_id,
                    "tool_name": call.tool_name,
                    "arguments": call.arguments,
                    "latency_ms": call.latency_ms
                }
                for call in tool_calls
            ]
        }
