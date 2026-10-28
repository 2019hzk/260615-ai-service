from langchain.agents import create_agent

from atguigu.agent.harness.middleware.scope import SkillScopeMiddleware
from atguigu.agent.harness.run.context import AgentRuntimeState, AgentRuntimeContext
from atguigu.agent.harness.tools.catalog import TOOL_CATALOG
from atguigu.agent.llm.adapter import get_model_client
from atguigu.agent.llm.output import AgentOutput
from atguigu.agent.llm.prompt import build_system_prompt


def build_agent():
    """
    整个fastapi实例 共用一个agent?
    :return:
    """
    return create_agent(  # type: ignore
        model=get_model_client(),
        system_prompt=build_system_prompt(),
        tools=TOOL_CATALOG.get_agent_tools(),
        middleware=[
            SkillScopeMiddleware()
        ],
        response_format=AgentOutput,
        context_schema=AgentRuntimeContext,
        state_schema=AgentRuntimeState,
        name="智能客服专家"
    )
