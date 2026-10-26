from typing import Annotated, Any
from fastapi import APIRouter, Request

from atguigu.app.dependencies import UserDep, require_internal_service, AgentExecutorDep
from atguigu.app.schemas import AgentRunRequest

router = APIRouter(tags=["Ai Service 运行路由"])


@router.post("/internal/v1/agent/runs")
async def start_run_endpoint(payload: AgentRunRequest,
                             current_user: UserDep,
                             _: Annotated[None, require_internal_service],
                             agent_executor: AgentExecutorDep
                             ) -> dict[str, Any]:
    return agent_executor.start_run(payload, current_user.access_token)
