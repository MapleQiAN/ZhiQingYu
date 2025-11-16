"""
会话模型
"""
from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from app.db import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, index=True)  # UUID
    title = Column(String, nullable=True)  # 会话标题（可选）
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    latest_message_at = Column(DateTime(timezone=True), nullable=True)

