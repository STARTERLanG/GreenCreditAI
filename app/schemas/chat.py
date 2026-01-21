from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class IntentType(str, Enum):
    GENERAL_CHAT = "GENERAL_CHAT"  # 闲聊
    POLICY_QUERY = "POLICY_QUERY"  # 政策查询
    PROJECT_AUDIT = "PROJECT_AUDIT"  # 项目申报/审核 (原文档分析)
    SUPPLEMENTARY_INFO = "SUPPLEMENTARY_INFO"  # 补充材料信息


class ChatRequest(BaseModel):
    message: str = Field(..., description="用户发送的消息")
    session_id: str | None = Field(None, description="会话ID")
    file_hashes: list[str] = Field(default_factory=list, description="挂载的文件哈希列表")


class ChatResponse(BaseModel):
    """
    非流式响应的标准结构 (如需)
    """

    message: str
    intent: IntentType | None = None


class StreamEvent(BaseModel):
    """流式响应事件结构"""

    event: Literal["think", "token", "error", "done"]

    payload: str


class UpdateSessionRequest(BaseModel):
    title: str
