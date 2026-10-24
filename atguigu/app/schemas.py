from typing import Any, Literal

from pydantic import BaseModel, Field


class CurrentUser(BaseModel):
    user_id: str
    role: Literal["user", "admin"]
