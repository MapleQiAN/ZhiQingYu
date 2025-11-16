"""
AI配置相关的Schema
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class AIConfigBase(BaseModel):
    """AI配置基础模型"""
    provider: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    extra_config: Optional[Dict[str, Any]] = None


class AIConfigCreate(AIConfigBase):
    """创建AI配置"""
    pass


class AIConfigUpdate(BaseModel):
    """更新AI配置"""
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    extra_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class AIConfigResponse(AIConfigBase):
    """AI配置响应模型"""
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AIConfigListResponse(BaseModel):
    """AI配置列表响应"""
    configs: list[AIConfigResponse]
    active_provider: Optional[str] = None

