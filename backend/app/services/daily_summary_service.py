"""
日记生成服务
使用 LLM 生成每日摘要的 summary_text
"""
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import DailySummary, Message
from app.core.llm_provider import LLMProvider
from app.schemas.chat import ChatMessage
import json
import logging

logger = logging.getLogger(__name__)


class DailySummaryService:
    """日记生成服务"""
    
    def __init__(self, db: Session, llm_provider: LLMProvider):
        self.db = db
        self.llm_provider = llm_provider
    
    def generate_daily_summary(self, target_date: date) -> str | None:
        """
        为指定日期生成日记总结文本
        
        Args:
            target_date: 目标日期
            
        Returns:
            生成的总结文本，如果生成失败则返回 None
        """
        try:
            # 获取当天的所有用户消息
            messages = self.db.query(Message).filter(
                func.date(Message.created_at) == target_date,
                Message.role == "user"
            ).order_by(Message.created_at.asc()).all()
            
            if not messages:
                logger.info(f"[Daily Summary] 日期 {target_date} 没有用户消息，跳过生成")
                return None
            
            # 获取当天的摘要信息
            summary = self.db.query(DailySummary).filter(
                DailySummary.date == target_date
            ).first()
            
            if not summary:
                logger.warning(f"[Daily Summary] 日期 {target_date} 没有摘要记录，跳过生成")
                return None
            
            # 如果用户已经编辑过，不自动重新生成
            if summary.is_edited == 1:
                logger.info(f"[Daily Summary] 日期 {target_date} 的摘要已被用户编辑，跳过自动生成")
                return summary.summary_text
            
            # 构建消息列表用于 LLM
            chat_messages = []
            for msg in messages:
                chat_messages.append(ChatMessage(
                    role=msg.role,
                    content=msg.content
                ))
            
            # 构建提示词
            prompt = self._build_summary_prompt(
                messages=chat_messages,
                main_emotion=summary.main_emotion,
                avg_intensity=summary.avg_intensity,
                main_topics=summary.main_topics
            )
            
            # 调用 LLM 生成总结
            system_message = ChatMessage(role="system", content=prompt)
            llm_messages = [system_message] + chat_messages
            
            # 使用简单的文本生成方法
            result = self._generate_text_summary(llm_messages)
            
            if result:
                # 更新摘要
                summary.summary_text = result
                self.db.commit()
                logger.info(f"[Daily Summary] 成功为日期 {target_date} 生成摘要")
                return result
            else:
                logger.warning(f"[Daily Summary] 为日期 {target_date} 生成摘要失败")
                return None
                
        except Exception as e:
            logger.exception(f"[Daily Summary] 生成摘要时发生错误: {str(e)}")
            self.db.rollback()
            return None
    
    def _build_summary_prompt(
        self,
        messages: list[ChatMessage],
        main_emotion: str | None,
        avg_intensity: float | None,
        main_topics: list[str] | None
    ) -> str:
        """构建生成摘要的提示词"""
        
        emotion_info = f"主要情绪：{main_emotion}" if main_emotion else "主要情绪：未识别"
        intensity_info = f"平均强度：{avg_intensity:.1f}/10" if avg_intensity else "平均强度：未记录"
        topics_info = f"主要主题：{', '.join(main_topics)}" if main_topics else "主要主题：未识别"
        
        prompt = f"""你是一位情绪陪伴助手。请根据用户当天的对话内容，生成一段简洁、温暖、有共情力的一句话日记总结。

要求：
1. 总结应该是一句话，长度控制在50-100字之间
2. 语气要温暖、共情，像朋友在回顾这一天
3. 要捕捉用户当天的情绪变化和主要关注点
4. 不要过于具体地提及对话细节，保持一定的概括性
5. 使用第一人称或第二人称都可以，但要自然

当天信息：
- {emotion_info}
- {intensity_info}
- {topics_info}

请直接输出总结文本，不要包含任何其他说明或格式标记。"""
        
        return prompt
    
    def _generate_text_summary(self, messages: list[ChatMessage]) -> str | None:
        """
        使用 LLM 生成文本总结
        
        这个方法使用 LLM Provider 的简单文本生成能力
        """
        try:
            # 使用 provider 的 generate_text 方法
            if hasattr(self.llm_provider, 'generate_text'):
                result = self.llm_provider.generate_text(messages)
                if result:
                    return result
            else:
                logger.warning("[Daily Summary] LLM Provider 不支持 generate_text 方法")
            
            return None
            
        except Exception as e:
            logger.exception(f"[Daily Summary] 生成文本总结时发生错误: {str(e)}")
            return None

