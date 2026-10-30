from typing import Annotated

from fastapi import Depends, Header, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from atguigu.agent.harness.run.executor import AgentExecutor
from atguigu.app.schemas import CurrentUser
from atguigu.app.services.admin import AdminService
from atguigu.app.services.auth import get_authorized_user
from atguigu.app.services.knowledge import KnowledgeService
from atguigu.common.settings import get_settings
from atguigu.infrastructure.db import get_async_session

SessionDep = Annotated[AsyncSession, Depends(get_async_session)]


def require_user(authorization: Annotated[str | None, Header()] = None) -> CurrentUser:
    return get_authorized_user(authorization, "user")


def require_admin(authorization: Annotated[str | None, Header()] = None) -> CurrentUser:
    return get_authorized_user(authorization, "admin")


def require_internal_service(token: Annotated[str | None, Header(alias="X-Internal-Service-Token")] = None):
    """只允许 Customer Service 调用内部接口"""
    if token != get_settings().internal_service_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无效的内部访问令牌")


def get_agent_executor(session: SessionDep, request: Request):
    agent = request.app.state.agent
    return AgentExecutor(session, agent)


def get_admin_service(session: SessionDep) -> AdminService:
    return AdminService(session)


def get_knowledge_service(session: SessionDep) -> KnowledgeService:
    return KnowledgeService(session)


AgentExecutorDep = Annotated[AgentExecutor, Depends(get_agent_executor)]
UserDep = Annotated[CurrentUser, Depends(require_user)]
AdminDep = Annotated[CurrentUser, Depends(require_admin)]
KnowledgeServiceDep = Annotated[KnowledgeService, Depends(get_knowledge_service)]
AdminServiceDep = Annotated[AdminService, Depends(get_admin_service)]
