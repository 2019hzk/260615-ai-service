from typing import Any

import httpx

from atguigu.common.settings import get_settings


class EcommerceClient:
    """使用当前客户身份访问 Ecommerce Service 接口。"""

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.settings = get_settings()

    async def get_json(
            self,
            resource_path: str,
            query_params: dict[str, Any] | None = None,
    ) -> Any:
        """发送只读请求并返回 JSON 响应数据。"""
        request_url = f"{self.settings.ecommerce_base_url}{resource_path}"
        request_headers = {
            "Authorization": f"Bearer {self.access_token}",
        }
        async with httpx.AsyncClient(
                timeout=self.settings.ecommerce_timeout_seconds,
                trust_env=False,
        ) as http_client:
            response = await http_client.get(
                request_url,
                headers=request_headers,
                params=query_params,
            )
            response.raise_for_status()
            return response.json()
