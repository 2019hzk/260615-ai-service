from enum import StrEnum
from dataclasses import dataclass
from typing import Any


class ActionCode(StrEnum):
    """定义服务端允许生成的页面动作编码。"""

    BROWSE_ORDERS = "browse_orders"
    OPEN_ORDER_DETAIL = "open_order_detail"
    CANCEL_ORDER = "cancel_order"
    EDIT_ADDRESS = "edit_address"
    APPLY_AFTER_SALE = "apply_after_sale"
    VIEW_AFTER_SALES = "view_after_sales"


@dataclass(slots=True, frozen=True)
class ActionDefinition:
    action_code: ActionCode
    label: str
    description: str
    path_template: str
    resource_type: str | None = None

    def build(self, resource_id: str | None = None) -> dict[str, Any]:
        """
        职责：负责根据行动码构建引导用户操作的链接
        :param action_code:
        :return:
        """
        return {
            "label": self.label,
            "description": self.description,
            "href": self.path_template.format(resource_id=resource_id)
        }


class ActionCatalog:
    """集中管理行动相关的链接"""

    def __init__(self, definitions: list[ActionDefinition]):
        self.definitions = {definition.action_code: definition for definition in definitions}

    def get_definition(self, action_code: ActionCode) -> ActionDefinition:
        return self.definitions[action_code]

    def render_index(self) -> str:
        """
        职责：返回所有的行动码以及行动描述给LLM
        :return:
        """
        return "\n".join(
            f"- {definition.action_code}: {definition.description}" for definition in self.definitions.values())


ACTION_CATALOG = ActionCatalog(
    [
        ActionDefinition(
            action_code=ActionCode.BROWSE_ORDERS,
            label="查看我的订单",
            description="进入我的订单列表",
            path_template="/me",
        ),
        ActionDefinition(
            action_code=ActionCode.OPEN_ORDER_DETAIL,
            label="查看订单详情",
            description="进入订单详情查看状态与可用操作",
            path_template="/me/orders/{resource_id}",
            resource_type="order",
        ),
        ActionDefinition(
            action_code=ActionCode.CANCEL_ORDER,
            label="前往取消订单",
            description="进入订单页面核对状态并确认取消",
            path_template="/me/orders/{resource_id}/cancel",
            resource_type="order",
        ),
        ActionDefinition(
            action_code=ActionCode.EDIT_ADDRESS,
            label="前往修改地址",
            description="进入订单页面修改收货地址",
            path_template="/me/orders/{resource_id}/address",
            resource_type="order",
        ),
        ActionDefinition(
            action_code=ActionCode.APPLY_AFTER_SALE,
            label="申请售后",
            description="进入订单页面填写售后申请",
            path_template="/me/orders/{resource_id}/after-sale",
            resource_type="order",
        ),
        ActionDefinition(
            action_code=ActionCode.VIEW_AFTER_SALES,
            label="查看售后进度",
            description="进入订单页面查看售后记录",
            path_template="/me/orders/{resource_id}?section=after-sales",
            resource_type="order",
        ),
    ]
)
