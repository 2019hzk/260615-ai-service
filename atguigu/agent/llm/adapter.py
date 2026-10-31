"""
根据不同的模型提供商，修改思考方式
1. deepseek---->ChatDeepSeek(extra_body={"thinking":{"typing":"disabled"}})
2. qwen------>ChatOpenAI(extra_body={"enable_thinking":False})

"""
from typing import Any

from langchain_deepseek import ChatDeepSeek
from langchain_openai import ChatOpenAI
from typesafe_sdk import AsyncTypeSafeClient

from atguigu.common.settings import get_settings


def get_model_client():
    """
    职责：获取模型客户端实例
    :return:
    """
    settings = get_settings()

    model_kwargs: dict[str, Any] = {
        "model": settings.llm_model,
        "api_key": settings.llm_api_key,
        "base_url": settings.llm_base_url,
        "timeout": settings.llm_timeout_seconds
    }

    if "deepseek" == settings.llm_provider:
        return ChatDeepSeek(
            **model_kwargs,
            extra_body={
                "thinking": {"type": "disabled"}
            }
        )

    if "qwen" == settings.llm_provider:
        return ChatOpenAI(
            **model_kwargs,
            extra_body={
                "enable_thinking": settings.llm_thinking_mode
            },
            use_responses_api=False  # LangChain新版整合了Response api方式集成了，防止LangChain找错端点
        )
    # 其它的模型提供商各自的私有参数  都可以适配TODO

    return ChatOpenAI(
        **model_kwargs,
        use_responses_api=False
    )


def get_jev_client() -> AsyncTypeSafeClient:
    """获取 TypeSafe Jev 模型客户端实例"""
    settings = get_settings()
    return AsyncTypeSafeClient(
        api_key=settings.typesafe_api_key,
        base_url=settings.typesafe_base_url,
        model=settings.typesafe_model,
    )
