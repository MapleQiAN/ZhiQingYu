"""
日记相关的Pydantic模型
"""
from pydantic import BaseModel
from typing import Optional, TYPE_CHECKING
from datetime import date

if TYPE_CHECKING:
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


class DailyDetailResponse(BaseModel):
    """单日详情响应"""
    date: date
    summary_text: Optional[str] = None
    main_emotion: Optional[str] = None
    avg_intensity: Optional[float] = None
    main_topics: Optional[list[str]] = None
    messages: list[MessageItem] = []

