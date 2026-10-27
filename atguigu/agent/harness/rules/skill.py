from enum import StrEnum
from dataclasses import dataclass


class SkillCode(StrEnum):
    """定义 Agent 可以加载的技能编码。"""
    PRODUCT_SERVICE = "product_service"
    ORDER_SERVICE = "order_service"
    LOGISTICS_SERVICE = "logistics_service"
    AFTER_SALES_SERVICE = "after_sales_service"
    POLICY_SERVICE = "policy_service"


@dataclass(slots=True, frozen=True)
class SkillDefinition:
    skill_code: SkillCode
    description: str  # 技能包的作用
    guidance: list[str]  # 如何使用技能包
    tools: list[str]  # 工具名


class SkillCatalog:
    """集中管理skill相关信息"""

    def __init__(self, definitions: list[SkillDefinition]):
        self.definitions = {definition.skill_code: definition for definition in definitions}

    def get_definition(self, skill_code: SkillCode) -> SkillDefinition:
        return self.definitions[skill_code]

    def render_index(self) -> str:
        """
        职责：返回所有的技能码以及技能描述给LLM
        :return:
        """

        return "\n".join(
            f"- {definition.skill_code}: {definition.description}" for definition in self.definitions.values())


SKILL_CATALOG = SkillCatalog(
    [
        SkillDefinition(
            skill_code=SkillCode.PRODUCT_SERVICE,
            description="商品搜索、商品详情、规格、价格和实时库存",
            guidance=[
                "用户未提供商品编号时，先使用 search_products 按关键词搜索商品。",
                "已知商品编号并查询商品详情、价格、规格或实时库存时，使用 get_product。",
            ],
            tools=["search_products", "get_product"],
        ),
        SkillDefinition(
            skill_code=SkillCode.ORDER_SERVICE,
            description="订单列表、订单详情、订单状态、金额及取消订单/修改地址页面跳转",
            guidance=[
                "用户未提供订单编号时，先使用 list_orders 查询订单列表。",
                "已知订单编号并查询状态、金额或商品明细时，使用 get_order。",
                "当用户要求取消订单、修改地址或打开订单页面时，必须先调用 get_order 确认订单，再生成对应的 page_action；仅查询订单信息时不生成 page_action。",
            ],
            tools=["list_orders", "get_order"],
        ),
        SkillDefinition(
            skill_code=SkillCode.LOGISTICS_SERVICE,
            description="具体订单的发货状态、承运公司、运单号和物流轨迹",
            guidance=[
                "用户未提供订单编号时，先使用 list_orders 查询订单列表。",
                "查询具体订单的配送进度、快递公司、运单号和物流轨迹时，使用 get_logistics。",
            ],
            tools=["list_orders", "get_logistics"],
        ),
        SkillDefinition(
            skill_code=SkillCode.POLICY_SERVICE,
            description="七天无理由退货及平台通用售后规则说明",
            guidance=[
                "用户询问平台退换货政策、退款规则或帮助说明时，使用 search_knowledge 查询知识库。",
                "知识库内容仅用于解释平台通用规则，不用于判断用户实际的售后申请进度。",
            ],
            tools=["search_knowledge"],
        ),
        SkillDefinition(
            skill_code=SkillCode.AFTER_SALES_SERVICE,
            description="用户实际售后申请记录、处理进度及申请售后页面跳转",
            guidance=[
                "用户询问自己实际的退款、退货或换货进度时，使用 list_after_sales 查询售后记录。",
                "当用户要求申请售后或查看售后页面时，必须先调用 get_order 确认订单，再生成对应的 page_action。",
            ],
            tools=["get_order", "list_after_sales"],
        ),
    ]
)
