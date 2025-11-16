"""
AI配置API路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db import get_db
from app.models.ai_config import AIConfig
from app.schemas.ai_config import (
    AIConfigCreate,
    AIConfigUpdate,
    AIConfigResponse,
    AIConfigListResponse
)
from app.schemas.common import ApiResponse, ErrorDetail
import json

router = APIRouter()


@router.get("/ai-config", response_model=ApiResponse[AIConfigListResponse])
async def get_ai_configs(db: Session = Depends(get_db)):
    """获取所有AI配置"""
    try:
        configs = db.query(AIConfig).all()
        
        # 找到激活的配置
        active_config = db.query(AIConfig).filter(AIConfig.is_active == True).first()
        active_provider = active_config.provider if active_config else None
        
        # 转换为响应模型
        config_responses = []
        for config in configs:
            extra_config = None
            if config.extra_config:
                try:
                    extra_config = json.loads(config.extra_config)
                except:
                    extra_config = {}
            
            config_responses.append(AIConfigResponse(
                id=config.id,
                provider=config.provider,
                is_active=config.is_active,
                api_key=config.api_key,  # 注意：实际生产环境应该隐藏或加密
                base_url=config.base_url,
                model=config.model,
                extra_config=extra_config,
                created_at=config.created_at,
                updated_at=config.updated_at
            ))
        
        response = AIConfigListResponse(
            configs=config_responses,
            active_provider=active_provider
        )
        
        return ApiResponse(data=response, error=None)
    
    except Exception as e:
        error_detail = ErrorDetail(
            code="GET_CONFIG_ERROR",
            message=f"获取AI配置时发生错误: {str(e)}"
        )
        return ApiResponse(data=None, error=error_detail)


@router.post("/ai-config", response_model=ApiResponse[AIConfigResponse])
async def create_ai_config(
    config: AIConfigCreate,
    db: Session = Depends(get_db)
):
    """创建AI配置"""
    try:
        # 检查是否已存在
        existing = db.query(AIConfig).filter(AIConfig.provider == config.provider).first()
        if existing:
            error_detail = ErrorDetail(
                code="CONFIG_EXISTS",
                message=f"配置 {config.provider} 已存在，请使用更新接口"
            )
            return ApiResponse(data=None, error=error_detail)
        
        # 创建新配置
        extra_config_str = None
        if config.extra_config:
            extra_config_str = json.dumps(config.extra_config)
        
        db_config = AIConfig(
            id=config.provider,
            provider=config.provider,
            api_key=config.api_key,
            base_url=config.base_url,
            model=config.model,
            extra_config=extra_config_str,
            is_active=False
        )
        
        db.add(db_config)
        db.commit()
        db.refresh(db_config)
        
        extra_config = None
        if db_config.extra_config:
            try:
                extra_config = json.loads(db_config.extra_config)
            except:
                extra_config = {}
        
        response = AIConfigResponse(
            id=db_config.id,
            provider=db_config.provider,
            is_active=db_config.is_active,
            api_key=db_config.api_key,
            base_url=db_config.base_url,
            model=db_config.model,
            extra_config=extra_config,
            created_at=db_config.created_at,
            updated_at=db_config.updated_at
        )
        
        return ApiResponse(data=response, error=None)
    
    except Exception as e:
        db.rollback()
        error_detail = ErrorDetail(
            code="CREATE_CONFIG_ERROR",
            message=f"创建AI配置时发生错误: {str(e)}"
        )
        return ApiResponse(data=None, error=error_detail)


@router.put("/ai-config/{provider}", response_model=ApiResponse[AIConfigResponse])
async def update_ai_config(
    provider: str,
    config: AIConfigUpdate,
    db: Session = Depends(get_db)
):
    """更新AI配置"""
    try:
        db_config = db.query(AIConfig).filter(AIConfig.provider == provider).first()
        if not db_config:
            error_detail = ErrorDetail(
                code="CONFIG_NOT_FOUND",
                message=f"配置 {provider} 不存在"
            )
            return ApiResponse(data=None, error=error_detail)
        
        # 更新字段
        if config.api_key is not None:
            db_config.api_key = config.api_key
        if config.base_url is not None:
            db_config.base_url = config.base_url
        if config.model is not None:
            db_config.model = config.model
        if config.extra_config is not None:
            db_config.extra_config = json.dumps(config.extra_config)
        if config.is_active is not None:
            # 如果设置为激活，需要先取消其他配置的激活状态
            if config.is_active:
                db.query(AIConfig).filter(AIConfig.is_active == True).update({"is_active": False})
            db_config.is_active = config.is_active
        
        db.commit()
        db.refresh(db_config)
        
        extra_config = None
        if db_config.extra_config:
            try:
                extra_config = json.loads(db_config.extra_config)
            except:
                extra_config = {}
        
        response = AIConfigResponse(
            id=db_config.id,
            provider=db_config.provider,
            is_active=db_config.is_active,
            api_key=db_config.api_key,
            base_url=db_config.base_url,
            model=db_config.model,
            extra_config=extra_config,
            created_at=db_config.created_at,
            updated_at=db_config.updated_at
        )
        
        return ApiResponse(data=response, error=None)
    
    except Exception as e:
        db.rollback()
        error_detail = ErrorDetail(
            code="UPDATE_CONFIG_ERROR",
            message=f"更新AI配置时发生错误: {str(e)}"
        )
        return ApiResponse(data=None, error=error_detail)


@router.post("/ai-config/{provider}/activate", response_model=ApiResponse[AIConfigResponse])
async def activate_ai_config(
    provider: str,
    db: Session = Depends(get_db)
):
    """激活指定的AI配置"""
    try:
        db_config = db.query(AIConfig).filter(AIConfig.provider == provider).first()
        if not db_config:
            error_detail = ErrorDetail(
                code="CONFIG_NOT_FOUND",
                message=f"配置 {provider} 不存在"
            )
            return ApiResponse(data=None, error=error_detail)
        
        # 取消所有配置的激活状态
        db.query(AIConfig).filter(AIConfig.is_active == True).update({"is_active": False})
        
        # 激活指定配置
        db_config.is_active = True
        db.commit()
        db.refresh(db_config)
        
        extra_config = None
        if db_config.extra_config:
            try:
                extra_config = json.loads(db_config.extra_config)
            except:
                extra_config = {}
        
        response = AIConfigResponse(
            id=db_config.id,
            provider=db_config.provider,
            is_active=db_config.is_active,
            api_key=db_config.api_key,
            base_url=db_config.base_url,
            model=db_config.model,
            extra_config=extra_config,
            created_at=db_config.created_at,
            updated_at=db_config.updated_at
        )
        
        return ApiResponse(data=response, error=None)
    
    except Exception as e:
        db.rollback()
        error_detail = ErrorDetail(
            code="ACTIVATE_CONFIG_ERROR",
            message=f"激活AI配置时发生错误: {str(e)}"
        )
        return ApiResponse(data=None, error=error_detail)

