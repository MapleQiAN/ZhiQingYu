"""
聊天API路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas.chat import (
    ChatRequest, ChatResponse, ChatMessage, SessionItem, SessionListResponse, SessionMessagesResponse
)
from app.schemas.common import ApiResponse, ErrorDetail
from app.core.provider_factory import get_llm_provider
from app.services.chat_service import ChatService
from app.models import Session as SessionModel, Message

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
        # 获取LLM Provider（传递db以从数据库读取配置）
        llm_provider = get_llm_provider(db=db)
        
        # 创建服务实例
        chat_service = ChatService(db, llm_provider)
        
        # 处理聊天请求
        result = chat_service.process_chat(
            request.session_id, 
            request.messages,
            experience_mode=request.experience_mode
        )
        
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


@router.get("/sessions", response_model=ApiResponse[SessionListResponse])
async def get_sessions(
    db: Session = Depends(get_db)
):
    """
    获取会话列表
    
    返回所有会话，按最新消息时间排序
    """
    try:
        # 查询所有会话，按最新消息时间降序排序
        sessions = db.query(SessionModel).order_by(
            SessionModel.latest_message_at.desc().nulls_last(),
            SessionModel.created_at.desc()
        ).all()
        
        session_items = []
        for session in sessions:
            # 获取第一条用户消息作为预览
            first_message = db.query(Message).filter(
                Message.session_id == session.id,
                Message.role == "user"
            ).order_by(Message.created_at.asc()).first()
            
            preview = None
            if first_message:
                # 取前50个字符作为预览
                preview = first_message.content[:50] + "..." if len(first_message.content) > 50 else first_message.content
            
            session_items.append(SessionItem(
                id=session.id,
                title=session.title,
                created_at=session.created_at,
                latest_message_at=session.latest_message_at,
                preview=preview
            ))
        
        return ApiResponse(
            data=SessionListResponse(sessions=session_items),
            error=None
        )
    
    except Exception as e:
        error_detail = ErrorDetail(
            code="SESSIONS_ERROR",
            message=f"获取会话列表时发生错误: {str(e)}"
        )
        return ApiResponse(data=None, error=error_detail)


@router.get("/sessions/{session_id}/messages", response_model=ApiResponse[SessionMessagesResponse])
async def get_session_messages(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    获取指定会话的所有消息
    """
    try:
        # 验证会话是否存在
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            error_detail = ErrorDetail(
                code="SESSION_NOT_FOUND",
                message=f"会话不存在: {session_id}"
            )
            return ApiResponse(data=None, error=error_detail)
        
        # 查询该会话的所有消息，按创建时间升序排序
        messages = db.query(Message).filter(
            Message.session_id == session_id
        ).order_by(Message.created_at.asc()).all()
        
        # 转换为ChatMessage格式
        chat_messages = [
            ChatMessage(
                role=msg.role, 
                content=msg.content,
                card_data=msg.card_data if hasattr(msg, 'card_data') else None
            )
            for msg in messages
        ]
        
        return ApiResponse(
            data=SessionMessagesResponse(
                session_id=session_id,
                messages=chat_messages
            ),
            error=None
        )
    
    except Exception as e:
        error_detail = ErrorDetail(
            code="SESSION_MESSAGES_ERROR",
            message=f"获取会话消息时发生错误: {str(e)}"
        )
        return ApiResponse(data=None, error=error_detail)


@router.delete("/sessions/{session_id}", response_model=ApiResponse[dict])
async def delete_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    删除指定会话及其所有消息
    """
    try:
        # 验证会话是否存在
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            error_detail = ErrorDetail(
                code="SESSION_NOT_FOUND",
                message=f"会话不存在: {session_id}"
            )
            return ApiResponse(data=None, error=error_detail)
        
        # 删除该会话的所有消息
        db.query(Message).filter(Message.session_id == session_id).delete()
        
        # 删除会话
        db.delete(session)
        db.commit()
        
        return ApiResponse(
            data={"success": True, "message": "会话已删除"},
            error=None
        )
    
    except Exception as e:
        db.rollback()
        error_detail = ErrorDetail(
            code="DELETE_SESSION_ERROR",
            message=f"删除会话时发生错误: {str(e)}"
        )
        return ApiResponse(data=None, error=error_detail)