from langchain.agents import create_agent
from atguigu.agent.llm.adapter import get_model_client


def build_agent():
    """
    整个fastapi实例 共用一个agent?
    :return:
    """
    return create_agent(
        model=get_model_client(),
        tools=[],
        middleware=[],
        name="智能客服专家"
    )
