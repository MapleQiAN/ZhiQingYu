"""
增强版情感解析器
实现混合模式（规则+LLM）、置信度评估、多因素强度计算、情绪趋势分析等功能
"""
import json
import re
from typing import Optional, List, Dict, Tuple
from app.schemas.chat import ChatMessage
from app.schemas.style import ParsedState
from app.core.llm_provider import LLMProvider
from app.core.risk_detection import detect_self_harm_keywords, detect_violence_keywords
# 延迟导入以避免循环导入
# from app.core.conversation_algorithm import parse_user_message as rule_based_parse


# 置信度阈值配置
CONFIDENCE_THRESHOLD_HIGH = 0.8  # 高置信度阈值，直接使用规则结果
CONFIDENCE_THRESHOLD_MEDIUM = 0.5  # 中置信度阈值，需要LLM增强
CONFIDENCE_THRESHOLD_LLM = 0.3  # 低置信度阈值，必须使用LLM

# 情绪类型的基础强度权重（不同情绪类型的默认强度不同）
EMOTION_BASE_INTENSITY = {
    "anxiety": 5,
    "sadness": 6,
    "anger": 7,
    "guilt": 5,
    "shame": 6,
    "fear": 7,
    "tired": 4,
    "overwhelmed": 8,
    "confusion": 4,
    "joy": 5,
    "relief": 3,
    "calm": 2,
    "neutral": 3,
}

# 场景对强度的调整系数（某些场景会放大/缩小情绪强度）
SCENE_INTENSITY_MODIFIERS = {
    "exam": 1.2,  # 考试场景会放大焦虑
    "work": 1.1,
    "relationship": 1.15,
    "family": 1.1,
    "health": 1.3,  # 健康问题会放大恐惧
    "self-worth": 1.2,
    "future": 1.1,
    "general": 1.0,
    "study": 1.0,
    "career": 1.0,
    "social": 1.0,
}


class EmotionTrend:
    """情绪趋势分析结果"""
    def __init__(
        self,
        direction: str,  # 'rising', 'falling', 'fluctuating', 'stable'
        intensity_change: float,  # 强度变化量
        is_persistent: bool,  # 是否为持续困扰
        turning_points: List[int] = None,  # 转折点位置
    ):
        self.direction = direction
        self.intensity_change = intensity_change
        self.is_persistent = is_persistent
        self.turning_points = turning_points or []


