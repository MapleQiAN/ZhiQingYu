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
from app.core.style_override_detector import StyleOverrideDetector
from app.core.safety_checker import SafetyChecker
import logging


class ChatService:
    """聊天服务"""
    
    def __init__(self, db: Session, llm_provider: LLMProvider):
        self.db = db
        self.llm_provider = llm_provider
    
    def process_chat(self, session_id: str | None, messages: list[ChatMessage]) -> dict:
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
        user_profile = UserProfile(
            id=session_id,  # 临时使用session_id作为user_id
            preferredStyleId=None,  # TODO: 从数据库读取
            recentStyleOverrideId=detected_style  # 使用检测到的风格覆盖
        )
        
        # 5. 使用对话算法生成回复
        try:
            llm_result = generate_reply_with_algorithm(
                self.llm_provider,
                messages,
                user_profile
            )
            logger = logging.getLogger(__name__)
            logger.info("=" * 80)
            logger.info("[Chat Service] AI回复生成完成")
            logger.info(f"  用户消息: {user_message.content if user_message else 'N/A'}")
            logger.info(f"  回复长度: {len(llm_result.reply)} 字符")
            logger.info(f"  完整回复内容:\n{llm_result.reply}")
            logger.info(f"  情绪: {llm_result.emotion}, 强度: {llm_result.intensity}")
            logger.info(f"  主题: {llm_result.topics}, 风险等级: {llm_result.risk_level}")
            logger.info("=" * 80)
        except Exception as e:
            # 如果新算法失败，回退到旧方法
            logger = logging.getLogger(__name__)
            logger.warning(f"对话算法失败，回退到旧方法: {str(e)}", exc_info=True)
            llm_result = self.llm_provider.generate_reply(messages)
            logger.info("=" * 80)
            logger.info("[Chat Service] AI回复生成完成（使用旧方法）")
            logger.info(f"  用户消息: {user_message.content if user_message else 'N/A'}")
            logger.info(f"  回复长度: {len(llm_result.reply)} 字符")
            logger.info(f"  完整回复内容:\n{llm_result.reply}")
            logger.info("=" * 80)
        
        # 6. 应用风险检测规则（二次检查）
        if user_message:
            final_risk_level = upgrade_risk_level_if_needed(
                llm_result.risk_level,
                user_message.content,
                llm_result.intensity
            )
            llm_result.risk_level = final_risk_level
        
        # 6.5. 质量自检（在保存前检查回复质量）
        if user_message:
            try:
                # 重新解析用户消息以获取ParsedState
                parsed = parse_user_message(user_message)
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
        
        # 7. 保存助手回复
        assistant_message = Message(
            session_id=session_id,
            role="assistant",
            content=llm_result.reply,
            emotion=llm_result.emotion,
            intensity=llm_result.intensity,
            topics=llm_result.topics
        )
        self.db.add(assistant_message)
        
        # 8. 更新或创建DailySummary
        self._update_daily_summary(
            date.today(),
            llm_result.emotion,
            llm_result.intensity,
            llm_result.topics
        )
        
        self.db.commit()
        
        return {
            "session_id": session_id,
            "reply": llm_result.reply,
            "emotion": llm_result.emotion,
            "intensity": llm_result.intensity,
            "topics": llm_result.topics,
            "risk_level": llm_result.risk_level
        }
    
    def _update_daily_summary(self, target_date: date, emotion: str, intensity: int, topics: list[str]):
        """更新或创建每日摘要"""
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
            # 计算新的平均强度（简单平均）
            today_messages = self.db.query(Message).filter(
                func.date(Message.created_at) == target_date,
                Message.intensity.isnot(None)
            ).all()
            
            if today_messages:
                intensities = [msg.intensity for msg in today_messages if msg.intensity]
                if intensities:
                    summary.avg_intensity = sum(intensities) / len(intensities)
            
            # 更新主要情绪（使用出现频率最高的）
            emotion_counts = {}
            today_emotions = self.db.query(Message).filter(
                func.date(Message.created_at) == target_date,
                Message.emotion.isnot(None)
            ).all()
            
            for msg in today_emotions:
                if msg.emotion:
                    emotion_counts[msg.emotion] = emotion_counts.get(msg.emotion, 0) + 1
            
            if emotion_counts:
                summary.main_emotion = max(emotion_counts, key=emotion_counts.get)
            
            # 合并主题
            all_topics = set(summary.main_topics or [])
            all_topics.update(topics)
            summary.main_topics = list(all_topics)
            
            summary.updated_at = datetime.now()

