"""
日记相关的Pydantic模型
"""
from pydantic import BaseModel
from typing import Optional
from datetime import date
from app.schemas.message import MessageItem


class DailySummaryItem(BaseModel):
    """每日摘要项"""
    date: date
    summary_text: Optional[str] = None
    main_emotion: Optional[str] = None
    avg_intensity: Optional[float] = None


class DailyListResponse(BaseModel):
    """日记列表响应"""
    items: list[DailySummaryItem]


class TopicGroup(BaseModel):
    """主题分组"""
    topic: str
    messages: list[MessageItem] = []
    emotion_summary: Optional[str] = None  # 该主题下的主要情绪
    message_count: int = 0


class DailyDetailResponse(BaseModel):
    """单日详情响应"""
    date: date
    summary_text: Optional[str] = None
    main_emotion: Optional[str] = None
    avg_intensity: Optional[float] = None
    main_topics: Optional[list[str]] = None
    messages: list[MessageItem] = []  # 保留原有字段以兼容
    topic_groups: list[TopicGroup] = []  # 新增：按主题分组
