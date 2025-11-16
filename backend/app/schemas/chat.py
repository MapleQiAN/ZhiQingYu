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


class SessionItem(BaseModel):
    """会话项"""
    id: str
    title: Optional[str] = None
    created_at: datetime
    latest_message_at: Optional[datetime] = None
    preview: Optional[str] = None  # 第一条用户消息的预览


class SessionListResponse(BaseModel):
    """会话列表响应"""
    sessions: list[SessionItem]


class SessionMessagesResponse(BaseModel):
    """会话消息响应"""
    session_id: str
    messages: list[ChatMessage]
