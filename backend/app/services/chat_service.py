"""
聊天服务层
"""
import uuid
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Message, Session as SessionModel, DailySummary
from app.schemas.chat import ChatMessage
from app.schemas.style import UserProfile
from app.core.llm_provider import LLMProvider
from app.core.risk_detection import upgrade_risk_level_if_needed
from app.core.conversation_algorithm import generate_reply_with_algorithm, parse_user_message
from app.schemas.style import ConversationState
import json
from app.core.style_override_detector import StyleOverrideDetector
from app.core.safety_checker import SafetyChecker
import logging


class ChatService:
    """聊天服务"""
    
    def __init__(self, db: Session, llm_provider: LLMProvider):
        self.db = db
        self.llm_provider = llm_provider
    
    def process_chat(self, session_id: str | None, messages: list[ChatMessage], experience_mode: str | None = None) -> dict:
        """
        处理聊天请求
        
        Returns:
            包含session_id和LLM结果的字典
        """
        # 1. 创建或获取Session
        if not session_id:
            session_id = str(uuid.uuid4())
            session = SessionModel(
                id=session_id,
                latest_message_at=datetime.now()
            )
            self.db.add(session)
        else:
            session = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
            if not session:
                # 如果session不存在，创建新的
                session = SessionModel(
                    id=session_id,
                    latest_message_at=datetime.now()
                )
                self.db.add(session)
            else:
                session.latest_message_at = datetime.now()
        
        self.db.commit()
        
        # 2. 保存用户最新消息
        user_message = messages[-1] if messages else None
        if user_message and user_message.role == "user":
            db_message = Message(
                session_id=session_id,
                role="user",
                content=user_message.content
            )
            self.db.add(db_message)
            self.db.commit()
        
        # 3. 检测用户是否请求切换风格
        style_detector = StyleOverrideDetector()
        detected_style = None
        if user_message and user_message.role == "user":
            detected_style = style_detector.detect(user_message.content)
        
        # 4. 获取用户配置（简化版，实际应该从数据库读取）
        # 如果前端提供了experience_mode，优先使用；否则使用用户偏好或对话状态中的
        preferred_experience_mode = experience_mode
        if not preferred_experience_mode and conversation_state:
            preferred_experience_mode = conversation_state.experienceMode
        
        user_profile = UserProfile(
            id=session_id,  # 临时使用session_id作为user_id
            preferredStyleId=None,  # TODO: 从数据库读取
            recentStyleOverrideId=detected_style,  # 使用检测到的风格覆盖
            preferredExperienceMode=preferred_experience_mode  # 使用前端提供的体验模式
        )
        
        # 5. 恢复对话状态（从session或创建新的）
        conversation_state = None
        if session and hasattr(session, 'conversation_state') and session.conversation_state:
            try:
                state_dict = json.loads(session.conversation_state) if isinstance(session.conversation_state, str) else session.conversation_state
                conversation_state = ConversationState(**state_dict)
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.warning(f"恢复对话状态失败: {e}，将创建新状态")
                conversation_state = None
        
        # 6. 使用对话算法生成回复（增强版：支持5步骤系统）
        try:
            llm_result, updated_conversation_state = generate_reply_with_algorithm(
                self.llm_provider,
                messages,
                user_profile,
                conversation_state=conversation_state
            )
            
            # 保存对话状态到session（如果session支持）
            if session and hasattr(session, 'conversation_state'):
                try:
                    session.conversation_state = json.dumps(updated_conversation_state.model_dump(), ensure_ascii=False)
                    self.db.commit()
                except Exception as e:
                    logger = logging.getLogger(__name__)
                    logger.warning(f"保存对话状态失败: {e}")
            
            logger = logging.getLogger(__name__)
            logger.info("=" * 80)
            logger.info("[Chat Service] AI回复生成完成（5步骤系统）")
            logger.info(f"  用户消息: {user_message.content if user_message else 'N/A'}")
            logger.info(f"  回复长度: {len(llm_result.reply)} 字符")
            logger.info(f"  完整回复内容:\n{llm_result.reply}")
            logger.info(f"  情绪: {llm_result.emotion}, 强度: {llm_result.intensity}")
            logger.info(f"  主题: {llm_result.topics}, 风险等级: {llm_result.risk_level}")
            logger.info(f"  对话模式: {updated_conversation_state.currentMode}, 当前步骤: {updated_conversation_state.currentStep}")
            logger.info("=" * 80)
        except Exception as e:
            # 如果新算法失败，回退到旧方法
            logger = logging.getLogger(__name__)
            logger.warning(f"对话算法失败，回退到旧方法: {str(e)}", exc_info=True)
            llm_result = self.llm_provider.generate_reply(messages)
            updated_conversation_state = ConversationState()  # 创建默认状态
            logger.info("=" * 80)
            logger.info("[Chat Service] AI回复生成完成（使用旧方法）")
            logger.info(f"  用户消息: {user_message.content if user_message else 'N/A'}")
            logger.info(f"  回复长度: {len(llm_result.reply)} 字符")
            logger.info(f"  完整回复内容:\n{llm_result.reply}")
            logger.info("=" * 80)
        
        # 7. 应用风险检测规则（二次检查）
        if user_message:
            final_risk_level = upgrade_risk_level_if_needed(
                llm_result.risk_level,
                user_message.content,
                llm_result.intensity
            )
            llm_result.risk_level = final_risk_level
        
        # 7.5. 质量自检（在保存前检查回复质量）
        if user_message:
            try:
                # 重新解析用户消息以获取ParsedState（传入历史消息）
                parsed = parse_user_message(user_message, history=messages[:-1] if len(messages) > 1 else [])
                safety_checker = SafetyChecker()
                check_result = safety_checker.check_reply_quality(
                    user_message=user_message,
                    assistant_reply=llm_result.reply,
                    parsed=parsed
                )
                
                if not check_result.passed:
                    # 质量检查失败，记录日志
                    logger = logging.getLogger(__name__)
                    logger.warning(
                        f"回复质量检查失败: {check_result.reason}. "
                        f"用户消息: {user_message.content[:50]}... "
                        f"助手回复: {llm_result.reply[:50]}..."
                    )
                    # 注意：这里不阻止回复，只是记录日志
                    # 如果需要，可以在这里触发重新生成或使用默认回复
            except Exception as e:
                # 质量检查本身出错，记录但不影响主流程
                logger = logging.getLogger(__name__)
                logger.error(f"质量检查过程出错: {str(e)}", exc_info=True)
        
        # 8. 保存助手回复
        assistant_message = Message(
            session_id=session_id,
            role="assistant",
            content=llm_result.reply,
            emotion=llm_result.emotion,
            intensity=llm_result.intensity,
            topics=llm_result.topics,
            card_data=llm_result.card_data
        )
        self.db.add(assistant_message)
        
        # 9. 更新或创建DailySummary
        self._update_daily_summary(
            date.today(),
            llm_result.emotion,
            llm_result.intensity,
            llm_result.topics
        )
        
        # 10. 根据AI总结的主题生成会话标题
        if llm_result.topics and len(llm_result.topics) > 0:
            # 将主题列表转换为友好的标题
            # 如果只有一个主题，直接使用；如果有多个，用"、"连接，最多显示3个
            topics_for_title = llm_result.topics[:3]  # 最多取前3个主题
            title = "、".join(topics_for_title)
            if len(llm_result.topics) > 3:
                title += "等"
            session.title = title
        elif not session.title:
            # 如果没有主题且还没有标题，使用第一条用户消息的前30个字符作为标题
            if user_message and user_message.role == "user":
                preview = user_message.content[:30]
                if len(user_message.content) > 30:
                    preview += "..."
                session.title = preview
        
        self.db.commit()
        
        # 映射风险级别：为了保持API兼容性，将low/medium/high映射到normal/high
        # low和medium都映射到normal，high保持为high
        api_risk_level = "normal" if llm_result.risk_level in ["low", "medium"] else llm_result.risk_level
        
        return {
            "session_id": session_id,
            "reply": llm_result.reply,
            "emotion": llm_result.emotion,
            "intensity": llm_result.intensity,
            "topics": llm_result.topics,
            "risk_level": api_risk_level,  # 映射后的风险级别（保持API兼容）
            "card_data": llm_result.card_data
        }
    
    def _update_daily_summary(self, target_date: date, emotion: str, intensity: int, topics: list[str]):
        """
        更新或创建每日摘要
        
        优化点：
        - 使用时间加权平均计算强度（最近的消息权重更高）
        - 使用加权频率计算主要情绪（考虑强度权重）
        - 智能合并相似主题
        """
        summary = self.db.query(DailySummary).filter(DailySummary.date == target_date).first()
        
        if not summary:
            # 创建新的摘要
            summary = DailySummary(
                date=target_date,
                main_emotion=emotion,
                avg_intensity=float(intensity),
                main_topics=topics,
                summary_text=None  # v0.1暂不自动生成summary_text
            )
            self.db.add(summary)
        else:
            # 更新现有摘要
            # 获取今天的所有消息（按时间排序）
            today_messages = self.db.query(Message).filter(
                func.date(Message.created_at) == target_date,
                Message.intensity.isnot(None)
            ).order_by(Message.created_at.asc()).all()
            
            if today_messages:
                # 使用时间加权平均计算强度（最近的消息权重更高）
                # 权重 = (消息序号 + 1) / 总消息数，使得后面的消息权重更高
                total_messages = len(today_messages)
                weighted_sum = 0.0
                total_weight = 0.0
                
                for idx, msg in enumerate(today_messages):
                    if msg.intensity:
                        # 权重：后面的消息权重更高（线性递增）
                        weight = (idx + 1) / total_messages
                        weighted_sum += msg.intensity * weight
                        total_weight += weight
                
                if total_weight > 0:
                    summary.avg_intensity = weighted_sum / total_weight
                else:
                    summary.avg_intensity = float(intensity)
            
            # 更新主要情绪（使用加权频率，考虑强度权重）
            # 高强度情绪的出现应该被赋予更高权重
            emotion_scores = {}  # emotion -> weighted_count
            today_emotions = self.db.query(Message).filter(
                func.date(Message.created_at) == target_date,
                Message.emotion.isnot(None)
            ).all()
            
            for msg in today_emotions:
                if msg.emotion:
                    # 强度越高，权重越大（1-10的强度，权重为强度值）
                    weight = msg.intensity if msg.intensity else 5  # 默认权重为5
                    emotion_scores[msg.emotion] = emotion_scores.get(msg.emotion, 0) + weight
            
            if emotion_scores:
                # 选择加权得分最高的情绪
                summary.main_emotion = max(emotion_scores, key=emotion_scores.get)
            elif emotion:
                # 如果没有历史数据，使用当前情绪
                summary.main_emotion = emotion
            
            # 智能合并主题（去重并保留频率信息）
            all_topics = {}
            # 先统计现有主题的频率
            if summary.main_topics:
                for topic in summary.main_topics:
                    all_topics[topic] = all_topics.get(topic, 0) + 1
            
            # 添加新主题
            for topic in topics:
                all_topics[topic] = all_topics.get(topic, 0) + 1
            
            # 按频率排序，保留前10个最常见的主题
            sorted_topics = sorted(all_topics.items(), key=lambda x: x[1], reverse=True)
            summary.main_topics = [topic for topic, count in sorted_topics[:10]]
            
            summary.updated_at = datetime.now()

