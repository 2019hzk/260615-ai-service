from atguigu.app.models.models import AgentToolCall


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

    # 1. 获取工具调用的证据(工具调用参数、工具调用的结果)

    evidence_numbers, evidence_texts = _collect_evidence(complete_tool_calls)


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
