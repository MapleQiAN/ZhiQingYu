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
        """基于规则的简单解析（作为后备方案，增强版）"""
        user_lower = user_input.lower()
        
        # 情绪关键词映射（扩展版）
        emotion_keywords = {
            "anxiety": ["焦虑", "担心", "紧张", "不安", "anxiety", "worried", "nervous", "worries"],
            "sadness": ["难过", "伤心", "沮丧", "失落", "sad", "sadness", "depressed", "down"],
            "anger": ["生气", "愤怒", "恼火", "angry", "anger", "mad", "furious"],
            "guilt": ["内疚", "愧疚", "guilt", "guilty", "自责"],
            "shame": ["羞耻", "丢脸", "shame", "ashamed", "embarrassed"],
            "fear": ["害怕", "恐惧", "fear", "scared", "afraid", "terrified"],
            "tired": ["累", "疲惫", "疲倦", "tired", "exhausted", "drained"],
            "overwhelmed": ["崩溃", "受不了", "overwhelmed", "崩溃", "撑不住"],
            "confusion": ["困惑", "迷茫", "confusion", "confused", "lost"],
            "joy": ["开心", "高兴", "快乐", "joy", "happy", "pleased"],
            "relief": ["放松", "relief", "relieved", "轻松"],
            "calm": ["平静", "calm", "peaceful", "serene"],
        }
        
        # 场景关键词映射（扩展版）
        scene_keywords = {
            "exam": ["考试", "期末", "测验", "exam", "test", "quiz"],
            "study": ["学习", "作业", "study", "homework", "课程"],
            "work": ["工作", "加班", "职场", "work", "job", "career", "同事", "老板"],
            "career": ["职业", "career", "职业规划", "工作规划"],
            "relationship": ["恋爱", "分手", "relationship", "love", "感情", "对象"],
            "family": ["家庭", "父母", "家人", "family", "parent", "家人"],
            "social": ["社交", "朋友", "social", "friend", "友谊"],
            "health": ["健康", "身体", "health", "身体", "疾病"],
            "self-worth": ["自我价值", "自卑", "self-worth", "自信", "自我"],
            "future": ["未来", "前途", "future", "将来"],
        }
        
        # 检测情绪（支持多情绪）
        detected_emotions = []
        emotion_scores = {}
        for emotion, keywords in emotion_keywords.items():
            matches = sum(1 for kw in keywords if kw in user_lower)
            if matches > 0:
                detected_emotions.append(emotion)
                emotion_scores[emotion] = matches
        
        if not detected_emotions:
            detected_emotions = ["neutral"]
        
        # 限制最多3个主要情绪
        if len(detected_emotions) > 3:
            detected_emotions = sorted(detected_emotions, key=lambda e: emotion_scores.get(e, 0), reverse=True)[:3]
        
        # 检测场景
        detected_scene = "general"
        scene_scores = {}
        for scene, keywords in scene_keywords.items():
            matches = sum(1 for kw in keywords if kw in user_lower)
            if matches > 0:
                scene_scores[scene] = matches
        
        if scene_scores:
            detected_scene = max(scene_scores, key=scene_scores.get)
        
        # 更细粒度的强度估算（1-10）
        intensity = 5  # 默认中等强度
        
        extreme_intensity_words = ["极度", "超级", "非常非常", "extremely", "崩溃", "绝望"]
        high_intensity_words = ["非常", "特别", "很", "very", "really", "much"]
        medium_intensity_words = ["比较", "有点", "somewhat", "quite"]
        low_intensity_words = ["稍微", "一点点", "a bit", "slightly", "little"]
        
        if any(word in user_lower for word in extreme_intensity_words):
            intensity = 9
        elif any(word in user_lower for word in high_intensity_words):
            intensity = 7
        elif any(word in user_lower for word in medium_intensity_words):
            intensity = 4
        elif any(word in user_lower for word in low_intensity_words):
            intensity = 2
        
        # 根据情绪数量调整强度
        if len(detected_emotions) > 1:
            intensity = min(10, intensity + 1)
        
        # 检测自伤和暴力关键词
        self_harm_keywords = ["自杀", "自残", "不想活", "结束生命", "suicide", "kill myself", "self-harm", "不想活了", "割腕", "跳楼", "上吊"]
        violence_keywords = ["伤害", "报复", "打", "kill", "hurt", "violence", "attack"]
        
        has_self_harm = any(kw in user_lower for kw in self_harm_keywords)
        has_violence = any(kw in user_lower for kw in violence_keywords)
        
        # 检测风险等级（三级：low/medium/high）
        high_risk_keywords = ["自杀", "自残", "不想活", "结束生命", "suicide", "kill myself", "self-harm", "不想活了", "结束自己"]
        medium_risk_keywords = ["绝望", "没有希望", "hopeless", "desperate", "撑不下去", "活不下去"]
        
        risk_level = "low"
        if any(kw in user_lower for kw in high_risk_keywords):
            risk_level = "high"
            intensity = max(intensity, 9)
        elif any(kw in user_lower for kw in medium_risk_keywords):
            risk_level = "medium"
            intensity = max(intensity, 7)
        elif intensity >= 8:
            risk_level = "medium"
        
        # 增强的用户目标识别
        user_goal = "want_relief"  # 默认想要缓解
        
        plan_keywords = ["怎么办", "建议", "如何", "how", "suggestion", "方法", "计划", "plan", "怎么做"]
        analysis_keywords = ["理解", "为什么", "why", "understand", "分析", "analyze", "原因", "怎么回事", "为什么会"]
        listen_keywords = ["倾听", "听我说", "想聊聊", "想说话", "想倾诉", "想聊聊"]
        clarification_keywords = ["搞懂", "弄清楚", "明白", "理解自己", "为什么会这样"]
        
        if any(kw in user_input for kw in listen_keywords):
            user_goal = "want_listen"
        elif any(kw in user_input for kw in clarification_keywords) or any(kw in user_input for kw in analysis_keywords):
            user_goal = "want_clarification"
        elif any(kw in user_input for kw in plan_keywords):
            user_goal = "want_plan"
        
        # 生成问题摘要（简化版，用于Step 1的问题复述）
        problem_summary = user_input[:100] if len(user_input) > 100 else user_input
        
        return ParsedState(
            emotions=detected_emotions[:3],  # 最多3个情绪
            intensity=intensity,
            scene=detected_scene,
            riskLevel=risk_level,
            userGoal=user_goal,
            hasSelfHarmKeywords=has_self_harm,
            hasViolenceKeywords=has_violence,
            problemSummary=problem_summary
        )


