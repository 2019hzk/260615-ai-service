import jwt
from fastapi import HTTPException, status

from atguigu.app.schemas import CurrentUser
from atguigu.common.settings import get_settings


def get_authorized_user(authorization: str | None, required_role: str) -> CurrentUser:
    """解析当前用户并校验接口要求的身份"""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer Token 必须提供")

    access_token = authorization.split(" ", 1)[1]

    current_user = decode_token(access_token)

    if current_user.role != required_role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="当前用户没有接口访问权限")

    return current_user


def decode_token(access_token: str) -> CurrentUser:
    payload = jwt.decode(access_token, get_settings().jwt_secret, algorithms=[get_settings().jwt_algorithm])
    return CurrentUser.model_validate(payload)
