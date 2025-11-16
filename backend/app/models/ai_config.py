"""
AI配置模型
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from app.db import Base


class AIConfig(Base):
    __tablename__ = "ai_configs"

    id = Column(String, primary_key=True, index=True)  # 配置ID，使用provider名称作为主键
    provider = Column(String, nullable=False, unique=True)  # 提供商名称: openai, ollama, deepseek, qwen, etc.
    is_active = Column(Boolean, default=False)  # 是否为当前激活的配置
    api_key = Column(Text, nullable=True)  # API密钥（加密存储）
    base_url = Column(String, nullable=True)  # API基础URL
    model = Column(String, nullable=True)  # 模型名称
    extra_config = Column(Text, nullable=True)  # 额外配置（JSON格式）
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

