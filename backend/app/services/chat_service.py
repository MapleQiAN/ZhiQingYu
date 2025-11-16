"""
聊天服务层
"""
import uuid
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Message, Session as SessionModel, DailySummary
from app.schemas.chat import ChatMessage
from app.core.llm_provider import LLMProvider
from app.core.risk_detection import upgrade_risk_level_if_needed


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
        
        # 3. 调用LLM Provider
        llm_result = self.llm_provider.generate_reply(messages)
        
        # 4. 应用风险检测规则（二次检查）
        if user_message:
            final_risk_level = upgrade_risk_level_if_needed(
                llm_result.risk_level,
                user_message.content,
                llm_result.intensity
            )
            llm_result.risk_level = final_risk_level
        
        # 5. 保存助手回复
        assistant_message = Message(
            session_id=session_id,
            role="assistant",
            content=llm_result.reply,
            emotion=llm_result.emotion,
            intensity=llm_result.intensity,
            topics=llm_result.topics
        )
        self.db.add(assistant_message)
        
        # 6. 更新或创建DailySummary
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

