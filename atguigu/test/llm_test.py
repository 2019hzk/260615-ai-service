"""

1. 直接使用langchain-openai包提供的ChatOpenAI(通用，只要模型提供上提供的模型兼容OpenAI协议)
2. 直接使用精确包提供的langchain-deepseek包提供ChatDeepSeek
选择技巧：能用精确的就用精确的，反正才用通用的（1. 思考链 2. 结构化输出）
结构化输出: (让模型)json格式的字符串--（Pydantic）-->数据模型对象
方式一：提示词+json_object(淘汰)
方式二：function_calling(提示词不需要额外强调输出json格式、比较稳、通用)
方式三：json_schema(提示词不需要额外强调输出json格式、最稳、不是所有现代大语言模型都支持) 如果支持该方式优先使用这种方式。


langchain方式获取结构化对象
1. 如果不用agent方式，使用with_structured_output（）获取：参数1：schema=数据模型 参数2：method=json_object/function_calling/json_schema
2. 如果用agent方式:create_agent(response_format=数据模型)

区别：
1. 如果使用方式1，langchain底层会优先看模型是否支持json_schema,如果支持，直接用json_schema,如果不支持，才用function_calling
2。 如果使用方式2：除了open_ai自己的模型，用 json_schema，其他兼容OpenAI协议的模型都不用json_schema，function_calling


kimi-k3:模型自己支持json_schema
create_agent（）---->function_calling
with_structured_output（）--->json_schema


deepseek模型：只支持工具调用，不支持json_schema


"""

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_deepseek import ChatDeepSeek
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field


class User(BaseModel):
    name: str = Field(description="用户的名字")
    age: int = Field(description="用户的年龄")
    skills: list[str] = Field(description="用户掌握的技能")


async def structured_output_km():
    """
    演示：
    :return: 支持json_schema的kimi_k3模型，用with_structured_output，最终选择的仍然是json_schema能力
    """
    km_model = ChatOpenAI(base_url="https://api.moonshot.cn/v1",
                          api_key="sk-lsCd9YWkVdTdShyf68E8WVw8n4BH99yceOaoebhBwHVlSzmn",
                          model="kimi-k3",
                          )

    runnable_object = km_model.with_structured_output(User)

    result = await runnable_object.ainvoke("我的名字叫tom,年龄18，熟练掌握的技能有Python、Java、Vue")

    print(result)


async def structured_output_2_ds():
    """
    演示：
    :return: 不支持json_schema的deepseek-flash模型，用with_structured_output，method指定json_schema报400，指定function_calling没有任何问题。
    结论：deepseek只支持function_calling
    """
    ds_model = ChatOpenAI(base_url="https://api.deepseek.com",
                          api_key="sk-796dac6acb3641858729c0d1cf8804d5",
                          model="deepseek-flash",
                          extra_body={"thinking": {"type": "disabled"}}
                          )

    runnable_object = ds_model.with_structured_output(User, method="function_calling")

    result = await runnable_object.ainvoke("我的名字叫tom,年龄18，熟练掌握的技能有Python、Java、Vue")

    print(result)


async def structured_output_2_ds_1():
    ds_model = ChatDeepSeek(base_url="https://api.deepseek.com",
                            api_key="sk-796dac6acb3641858729c0d1cf8804d5",
                            model="deepseek-flash",
                            extra_body={"thinking": {"type": "disabled"}})

    runnable_object = ds_model.with_structured_output(User)

    result = await runnable_object.ainvoke("我的名字叫tom,年龄18，熟练掌握的技能有Python、Java、Vue")

    print(repr(result))


async def structured_output_3_ca():
    """
    演示： create_agent创建时指定结构化对象，只要是兼容OpenAI协议的都是function_calling
    :return:
    结论：
    """
    qw_model = ChatOpenAI(base_url="https://llm-zk5vlasmrhfv20fy.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
                          api_key="sk-ws-H.YMYPPRR.g1uD.MEUCIQDwXWabWMo3VDj3wZKbPsxWT2eVLNsPp3pzgb7vlJGwbgIgaYGwL4qfgsq1FN934Au64vYI92wSph6HQavtZtnP_VM",
                          model="qwen-plus"
                          )
    agent = create_agent(
        model=qw_model,
        tools=[],
        response_format=User
    )

    result = await agent.ainvoke({
        "messages": [HumanMessage(content="我的名字叫tom,年龄18，熟练掌握的技能有Python、Java、Vue")]
    })

    response = result['structured_response']
    print(repr(response))


if __name__ == '__main__':
    pass
    # asyncio.run(structured_output())
    # asyncio.run(structured_output_1())
    # asyncio.run(structured_output_2_ds_1())
