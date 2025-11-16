"""
每日摘要模型
"""
from sqlalchemy import Column, Integer, String, Date, Float, DateTime, JSON, Text
from sqlalchemy.sql import func
from app.db import Base


class DailySummary(Base):
    __tablename__ = "daily_summaries"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, index=True, nullable=False)
    summary_text = Column(Text, nullable=True)  # 一句话总结
    main_emotion = Column(String, nullable=True)  # 主要情绪标签
    avg_intensity = Column(Float, nullable=True)  # 平均强度
    main_topics = Column(JSON, nullable=True)  # 主题列表
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

