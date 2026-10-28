import re

from atguigu.agent.harness.validator.validator import ValidateOutputError
from atguigu.app.models.models import AgentToolCall
from atguigu.common.utils import normalize_resource_id

STATUS_CODE_MAP = {
    "已支付": "paid",
    "待发货": "pending_shipment",
    "已发货": "shipped",
    "已完成": "completed",
    "已取消": "cancelled",
    "已退款": "refunded",
    "运输中": "in_transit",
    "已签收": "delivered",
    "待处理": "pending",
    "已通过": "approved",
    "处理中": "processing",
    "已拒绝": "rejected"
}

RESOURCE_ID_RE = re.compile(
    r"\b(?:ORDER|PRODUCT|AS)[_-][A-Z0-9_-]+\b",
    re.IGNORECASE,
)

NUMBER_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:元|块|件|台|套|笔|单)")


def validate_answer(text: str,
                    complete_tool_calls: list[AgentToolCall]):
    """
    职责：校验答案
    参与比较对象
    对象1：llm输出的文本
    对象2：工具执行的记录（参数值、返回值的内容）

    比较的内容：
    ①资源ID(订单编号、商品编号、售后单编号)
    ②数值（价格、库存、量词）
    ③状态（订单状态、物流状态、售后单状态）
    :param text:
    :param complete_tool_calls:
    :return:
    """
    unsupported = []
    # 1. 获取工具调用的证据(工具调用参数、工具调用的结果)
    evidence_numbers, evidence_texts = _collect_evidence(complete_tool_calls)

    # 2. 利用正则+in获取text中的资源ID
    for raw_id in set(RESOURCE_ID_RE.findall(text)):
        normalized_resource_id = normalize_resource_id(raw_id)
        if normalized_resource_id not in evidence_texts:
            unsupported.append(normalized_resource_id)

    # 3. 利用正则+in获取text中的数值
    for raw_number in set(NUMBER_RE.findall(text)):
        if float(raw_number) not in evidence_numbers:
            unsupported.append(float(raw_number))

    # 4. 利用映射表+in获取text中的状态
    for label, code in STATUS_CODE_MAP.items():
        if (label in text or code in text) and code not in evidence_texts:
            unsupported.append(code)
    if unsupported:
        values = "、".join(unsupported)
        raise ValidateOutputError(
            f"回复中的业务事实缺少工具支持：{values}，请仅根据工具返回结果回答"
        )


def _collect_evidence(complete_tool_calls: list[AgentToolCall]) -> tuple[set[float], set[str]]:
    """
    收集证据
    收集参数
    收集返回值
    :param complete_tool_calls:

    :return:
    """
    texts = set()
    numbers = set()

    def collect(value: object):
        """
        value类型：
        参数类型：dict[str,str、int、float]
        返回结果：
        search_products:1.list[dict[str,"str"、"int"、"float"、dict["str","str"、"int"、"float"]]]
        get_product:dict[str,"str"、"int"、"float"、dict["str","str"、"int"、"float"]]
        list_orders:list[dict["str", "str"、list[dict["str","float"]]]]
        get_order:dict["str", "str"、list[dict["str","float"]]]
        get_logistics:dict["str","str"、list[dict]]
        list_after_sales:list[dict["str":"str"]]
        :param value:
        :return:
        """
        if isinstance(value, dict):
            for v in value.values():
                collect(v)
        elif isinstance(value, list):
            for item in value:
                collect(item)
        elif isinstance(value, str):
            texts.add(value)
        elif isinstance(value, int | float):
            numbers.add(float(value))

    for tool_call in complete_tool_calls:
        collect(tool_call.arguments)  # dict对象
        collect(tool_call.result['data'])

    return numbers, texts
