"""
聊天API路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas.chat import (
    ChatRequest, ChatResponse, ChatMessage, SessionItem, SessionListResponse, SessionMessagesResponse
)
from app.schemas.style import ConversationState
import json
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
            experience_mode=request.experience_mode,
            ai_style=request.ai_style,
            chat_mode=request.chat_mode
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
            # 如果已经有AI生成的标题，就不需要预览了
            # 否则获取第一条用户消息作为预览
            preview = None
            if not session.title:
                first_message = db.query(Message).filter(
                    Message.session_id == session.id,
                    Message.role == "user"
                ).order_by(Message.created_at.asc()).first()
                
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


@router.post("/sessions/{session_id}/generate-card", response_model=ApiResponse[ChatResponse])
async def generate_card(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    生成关心卡
    
    基于会话的多轮对话，生成一张关心卡
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
        
        # 获取该会话的所有消息
        messages = db.query(Message).filter(
            Message.session_id == session_id
        ).order_by(Message.created_at.asc()).all()
        
        if not messages:
            error_detail = ErrorDetail(
                code="NO_MESSAGES",
                message="会话中没有消息"
            )
            return ApiResponse(data=None, error=error_detail)
        
        # 转换为ChatMessage格式
        chat_messages = [
            ChatMessage(
                role=msg.role,
                content=msg.content,
                card_data=msg.card_data if hasattr(msg, 'card_data') else None
            )
            for msg in messages
        ]
        
        # 恢复对话状态
        conversation_state = None
        if session and hasattr(session, 'conversation_state') and session.conversation_state:
            try:
                state_dict = json.loads(session.conversation_state) if isinstance(session.conversation_state, str) else session.conversation_state
                conversation_state = ConversationState(**state_dict)
            except Exception:
                conversation_state = None
        
        if not conversation_state:
            conversation_state = ConversationState()
        
        # 获取LLM Provider
        llm_provider = get_llm_provider(db=db)
        
        # 创建服务实例
        chat_service = ChatService(db, llm_provider)
        
        # 使用深聊模式生成完整的关心卡（包含所有5个步骤）
        from app.schemas.style import UserProfile, ParsedState
        from app.core.conversation_algorithm import parse_user_message, select_style, select_interventions
        from app.core.step_controller import StepController
        from app.core.five_step_planner import FiveStepPlanner
        
        # 解析最后一条用户消息，并考虑整个对话历史
        last_user_message = next((m for m in reversed(chat_messages) if m.role == "user"), None)
        if not last_user_message:
            error_detail = ErrorDetail(
                code="NO_USER_MESSAGE",
                message="会话中没有用户消息"
            )
            return ApiResponse(data=None, error=error_detail)
        
        # 解析用户消息，传入完整对话历史以获取更准确的解析
        parsed = parse_user_message(last_user_message, history=[m for m in chat_messages if m != last_user_message])
        
        # 如果对话状态中有结构化信息，使用它来增强解析结果
        if conversation_state and conversation_state.structuredInfo:
            structured_info = conversation_state.structuredInfo
            # 更新解析结果中的情绪信息（如果结构化信息中有更准确的数据）
            if structured_info.get("emotion_primary"):
                if not parsed.emotions or structured_info["emotion_primary"] not in parsed.emotions:
                    parsed.emotions = [structured_info["emotion_primary"]] + parsed.emotions[:2]
            if structured_info.get("emotion_intensity"):
                parsed.intensity = max(parsed.intensity, structured_info["emotion_intensity"])
            if structured_info.get("topic"):
                parsed.scene = structured_info["topic"]
            if structured_info.get("need"):
                parsed.userGoal = structured_info["need"]
        
        # 创建用户配置
        user_profile = UserProfile(
            id=session_id,
            preferredStyleId=None,
            recentStyleOverrideId=None,
            preferredExperienceMode=None
        )
        
        # 选择风格
        style = select_style(user_profile, parsed)
        
        # 使用深聊模式，执行所有5个步骤
        steps_to_execute = [1, 2, 3, 4, 5]
        interventions = select_interventions(parsed, style)
        
        # 规划步骤
        five_step_planner = FiveStepPlanner()
        plan = five_step_planner.plan_steps(
            parsed=parsed,
            style=style,
            interventions=interventions,
            steps_to_execute=steps_to_execute,
            conversation_state=conversation_state.model_dump() if conversation_state else None
        )
        
        # 生成关心卡（使用深聊模式）
        llm_result = llm_provider.generate_deep_chat_reply(
            messages=chat_messages,
            parsed=parsed,
            style=style,
            plan=plan,
            interventions=interventions
        )
        
        # 更新对话状态为card_generated
        conversation_state.conversationStage = "card_generated"
        
        # 保存对话状态
        if session and hasattr(session, 'conversation_state'):
            try:
                session.conversation_state = json.dumps(conversation_state.model_dump(), ensure_ascii=False)
                db.commit()
            except Exception:
                pass
        
        # 保存助手回复（包含卡片数据）
        assistant_message = Message(
            session_id=session_id,
            role="assistant",
            content=llm_result.reply,
            emotion=llm_result.emotion,
            intensity=llm_result.intensity,
            topics=llm_result.topics,
            card_data=llm_result.card_data,
            prompt_tokens=llm_result.prompt_tokens,
            completion_tokens=llm_result.completion_tokens,
            total_tokens=llm_result.total_tokens
        )
        db.add(assistant_message)
        db.commit()
        
        # 映射风险级别
        api_risk_level = "normal" if llm_result.risk_level in ["low", "medium"] else llm_result.risk_level
        
        # 构建响应
        response = ChatResponse(
            session_id=session_id,
            reply=llm_result.reply,
            emotion=llm_result.emotion,
            intensity=llm_result.intensity,
            topics=llm_result.topics,
            risk_level=api_risk_level,
            card_data=llm_result.card_data,
            should_show_card_button=False  # 生成卡片后不再显示按钮
        )
        
        return ApiResponse(data=response, error=None)
    
    except Exception as e:
        error_detail = ErrorDetail(
            code="GENERATE_CARD_ERROR",
            message=f"生成关心卡时发生错误: {str(e)}"
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