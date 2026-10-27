from pydantic import BaseModel, Field

from atguigu.agent.harness.rules.action import ActionCode
from atguigu.app.models.enums import ReplyType


class PageAction(BaseModel):
    """定义 Agent 建议用户前往页面完成的操作。"""

    action_code: ActionCode = Field(description="服务端允许的页面动作编码")
    resource_id: str | None = Field(
        default=None,
        description="具体订单页面动作使用的订单编号，必须与订单详情工具成功确认的订单编号一致；订单列表页不提供",
    )


class AgentOutput(BaseModel):
    """定义大语言模型必须返回的结构化结果。"""

    reply_type: ReplyType = Field(description="本轮客服回复的业务类型")
    text: str = Field(description="可以直接展示给用户的完整回复内容")
    handoff_summary: str | None = Field(
        default=None,
        description="仅当 reply_type 为 REQUEST_HANDOFF 时提供面向人工客服的问题摘要",
    )
    page_action: PageAction | None = Field(
        default=None,
        description="仅当用户要求取消订单、修改地址、申请售后或打开订单页面时提供；仅查询业务信息时不提供",
    )

