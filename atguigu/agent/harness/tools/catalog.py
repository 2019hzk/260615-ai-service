from enum import StrEnum

from langchain_core.tools import BaseTool

from atguigu.agent.harness.tools.definitions import search_products, get_product, list_orders, get_order, get_logistics, \
    list_after_sales, load_skill, search_knowledge


class ToolCategory(StrEnum):
    """
    工具的三种类型
    """
    BUSINESS = "BUSINESS"
    GUIDANCE = "GUIDANCE"
    KNOWLEDGE = "KNOWLEDGE"



class ToolCatalog:
    """
    集中管理工具以及所对应的类别
    """
    def __init__(self, tool_catalogs: list[tuple[BaseTool, ToolCategory]]):
        self.tools = [tool for tool, _ in tool_catalogs]
        self.categories = {tool.name: category for tool, category in tool_catalogs}

    def get_agent_tools(self):
        """
        职责：返回所有给Agent使用的工具对象列表
        :return:
        """
        return self.tools

    def get_category(self, tool_name: str):
        """
        职责： 根据工具名获取工具所在的分类
        :param tool_name:
        :return:
        """
        return self.categories[tool_name]

TOOL_CATALOG = ToolCatalog(
    [
        (search_products, ToolCategory.BUSINESS),
        (get_product, ToolCategory.BUSINESS),
        (list_orders, ToolCategory.BUSINESS),
        (get_order, ToolCategory.BUSINESS),
        (get_logistics, ToolCategory.BUSINESS),
        (list_after_sales, ToolCategory.BUSINESS),
        (load_skill, ToolCategory.GUIDANCE),
        (search_knowledge, ToolCategory.KNOWLEDGE)
    ]
)