class EnhancedEmotionParser:
    """增强版情感解析器"""
    
    def __init__(self, llm_provider: Optional[LLMProvider] = None, enable_llm: bool = True):
        """
        初始化增强版解析器
        
        Args:
            llm_provider: LLM提供者（可选，用于LLM增强）
            enable_llm: 是否启用LLM增强（默认启用）
        """
        self.llm_provider = llm_provider
        self.enable_llm = enable_llm and llm_provider is not None
    
    def parse(
        self,
        message: ChatMessage,
        history: List[ChatMessage] = None,
        use_llm_enhancement: Optional[bool] = None
    ) -> Tuple[ParsedState, float]:
        """
        解析用户消息（混合模式）
        
        Args:
            message: 用户消息
            history: 对话历史
            use_llm_enhancement: 是否强制使用LLM增强（None表示自动判断）
            
        Returns:
            (ParsedState, confidence): 解析结果和置信度
        """
        history = history or []
        
        # 1. 规则匹配（快速）
        # 延迟导入以避免循环导入
        from app.core.conversation_algorithm import parse_user_message as rule_based_parse
        rule_result = rule_based_parse(message, history)
        
        # 2. 计算置信度
        confidence = self._calculate_confidence(rule_result, message, history)
        
        # 3. 判断是否需要LLM增强
        should_use_llm = use_llm_enhancement
        if should_use_llm is None:
            should_use_llm = (
                self.enable_llm and
                (confidence < CONFIDENCE_THRESHOLD_MEDIUM or 
                 self._is_complex_case(message, rule_result))
            )
        
        # 4. LLM增强（如果需要）
        if should_use_llm:
            try:
                llm_result = self._llm_enhanced_parse(message, history, rule_result)
                # 融合结果
                final_result = self._merge_results(rule_result, llm_result, confidence)
                # LLM增强后，置信度提升
                final_confidence = min(1.0, confidence + 0.2)
                return final_result, final_confidence
            except Exception as e:
                # LLM调用失败，回退到规则结果
                print(f"LLM增强解析失败，使用规则结果: {e}")
                return rule_result, confidence
        
        # 5. 应用增强算法（即使不使用LLM，也应用多因素强度计算等）
        enhanced_result = self._apply_enhancements(rule_result, message, history)
        
        return enhanced_result, confidence
    
    def _calculate_confidence(
        self,
        rule_result: ParsedState,
        message: ChatMessage,
        history: List[ChatMessage]
    ) -> float:
        """
        计算规则匹配的置信度
        
        评估维度：
        1. 关键词匹配度（0-0.4）
        2. 表达清晰度（0-0.3）
        3. 上下文一致性（0-0.3）
        """
        content = message.content.lower()
        confidence = 1.0
        
        # 1. 关键词匹配度
        keyword_score = self._calculate_keyword_match_score(content, rule_result)
        confidence *= (0.6 + 0.4 * keyword_score)
        
        # 2. 表达清晰度
        clarity_score = self._assess_expression_clarity(message.content)
        confidence *= (0.7 + 0.3 * clarity_score)
        
        # 3. 上下文一致性
        if history:
            consistency_score = self._check_context_consistency(rule_result, history)
            confidence *= (0.7 + 0.3 * consistency_score)
        
        return min(1.0, max(0.0, confidence))
    
    def _calculate_keyword_match_score(self, content: str, parsed: ParsedState) -> float:
        """计算关键词匹配得分"""
        # 检查情绪关键词匹配
        emotion_keywords = {
            "anxiety": ["焦虑", "担心", "紧张", "不安"],
            "sadness": ["难过", "伤心", "沮丧", "失落"],
            "anger": ["生气", "愤怒", "恼火"],
            "guilt": ["内疚", "愧疚", "自责"],
            "shame": ["羞耻", "丢脸"],
            "fear": ["害怕", "恐惧"],
            "tired": ["累", "疲惫", "疲倦"],
            "overwhelmed": ["崩溃", "受不了", "撑不住"],
            "confusion": ["困惑", "迷茫"],
            "joy": ["开心", "高兴", "快乐"],
            "relief": ["放松", "轻松"],
            "calm": ["平静"],
        }
        
        matched_keywords = 0
        total_keywords = 0
        
        for emotion in parsed.emotions:
            if emotion in emotion_keywords:
                keywords = emotion_keywords[emotion]
                total_keywords += len(keywords)
                matched_keywords += sum(1 for kw in keywords if kw in content)
        
        if total_keywords == 0:
            return 0.5  # 中性情绪，给中等分数
        
        return min(1.0, matched_keywords / max(1, total_keywords / 2))
    
    def _assess_expression_clarity(self, content: str) -> float:
        """评估表达清晰度"""
        score = 0.5  # 基础分数
        
        # 检查是否有明确的情绪词
        emotion_indicators = [
            "焦虑", "担心", "难过", "生气", "开心", "害怕",
            "累", "崩溃", "困惑", "内疚", "羞耻"
        ]
        if any(indicator in content for indicator in emotion_indicators):
            score += 0.3
        
        # 检查是否有强度词
        intensity_indicators = ["非常", "特别", "很", "极度", "超级"]
        if any(indicator in content for indicator in intensity_indicators):
            score += 0.1
        
        # 检查长度（太短可能不够清晰，太长可能冗余）
        if 10 <= len(content) <= 200:
            score += 0.1
        
        # 检查是否有问号（可能表示不确定）
        if "?" in content or "？" in content:
            score -= 0.1
        
        return min(1.0, max(0.0, score))
    
    def _check_context_consistency(
        self,
        parsed: ParsedState,
        history: List[ChatMessage]
    ) -> float:
        """检查与历史上下文的一致性"""
        if not history:
            return 1.0
        
        # 提取历史情绪
        recent_emotions = []
        for msg in history[-3:]:
            if hasattr(msg, 'emotion') and msg.emotion:
                recent_emotions.append(msg.emotion)
            elif hasattr(msg, 'emotions') and msg.emotions:
                recent_emotions.extend(msg.emotions)
        
        if not recent_emotions:
            return 0.8  # 没有历史情绪，给中等一致性
        
        # 检查当前情绪是否与历史一致
        current_emotions = set(parsed.emotions)
        history_emotions = set(recent_emotions)
        
        # 如果有重叠，一致性高
        overlap = len(current_emotions & history_emotions)
        if overlap > 0:
            return 0.9
        else:
            # 没有重叠，可能是情绪变化，给中等分数
            return 0.6
    
    def _is_complex_case(self, message: ChatMessage, rule_result: ParsedState) -> bool:
        """判断是否为复杂情况，需要LLM增强"""
        content = message.content.lower()
        
        # 1. 检测反讽、隐喻等复杂表达
        irony_indicators = ["呵呵", "哈哈", "真好", "太好了", "太棒了"]  # 可能表示反讽
        if any(indicator in content for indicator in irony_indicators) and "开心" not in content:
            return True
        
        # 2. 检测多重否定
        negation_count = content.count("不") + content.count("没") + content.count("非")
        if negation_count >= 3:
            return True
        
        # 3. 检测情绪冲突（规则检测到多个矛盾情绪）
        positive_emotions = {"joy", "relief", "calm"}
        negative_emotions = {"anxiety", "sadness", "anger", "fear", "overwhelmed"}
        detected_positive = any(e in positive_emotions for e in rule_result.emotions)
        detected_negative = any(e in negative_emotions for e in rule_result.emotions)
        if detected_positive and detected_negative:
            return True
        
        # 4. 检测模糊表达
        vague_indicators = ["说不清", "不知道", "可能", "也许", "好像"]
        if any(indicator in content for indicator in vague_indicators):
            return True
        
        return False
    
    def _llm_enhanced_parse(
        self,
        message: ChatMessage,
        history: List[ChatMessage],
        rule_result: ParsedState
    ) -> ParsedState:
        """使用LLM进行增强解析"""
        if not self.llm_provider:
            return rule_result
        
        # 构建历史摘要
        history_summary = ""
        if history:
            recent_history = history[-3:]
            history_summary = "\n".join([
                f"{msg.role}: {msg.content[:100]}" for msg in recent_history
            ])
        
        # 构建prompt
        prompt = f"""你是一个专业的情绪分析助手。请分析用户输入，输出JSON格式的情绪分析结果。

用户输入：{message.content}
对话历史：
{history_summary if history_summary else "无"}

规则匹配结果（仅供参考）：
- 情绪: {rule_result.emotions}
- 强度: {rule_result.intensity}
- 场景: {rule_result.scene}
- 风险等级: {rule_result.riskLevel}
- 用户目标: {rule_result.userGoal}

请基于语义理解，输出更准确的分析结果。注意：
1. 如果用户表达模糊或存在反讽，请仔细分析真实情绪
2. 考虑对话历史上下文
3. 如果规则结果明显错误，请纠正

输出JSON格式：
{{
  "emotions": ["anxiety", "sadness"],  // 最多3个情绪
  "intensity": 7,  // 1-10的整数
  "scene": "exam",  // 场景类型
  "riskLevel": "low",  // low/medium/high
  "userGoal": "want_relief",  // want_relief/want_plan/want_clarification/want_listen
  "problemSummary": "用户的问题摘要"  // 简短摘要
}}

只输出JSON，不要包含其他文本。"""
        
        # 调用LLM
        try:
            chat_messages = [
                {"role": "system", "content": "你是一个专业的情绪分析助手，只输出JSON格式的结果。"},
                {"role": "user", "content": prompt}
            ]
            
            # 使用LLM Provider的文本生成方法
            if hasattr(self.llm_provider, '_perform_text_completion'):
                result_text = self.llm_provider._perform_text_completion(chat_messages)
                if isinstance(result_text, dict):
                    result_text = result_text.get("text", "")
            else:
                # 回退到规则结果
                return rule_result
            
            # 解析JSON
            result_dict = json.loads(result_text)
            
            # 构建ParsedState
            return ParsedState(
                emotions=result_dict.get("emotions", rule_result.emotions)[:3],
                intensity=result_dict.get("intensity", rule_result.intensity),
                scene=result_dict.get("scene", rule_result.scene),
                riskLevel=result_dict.get("riskLevel", rule_result.riskLevel),
                userGoal=result_dict.get("userGoal", rule_result.userGoal),
                hasSelfHarmKeywords=detect_self_harm_keywords(message.content),
                hasViolenceKeywords=detect_violence_keywords(message.content),
                problemSummary=result_dict.get("problemSummary", rule_result.problemSummary)
            )
        except Exception as e:
            print(f"LLM解析失败: {e}")
            return rule_result
    
    def _merge_results(
        self,
        rule_result: ParsedState,
        llm_result: ParsedState,
        confidence: float
    ) -> ParsedState:
        """融合规则结果和LLM结果"""
        if confidence > CONFIDENCE_THRESHOLD_HIGH:
            # 高置信度：以规则结果为主，LLM结果微调
            return self._merge_with_weights(rule_result, llm_result, [0.8, 0.2])
        elif confidence > CONFIDENCE_THRESHOLD_MEDIUM:
            # 中置信度：加权融合
            return self._merge_with_weights(rule_result, llm_result, [0.4, 0.6])
        else:
            # 低置信度：以LLM结果为主
            return llm_result
    
    def _merge_with_weights(
        self,
        result1: ParsedState,
        result2: ParsedState,
        weights: List[float]
    ) -> ParsedState:
        """加权融合两个结果"""
        w1, w2 = weights
        
        # 融合情绪（优先使用LLM结果，但保留规则结果中的情绪）
        merged_emotions = result2.emotions if w2 > w1 else result1.emotions
        if not merged_emotions:
            merged_emotions = result1.emotions or result2.emotions
        
        # 融合强度（加权平均）
        merged_intensity = int(result1.intensity * w1 + result2.intensity * w2)
        merged_intensity = max(1, min(10, merged_intensity))
        
        # 融合场景（优先使用LLM结果）
        merged_scene = result2.scene if w2 > w1 else result1.scene
        
        # 风险等级取较高的
        risk_priority = {"low": 1, "medium": 2, "high": 3}
        risk1_priority = risk_priority.get(result1.riskLevel, 1)
        risk2_priority = risk_priority.get(result2.riskLevel, 1)
        merged_risk = result2.riskLevel if risk2_priority >= risk1_priority else result1.riskLevel
        
        # 用户目标优先使用LLM结果
        merged_goal = result2.userGoal if w2 > w1 else result1.userGoal
        
        return ParsedState(
            emotions=merged_emotions[:3],
            intensity=merged_intensity,
            scene=merged_scene,
            riskLevel=merged_risk,
            userGoal=merged_goal,
            hasSelfHarmKeywords=result1.hasSelfHarmKeywords or result2.hasSelfHarmKeywords,
            hasViolenceKeywords=result1.hasViolenceKeywords or result2.hasViolenceKeywords,
            problemSummary=result2.problemSummary or result1.problemSummary
        )
    
    def _apply_enhancements(
        self,
        rule_result: ParsedState,
        message: ChatMessage,
        history: List[ChatMessage]
    ) -> ParsedState:
        """应用增强算法（多因素强度计算、情绪趋势等）"""
        # 1. 多因素强度计算
        enhanced_intensity = self._calculate_enhanced_intensity(
            rule_result, message, history
        )
        
        # 2. 情绪趋势分析
        trend = self._analyze_emotion_trend(history, rule_result)
        
        # 3. 根据趋势调整强度
        if trend.is_persistent and trend.direction == "rising":
            enhanced_intensity = min(10, enhanced_intensity + 1)
        elif trend.direction == "falling":
            enhanced_intensity = max(1, enhanced_intensity - 1)
        
        # 4. 多场景支持（如果有多个场景，保留主场景，但可以扩展）
        # 这里先保持单场景，后续可以扩展
        
        return ParsedState(
            emotions=rule_result.emotions,
            intensity=enhanced_intensity,
            scene=rule_result.scene,
            riskLevel=rule_result.riskLevel,
            userGoal=rule_result.userGoal,
            hasSelfHarmKeywords=rule_result.hasSelfHarmKeywords,
            hasViolenceKeywords=rule_result.hasViolenceKeywords,
            problemSummary=rule_result.problemSummary
        )
    
    def _calculate_enhanced_intensity(
        self,
        parsed: ParsedState,
        message: ChatMessage,
        history: List[ChatMessage]
    ) -> int:
        """多因素强度计算"""
        content = message.content.lower()
        base_intensity = parsed.intensity
        
        # 1. 情绪类型基础强度
        if parsed.emotions:
            primary_emotion = parsed.emotions[0]
            emotion_base = EMOTION_BASE_INTENSITY.get(primary_emotion, 5)
            # 情绪类型加权：如果基础强度与当前强度差异大，适当调整
            if abs(emotion_base - base_intensity) > 2:
                base_intensity = int((base_intensity + emotion_base) / 2)
        
        # 2. 场景影响
        scene_modifier = SCENE_INTENSITY_MODIFIERS.get(parsed.scene, 1.0)
        base_intensity = int(base_intensity * scene_modifier)
        
        # 3. 表达方式调整
        # 检查感叹号
        exclamation_count = message.content.count("!") + message.content.count("！")
        if exclamation_count >= 2:
            base_intensity = min(10, base_intensity + 1)
        
        # 检查重复字（如"好累好累"）
        repeated_pattern = re.findall(r'(\S)\1{2,}', message.content)
        if repeated_pattern:
            base_intensity = min(10, base_intensity + 1)
        
        # 检查长度（很长的消息可能表示情绪强烈）
        if len(message.content) > 300:
            base_intensity = min(10, base_intensity + 1)
        
        return max(1, min(10, base_intensity))
    
    def _analyze_emotion_trend(
        self,
        history: List[ChatMessage],
        current_parsed: ParsedState
    ) -> EmotionTrend:
        """分析情绪趋势"""
        if not history or len(history) < 2:
            return EmotionTrend(
                direction="stable",
                intensity_change=0,
                is_persistent=False
            )
        
        # 提取历史情绪强度序列
        intensity_sequence = []
        emotion_sequence = []
        
        for msg in history[-5:]:  # 看最近5条
            if hasattr(msg, 'intensity') and msg.intensity:
                intensity_sequence.append(msg.intensity)
            elif hasattr(msg, 'emotion') and msg.emotion:
                # 如果没有强度，根据情绪类型估算
                emotion = msg.emotion
                intensity_sequence.append(EMOTION_BASE_INTENSITY.get(emotion, 5))
            
            if hasattr(msg, 'emotion') and msg.emotion:
                emotion_sequence.append(msg.emotion)
            elif hasattr(msg, 'emotions') and msg.emotions:
                emotion_sequence.extend(msg.emotions)
        
        # 添加当前情绪
        intensity_sequence.append(current_parsed.intensity)
        emotion_sequence.extend(current_parsed.emotions)
        
        if len(intensity_sequence) < 2:
            return EmotionTrend(
                direction="stable",
                intensity_change=0,
                is_persistent=False
            )
        
        # 计算趋势
        recent_intensities = intensity_sequence[-3:]
        if len(recent_intensities) >= 2:
            intensity_change = recent_intensities[-1] - recent_intensities[0]
            
            # 判断趋势方向
            if intensity_change > 1:
                direction = "rising"
            elif intensity_change < -1:
                direction = "falling"
            elif abs(intensity_change) <= 1:
                # 检查波动
                if max(recent_intensities) - min(recent_intensities) > 2:
                    direction = "fluctuating"
                else:
                    direction = "stable"
            else:
                direction = "stable"
        else:
            direction = "stable"
            intensity_change = 0
        
        # 判断是否为持续困扰（相同情绪持续3轮以上）
        is_persistent = False
        if len(emotion_sequence) >= 3:
            recent_emotions = emotion_sequence[-3:]
            if len(set(recent_emotions)) <= 2:  # 情绪类型不超过2种
                is_persistent = True
        
        return EmotionTrend(
            direction=direction,
            intensity_change=intensity_change,
            is_persistent=is_persistent
        )


# 便捷函数：向后兼容的接口
def parse_user_message_enhanced(
    message: ChatMessage,
    history: List[ChatMessage] = None,
    llm_provider: Optional[LLMProvider] = None,
    enable_llm: bool = True
) -> Tuple[ParsedState, float]:
    """
    增强版解析函数（向后兼容）
    
    Returns:
        (ParsedState, confidence): 解析结果和置信度
    """
    parser = EnhancedEmotionParser(llm_provider=llm_provider, enable_llm=enable_llm)
    return parser.parse(message, history)

