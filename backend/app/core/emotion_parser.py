"""
情绪解析模块
"""
import json
from typing import Optional
from app.schemas.chat import ChatMessage
from app.schemas.style import ParsedState
from app.core.llm_provider import LLMProvider


class EmotionParser:
    """情绪解析器"""
    
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider
    
    async def parse(self, user_input: str, history: list[ChatMessage]) -> ParsedState:
        """
        解析用户输入的情绪和场景
        
        Args:
            user_input: 用户输入文本
            history: 对话历史
            
        Returns:
            ParsedState: 解析结果
        """
        # 构建解析 prompt
        prompt = self._build_parser_prompt(user_input, history)
        
        # 调用 LLM 进行解析
        try:
            # 使用 LLM Provider 的底层方法，或者创建一个专门的解析方法
            # 这里简化处理，直接调用 generate_reply 但使用特殊的 prompt
            # 实际实现中可能需要扩展 LLMProvider 接口
            
            # 临时方案：使用简单的规则解析 + LLM 增强
            parsed = self._rule_based_parse(user_input)
            
            # TODO: 后续可以接入专门的 LLM 解析
            # parsed = await self._llm_parse(prompt)
            
            return parsed
        except Exception as e:
            print(f"情绪解析失败: {e}")
            # 返回默认的安全解析结果
            return ParsedState(
                emotions=["neutral"],
                intensity=3,
                scene="general",
                riskLevel="low",
                userGoal="want_relief"
            )
    
    def _build_parser_prompt(self, user_input: str, history: list[ChatMessage]) -> str:
        """构建解析 prompt"""
        history_text = "\n".join([
            f"{msg.role}: {msg.content}" for msg in history[-5:]  # 只取最近5条
        ])
        
        return f"""你是一个情绪分析助手。请分析以下用户输入，输出JSON格式的结果。

用户输入: {user_input}

对话历史:
{history_text}

请分析并输出以下JSON格式：
{{
  "emotions": ["anxiety", "sadness"],  // 可能包含多个情绪，从以下选择：anxiety, sadness, anger, guilt, shame, fear, joy, relief, calm, tired, overwhelmed, confusion, neutral
  "intensity": 7,  // 1-10的整数，表示情绪强度
  "scene": "exam",  // 场景类型：exam, study, work, career, relationship, family, social, health, self-worth, future, general
  "riskLevel": "low",  // 风险等级：low, medium, high
  "userGoal": "want_relief"  // 用户目标：want_relief, want_plan, want_analysis, want_listen, unknown
}}

只输出JSON，不要包含其他文本。"""
    
    def _rule_based_parse(self, user_input: str) -> ParsedState:
        """基于规则的简单解析（作为后备方案）"""
        user_lower = user_input.lower()
        
        # 情绪关键词映射
        emotion_keywords = {
            "anxiety": ["焦虑", "担心", "紧张", "不安", "anxiety", "worried", "nervous"],
            "sadness": ["难过", "伤心", "沮丧", "sad", "sadness", "depressed"],
            "anger": ["生气", "愤怒", "恼火", "angry", "anger", "mad"],
            "guilt": ["内疚", "愧疚", "guilt"],
            "shame": ["羞耻", "丢脸", "shame"],
            "fear": ["害怕", "恐惧", "fear", "scared"],
            "tired": ["累", "疲惫", "tired", "exhausted"],
            "overwhelmed": ["崩溃", "受不了", "overwhelmed"],
            "joy": ["开心", "高兴", "快乐", "joy", "happy"],
        }
        
        # 场景关键词映射
        scene_keywords = {
            "exam": ["考试", "期末", "exam", "test"],
            "study": ["学习", "作业", "study", "homework"],
            "work": ["工作", "加班", "work", "job"],
            "relationship": ["恋爱", "分手", "relationship", "love"],
            "family": ["家庭", "父母", "family", "parent"],
            "social": ["社交", "朋友", "social", "friend"],
        }
        
        # 检测情绪
        detected_emotions = []
        for emotion, keywords in emotion_keywords.items():
            if any(kw in user_lower for kw in keywords):
                detected_emotions.append(emotion)
        
        if not detected_emotions:
            detected_emotions = ["neutral"]
        
        # 检测场景
        detected_scene = "general"
        for scene, keywords in scene_keywords.items():
            if any(kw in user_lower for kw in keywords):
                detected_scene = scene
                break
        
        # 估算强度（简单规则：根据关键词数量和语气词）
        intensity = 3
        if any(word in user_lower for word in ["非常", "特别", "超级", "extremely", "very"]):
            intensity = 7
        elif any(word in user_lower for word in ["有点", "稍微", "a bit", "slightly"]):
            intensity = 2
        elif len(detected_emotions) > 1:
            intensity = 5
        
        # 检测风险等级
        risk_keywords = ["不想活", "结束", "自杀", "自残", "suicide", "kill myself"]
        risk_level = "high" if any(kw in user_lower for kw in risk_keywords) else "low"
        if intensity >= 8:
            risk_level = "medium" if risk_level == "low" else risk_level
        
        # 用户目标（简单推断）
        user_goal = "want_relief"
        if any(word in user_input for word in ["分析", "为什么", "分析", "analyze"]):
            user_goal = "want_analysis"
        elif any(word in user_input for word in ["计划", "怎么办", "plan", "how"]):
            user_goal = "want_plan"
        
        return ParsedState(
            emotions=detected_emotions[:3],  # 最多3个情绪
            intensity=intensity,
            scene=detected_scene,
            riskLevel=risk_level,
            userGoal=user_goal
        )


