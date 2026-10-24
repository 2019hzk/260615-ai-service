import asyncio
from typing import Callable, Awaitable

from langchain.agents import create_agent, AgentState
from langchain.agents.middleware import dynamic_prompt, AgentMiddleware, ModelRequest, ModelResponse
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import tool
from langchain_deepseek import ChatDeepSeek
from langgraph.prebuilt import ToolRuntime
from langgraph.types import Command
from pydantic import BaseModel, Field


class Student(BaseModel):
    name: str = Field(description="学生的姓名")
    score: int = Field(description="学生的分数")
    replay: str = Field(description="给学生的回复")


class StudentContext(BaseModel):
    name: str


class LoginState(AgentState):
    is_login: bool | None


#  工具负责读取外部上下文的数据
# llm先给工具名工具参数个数、工具参数类型<---Agent调用工具
@tool
def login(runtime: ToolRuntime[StudentContext, LoginState]):
    """负责用户登录"""
    print(f"【工具:login】被执行了")
    return Command(
        update={
            "is_login": True,
            "messages": [
                ToolMessage(
                    content="学生已经登录，请你接下来执行get_score工具",
                    tool_call_id=runtime.tool_call_id
                )
            ]
        }
    )


@tool
def get_score(runtime: ToolRuntime[StudentContext, LoginState]):
    """获取学生的分数"""
    student_name = runtime.context.name
    print(f"【工具:get_score】被执行了,获取到用户的名字:{student_name}")

    return f"学生{student_name}的期末Python语言的考试成绩为98分"


@dynamic_prompt
def system_prompt(request: ModelRequest) -> str:
    """
    动态提示词:每次请求LLM之前，Agent（LangChain）调用:Agent执行任务，可能会多次LLM
    :return:
    """
    is_login = request.state.get("is_login")
    print(f"【中间件:@dynamic_prompt】被执行了，is_login={is_login}")
    if not is_login:
        return "你是教务系统助手，负责查询学生的成绩"

    return "你是教务系统助手，请准许以下的规则，学生成绩如果大于90分，请在回复的内容中说明【等级:优秀】"


class LoginCheckMiddleware(AgentMiddleware[StudentContext, LoginState, Student]):
    """
    中间件：主要是为了对Agent处理一次任务的各个阶段去增强接入的
    """

    async def awrap_model_call(
            self,
            request: ModelRequest[StudentContext],
            handler: Callable[[ModelRequest[StudentContext]], Awaitable[ModelResponse[Student]]]
    ) -> ModelResponse[Student]:
        """
        每次请求LLM之前，Agent（LangChain）调用:awrap_model_call，可能会多次LLM
        现在每次调用LLM的时候，暴露的工具具体是哪些。（对Agent身上的工具做选择）
        :param request:
        :param handler:
        :return:
        """
        is_login = request.state.get("is_login")
        allowed_tool_name = {"get_score"} if is_login else {"login"}
        available_tool = [tool for tool in request.tools if tool.name in allowed_tool_name]
        print(f"【中间件:LoginCheckMiddleware】被执行了，本轮给LLM参考的工具:{[t.name for t in available_tool]}")
        return await handler(request.override(tools=available_tool))


async def main_test():
    # 1. 创建模型实例对象
    ds_model = ChatDeepSeek(base_url="https://api.deepseek.com",
                            api_key="sk-796dac6acb3641858729c0d1cf8804d5",
                            model="deepseek-chat",
                            extra_body={"thinking": {"type": "disabled"}})

    # 实例化agent对象
    agent = create_agent(  # type:ignore
        model=ds_model,
        tools=[login, get_score],
        middleware=[
            system_prompt,
            LoginCheckMiddleware()
        ],
        response_format=Student,
        state_schema=LoginState,
        context_schema=StudentContext
    )

    result = await agent.ainvoke({
        "messages": [HumanMessage(content="我的名字叫张三，考试考了98分。")]},
        context=StudentContext(name="张三")
    )

    print(result['structured_response'])


if __name__ == '__main__':
    """
    会调用多少次LLM
    """
    asyncio.run(main_test())
