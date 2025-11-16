"""
消息相关的Pydantic模型
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MessageItem(BaseModel):
    """消息项"""
    id: int
    role: str
    content: str
    emotion: Optional[str] = None
    intensity: Optional[int] = None
    topics: Optional[list[str]] = None
    created_at: datetime

    class Config:
        from_attributes = True

