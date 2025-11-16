"""
聊天API路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.common import ApiResponse, ErrorDetail
from app.core.provider_factory import get_llm_provider
from app.services.chat_service import ChatService

router = APIRouter()


@router.post("/chat", response_model=ApiResponse[ChatResponse])
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    聊天接口
    
    接收用户消息，调用LLM生成回复，保存到数据库并更新每日摘要
    """
    try:
        # 获取LLM Provider
        llm_provider = get_llm_provider()
        
        # 创建服务实例
        chat_service = ChatService(db, llm_provider)
        
        # 处理聊天请求
        result = chat_service.process_chat(request.session_id, request.messages)
        
        # 构建响应
        response = ChatResponse(**result)
        
        return ApiResponse(data=response, error=None)
    
    except Exception as e:
        # 统一错误处理
        error_detail = ErrorDetail(
            code="CHAT_ERROR",
            message=f"处理聊天请求时发生错误: {str(e)}"
        )
        return ApiResponse(data=None, error=error_detail)
