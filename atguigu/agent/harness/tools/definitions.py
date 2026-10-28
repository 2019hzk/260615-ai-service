from typing import Annotated
from langchain.tools import ToolRuntime, tool
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from atguigu.agent.harness.rules.skill import SKILL_CATALOG
from atguigu.agent.harness.run.context import AgentRuntimeContext, AgentRuntimeState
from atguigu.common.utils import normalize_resource_id
from atguigu.infrastructure.client import EcommerceClient
from atguigu.agent.harness.tools.executor import tool_executor


@tool
async def search_products(
        query: Annotated[str, "商品名称、类别、规格或用户描述的购买需求"],
        runtime: ToolRuntime[AgentRuntimeContext],
) -> str:
    """
    根据用户需求搜索当前在售商品。
    用户询问某类商品、商品名称或购买建议，但没有明确商品编号时调用。
    返回匹配商品的名称、类别、价格、库存、状态、描述和规格。
    """

    # 1. 创建电商服务客户端对象
    ecommerce_client = EcommerceClient(runtime.context.access_token)

    # 2. 构建查询参数
    query_params = {"query": query}

    # 3. 执行执行工具调用，并且返回工具执行后结果
    return await tool_executor.execute_tool(
        trace_id=runtime.context.trace_id,
        tool_call_id=runtime.tool_call_id,
        tool_name="search_products",
        tool_arguments=query_params,
        operation=lambda: ecommerce_client.get_json("/products", query_params={"query": query})
    )


@tool
async def get_product(
        product_id: Annotated[str, "用户明确提供或商品搜索结果返回的商品编号，例如 PRODUCT_001"],
        runtime: ToolRuntime[AgentRuntimeContext],
) -> str:
    """
    查询一个商品的名称、价格、实时库存、销售状态、描述和规格。
    用户已经明确商品编号，并询问该商品的详情或库存信息时调用。
    """
    # 1. 创建电商服务客户端对象
    ecommerce_client = EcommerceClient(runtime.context.access_token)

    # 2. 规范化商品的编号
    normalized_product_id = normalize_resource_id(product_id)

    # 3. 执行执行工具调用，并且返回工具执行后结果
    return await tool_executor.execute_tool(
        trace_id=runtime.context.trace_id,
        tool_call_id=runtime.tool_call_id,
        tool_name="get_product",
        tool_arguments={"product_id": normalized_product_id},
        operation=lambda: ecommerce_client.get_json(f"/products/{normalized_product_id}")
    )


@tool
async def list_orders(runtime: ToolRuntime[AgentRuntimeContext]) -> str:
    """
    查询当前用户的订单列表。
    用户询问自己的订单但没有明确订单编号时调用。
    返回订单编号、状态、金额、创建时间和商品信息，只读取数据，不执行订单操作。
    """
    # 1. 创建电商服务客户端对象
    ecommerce_client = EcommerceClient(runtime.context.access_token)

    # 2. 执行执行工具调用，并且返回工具执行后结果
    return await tool_executor.execute_tool(
        trace_id=runtime.context.trace_id,
        tool_call_id=runtime.tool_call_id,
        tool_name="list_orders",
        tool_arguments={},
        operation=lambda: ecommerce_client.get_json("/orders")
    )


@tool
async def get_order(
        order_id: Annotated[str, "用户明确提供或订单列表返回的订单编号，例如 ORDER_001"],
        runtime: ToolRuntime[AgentRuntimeContext],
) -> str:
    """
    查询当前用户的一条订单详情。
    用户已经明确订单编号，并询问该订单的状态、金额、创建时间或商品信息时调用。
    只读取数据，不取消订单、退款或修改地址。
    """

    # 1. 创建电商服务客户端对象
    ecommerce_client = EcommerceClient(runtime.context.access_token)

    # 2. 规范订单编号
    normalized_order_id = normalize_resource_id(order_id)

    # 3. 执行执行工具调用，并且返回工具执行后结果
    return await tool_executor.execute_tool(
        trace_id=runtime.context.trace_id,
        tool_call_id=runtime.tool_call_id,
        tool_name="get_order",
        tool_arguments={"order_id": normalized_order_id},
        operation=lambda: ecommerce_client.get_json(f"/orders/{normalized_order_id}")
    )


@tool
async def get_logistics(
        order_id: Annotated[str, "用户明确提供或订单列表返回的订单编号，例如 ORDER_001"],
        runtime: ToolRuntime[AgentRuntimeContext],
) -> str:
    """
    查询一个订单的物流公司、运单号、状态和物流轨迹。
    用户已经明确订单编号，并询问该订单的配送进度或物流信息时调用。
    订单基础信息应使用 get_order 查询。
    """
    # 1. 创建电商服务客户端对象
    ecommerce_client = EcommerceClient(runtime.context.access_token)

    # 规范订单编号
    normalized_order_id = normalize_resource_id(order_id)

    # 3. 执行执行工具调用，并且返回工具执行后结果
    return await tool_executor.execute_tool(
        trace_id=runtime.context.trace_id,
        tool_call_id=runtime.tool_call_id,
        tool_name="get_logistics",
        tool_arguments={"order_id": normalized_order_id},
        operation=lambda: ecommerce_client.get_json(f"/orders/{normalized_order_id}/logistics")
    )


@tool
async def list_after_sales(
        runtime: ToolRuntime[AgentRuntimeContext],
        order_id: Annotated[str | None, "可选的订单编号；提供后只查询该订单的售后记录"] = None,
) -> str:
    """
    查询当前用户的售后申请记录。
    用户询问退款、退货或换货申请的处理进度时调用。
    已经明确订单编号时按订单查询，否则返回当前客户的全部售后记录。
    """

    # 1. 创建电商服务客户端对象
    ecommerce_client = EcommerceClient(runtime.context.access_token)

    # 2. 构建查询参数
    normalized_order_id = normalize_resource_id(order_id) if order_id is not None else None
    query_params = {"order_id": normalized_order_id} if normalized_order_id is not None else None

    # 3. 执行执行工具调用，并且返回工具执行后结果
    return await tool_executor.execute_tool(
        trace_id=runtime.context.trace_id,
        tool_call_id=runtime.tool_call_id,
        tool_name="list_after_sales",
        tool_arguments=query_params or {},
        operation=lambda: ecommerce_client.get_json("/after-sales", query_params=query_params)
    )


@tool
async def load_skill(
        runtime: ToolRuntime[AgentRuntimeContext, AgentRuntimeState],
        skill_code: Annotated[str, "用户当前问题最相关的客服领域技能码"],
) -> Command:
    """加载客服领域技能并更新当前 Agent 的能力范围"""

    # 1. 根据技能码获取技能对象的指导
    skill_definition = SKILL_CATALOG.get_definition(skill_code)
    skill_guidance = "\n".join(f"- {guidance}" for guidance in skill_definition.guidance)

    # 2. 更新获取到的技能码（skill_code更新到AgentRuntimeState）
    return Command(
        update={
            "active_skill_code": skill_code,
            "messages": [
                ToolMessage(
                    content=f"已经成功加载技能{skill_code}，请遵循以下规则:{skill_guidance}",
                    tool_call_id=runtime.tool_call_id
                )
            ]
        }
    )
