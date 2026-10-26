from typing import Any, Literal

from pydantic import BaseModel, Field


class CurrentUser(BaseModel):
    user_id: str
    role: Literal["user", "admin"]
    access_token: str


class AgentRunRequest(BaseModel):
    conversation_id: str
    messages: list[dict[str, Any]]
    history: list[dict[str, Any]]
