"""
聊天相关的Pydantic模型
"""
from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime


class ChatMessage(BaseModel):
    """聊天消息"""
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    """聊天请求"""
    session_id: Optional[str] = None
    messages: list[ChatMessage]


class ChatResponse(BaseModel):
    """聊天响应"""
    session_id: str
    reply: str
    emotion: str
    intensity: int
    topics: list[str]
    risk_level: Literal["normal", "high"]

