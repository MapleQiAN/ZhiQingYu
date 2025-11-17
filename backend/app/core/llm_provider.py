"""
LLM Provider抽象接口和实现
"""
from abc import ABC, abstractmethod
from typing import Literal, Optional
from pydantic import BaseModel
from app.schemas.chat import ChatMessage
from app.schemas.style import StyleProfile, ParsedState, ReplyPlan, InterventionConfig


class LLMResult(BaseModel):
    """LLM返回结果"""
    reply: str
    emotion: str
    intensity: int
    topics: list[str]
    risk_level: Literal["normal", "high"]


class LLMProvider(ABC):
    """LLM Provider抽象接口"""
    
    @abstractmethod
    def generate_reply(self, messages: list[ChatMessage]) -> LLMResult:
        """
        生成回复和情绪分析（旧接口，保持兼容）
        
        Args:
            messages: 对话消息列表
            
        Returns:
            LLMResult: 包含回复、情绪分析等信息
        """
        pass
    
    @abstractmethod
    def generate_structured_reply(
        self,
        messages: list[ChatMessage],
        parsed: ParsedState,
        style: StyleProfile,
        plan: ReplyPlan,
        interventions: list[InterventionConfig],
    ) -> LLMResult:
        """
        生成结构化回复（支持风格系统和三段式结构）
        
        Args:
            messages: 对话消息列表
            parsed: 情绪解析结果
            style: 当前风格
            plan: 回复规划
            interventions: 干预模块列表
            
        Returns:
            LLMResult: 包含回复、情绪分析等信息
        """
        pass


class MockLLMProvider(LLMProvider):
    """Mock实现，用于测试和开发"""
    
    def generate_reply(self, messages: list[ChatMessage]) -> LLMResult:
        """返回固定的测试数据"""
        last_message = messages[-1] if messages else None
        content = last_message.content if last_message else ""
        
        # 简单的关键词匹配来决定情绪
        if any(word in content for word in ["开心", "高兴", "快乐", "joy"]):
            emotion = "joy"
            intensity = 3
            reply = "听到你这么说，我也为你感到高兴。继续保持这种积极的心态吧！"
        elif any(word in content for word in ["难过", "伤心", "sad", "sadness"]):
            emotion = "sadness"
            intensity = 4
            reply = "我理解你现在的感受。每个人都会有低谷期，这很正常。你愿意和我聊聊具体发生了什么吗？"
        elif any(word in content for word in ["焦虑", "担心", "anxiety", "worried"]):
            emotion = "anxiety"
            intensity = 3
            reply = "焦虑是很常见的情绪反应。我们可以一起梳理一下让你感到焦虑的事情，看看能否找到一些缓解的方法。"
        else:
            emotion = "neutral"
            intensity = 2
            reply = "我在这里倾听你的想法。无论你想分享什么，我都会认真对待。"
        
        topics = ["general"]
        risk_level = "normal"
        
        return LLMResult(
            reply=reply,
            emotion=emotion,
            intensity=intensity,
            topics=topics,
            risk_level=risk_level
        )
    
    def generate_structured_reply(
        self,
        messages: list[ChatMessage],
        parsed: ParsedState,
        style: StyleProfile,
        plan: ReplyPlan,
        interventions: list[InterventionConfig],
    ) -> LLMResult:
        """Mock结构化回复生成"""
        # 使用旧的 generate_reply 作为后备
        return self.generate_reply(messages)

