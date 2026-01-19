from pydantic import BaseModel, Field
from typing import Literal, Optional
from enum import Enum

class IntentType(str, Enum):
    GENERAL_CHAT = "GENERAL_CHAT"       # 闲聊
    POLICY_QUERY = "POLICY_QUERY"       # 政策查询
    DOCUMENT_ANALYSIS = "DOCUMENT_ANALYSIS" # 文档分析

class ChatRequest(BaseModel):
    message: str = Field(..., description="用户发送的消息")
    session_id: Optional[str] = Field(None, description="会话ID")

class ChatResponse(BaseModel):
    """
    非流式响应的标准结构 (如需)
    """
    message: str
    intent: Optional[IntentType] = None

class StreamEvent(BaseModel):

    """流式响应事件结构"""

    event: Literal["think", "token", "error", "done"]

    payload: str



class UpdateSessionRequest(BaseModel):

    title: str
