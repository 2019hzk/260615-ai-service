import asyncio
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field


class User(BaseModel):
    name: str = Field(description="用户的名字")
    age: int = Field(description="用户的年龄")
    skills: list[str] = Field(description="用户掌握的技能")


async def structured_output_1():
    oa_model = ChatOpenAI(
        model="kimi-k3",
        base_url="https://api.moonshot.cn/v1",
        api_key="sk-g79i9Hu0mfu1Nb9Vmvh5BXj3X9NICxX1dK0NShsthrccrLu7"
    )

    oa_chain = oa_model.with_structured_output(User)  # 'method': 'json_schema'
    print("2. [ChatOpenAI 默认绑定的底层 API 参数]:")
    print("  ", oa_chain.first.kwargs)


async def structured_output_2():
    oa_model = ChatOpenAI(
        model="kimi-k3",
        base_url="https://api.moonshot.cn/v1",
        api_key="sk-g79i9Hu0mfu1Nb9Vmvh5BXj3X9NICxX1dK0NShsthrccrLu7"
    )
    agent = create_agent(
        model=oa_model,
        tools=[],
        response_format=User  # tool_call/function_calling
    )

    result = await agent.ainvoke({
        "messages": [HumanMessage(content="我的名字叫tom,年龄18，熟练掌握的技能有Python、Java、Vue")]
    })

    print(result)


if __name__ == '__main__':
    asyncio.run(structured_output_1())
    asyncio.run(structured_output_2())
