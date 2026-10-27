from datetime import UTC, datetime
from uuid import uuid4


def get_uid(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def get_utcnow() -> datetime:
    return datetime.now(UTC)



def normalize_resource_id(resource_id: str) -> str:
    """统一订单、商品、售后等业务编号格式（去空格、转大写、连字符转下划线）。"""
    return resource_id.strip().upper().replace("-", "_")
