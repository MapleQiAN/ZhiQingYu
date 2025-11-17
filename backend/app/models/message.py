"""
消息模型
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text
from sqlalchemy.sql import func
from app.db import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    emotion = Column(String, nullable=True)  # 主情绪标签
    intensity = Column(Integer, nullable=True)  # 情绪强度 1-5
    topics = Column(JSON, nullable=True)  # 主题列表
    card_data = Column(JSON, nullable=True)  # 卡片数据（主题、情感回音、认知澄清、建议）
    created_at = Column(DateTime(timezone=True), server_default=func.now())

