"""
对话算法核心流程
实现风格系统和三段式回复生成
"""
from app.schemas.chat import ChatMessage
from app.schemas.style import (
    StyleProfile, ParsedState, UserProfile, ReplyPlan, InterventionConfig
)
from app.core.llm_provider import LLMProvider, LLMResult
from app.core.style_resolver import StyleResolver
from app.core.intervention_manager import get_intervention_manager


# 预定义的干预模块（带描述信息，用于构建prompt）
# 这些描述会传递给LLM，帮助理解每个干预模块的用途
INTERVENTION_DESCRIPTIONS = {
    "emotion_naming": "命名和验证情绪：帮助用户识别和命名当前情绪，验证其合理性",
    "catastrophizing_identification": "识别灾难化思维：帮助用户识别灾难化思维模式，即过度放大负面结果",
    "perfectionism_identification": "识别完美主义：帮助用户识别完美主义倾向，理解'足够好'的概念",
    "behavioral_activation": "行为激活：从极小行为开始，帮助用户重新建立行动力",
    "breathing_exercise": "呼吸放松练习：提供简单的呼吸放松技巧，帮助缓解急性焦虑",
    "grounding_exercise": "注意力锚定练习：通过5-4-3-2-1 grounding技巧，帮助用户回到当下",
    "task_breakdown": "任务拆解：将大任务拆解成可执行的小步骤",
    "self_compassion": "自我关怀：帮助用户对自己更温和，减少自我批评",
    "reframing": "认知重构：帮助用户从不同角度看待问题",
    "boundary_setting": "边界设定：帮助用户识别和设定健康的边界",
    # 兼容旧版本
    "emotion_validation": "情绪验证：承认并接纳用户的情绪",
    "cognitive_reframing": "认知重构：帮助用户重新审视问题",
    "action_planning": "行动规划：提供具体可行的步骤",
}


def parse_user_message(message: ChatMessage) -> ParsedState:
    """
    解析用户消息，提取情绪、强度、场景等信息
    
    这是一个简化版本，实际应该调用专门的NLP服务或LLM
    """
    content = message.content.lower()
    
    # 简单的关键词匹配（实际应该用更复杂的NLP）
    emotions = []
    if any(word in content for word in ["焦虑", "担心", "anxiety", "worried"]):
        emotions.append("anxiety")
    if any(word in content for word in ["难过", "伤心", "sad", "sadness"]):
        emotions.append("sadness")
    if any(word in content for word in ["愤怒", "生气", "anger", "angry"]):
        emotions.append("anger")
    if any(word in content for word in ["开心", "高兴", "joy", "happy"]):
        emotions.append("joy")
    if not emotions:
        emotions.append("neutral")
    
    # 估算强度（简化版）
    intensity = 5
    if any(word in content for word in ["非常", "特别", "极度", "very", "extremely"]):
        intensity = 8
    elif any(word in content for word in ["有点", "稍微", "a bit", "slightly"]):
        intensity = 3
    
    # 场景识别（简化版）
    scene = "general"
    if any(word in content for word in ["考试", "学习", "exam", "study"]):
        scene = "exam"
    elif any(word in content for word in ["工作", "职场", "work", "job"]):
        scene = "work"
    elif any(word in content for word in ["关系", "恋爱", "relationship", "love"]):
        scene = "relationship"
    
    # 风险等级（简化版）
    risk_level = "low"
    if any(word in content for word in ["自杀", "自残", "suicide", "self-harm"]):
        risk_level = "high"
    elif intensity >= 8:
        risk_level = "medium"
    
    # 用户目标（简化版）
    user_goal = "want_relief"
    if any(word in content for word in ["怎么办", "建议", "how", "suggestion"]):
        user_goal = "want_plan"
    elif any(word in content for word in ["理解", "为什么", "why", "understand"]):
        user_goal = "want_clarification"
    
    return ParsedState(
        emotions=emotions,
        intensity=intensity,
        scene=scene,
        riskLevel=risk_level,
        userGoal=user_goal
    )


def select_style(user_profile: UserProfile, parsed: ParsedState) -> StyleProfile:
    """
    根据用户配置和当前状态选择风格
    
    优先级（符合文档要求）：
    1. 高风险 → crisis_safe（危机安全型）
    2. 用户本轮请求 → 对应风格
    3. 用户默认偏好 → 用户设置
    4. 无偏好时自适应：
       - 情绪强度高(>=7) → comfort（温柔陪伴型）
       - 学习/规划场景 → growth（成长陪伴型）或 coach（学长直给型）
       - 其他 → mentor（温和导师型）
    """
    resolver = StyleResolver()
    return resolver.resolve(user_profile, parsed)


def select_interventions(parsed: ParsedState, style: StyleProfile) -> list[InterventionConfig]:
    """
    根据解析结果和风格选择干预模块
    
    从干预管理器加载所有可用干预模块，然后根据触发条件筛选
    """
    intervention_manager = get_intervention_manager()
    all_interventions = intervention_manager.get_all_interventions()
    
    # 如果没有从配置文件加载到，使用默认的简化版本
    if not all_interventions:
        all_interventions = [
            InterventionConfig(
                id="emotion_validation",
                triggers={"emotions": ["anxiety", "sadness"], "intensity": [5, 10]},
                role="emotion"
            ),
            InterventionConfig(
                id="cognitive_reframing",
                triggers={"scene": ["exam", "work"], "intensity": [3, 10]},
                role="clarification"
            ),
            InterventionConfig(
                id="action_planning",
                triggers={"userGoal": "want_plan", "intensity": [1, 7]},
                role="action"
            ),
        ]
    
    selected = []
    
    for interv in all_interventions:
        triggers = interv.triggers
        matched = False
        
        # 检查强度范围（支持两种格式：intensity数组 或 intensityMin/intensityMax）
        def check_intensity(triggers_dict):
            if "intensity" in triggers_dict:
                # 格式：[min, max]
                min_int, max_int = triggers_dict["intensity"]
                return min_int <= parsed.intensity <= max_int
            elif "intensityMin" in triggers_dict and "intensityMax" in triggers_dict:
                # 格式：intensityMin 和 intensityMax
                return triggers_dict["intensityMin"] <= parsed.intensity <= triggers_dict["intensityMax"]
            else:
                # 没有强度限制
                return True
        
        # 检查情绪触发
        if "emotions" in triggers:
            if any(emotion in parsed.emotions for emotion in triggers["emotions"]):
                if check_intensity(triggers):
                    selected.append(interv)
                    matched = True
                    continue
        
        # 检查场景触发（支持 scene 或 scenes）
        scene_list = triggers.get("scene", triggers.get("scenes", []))
        if scene_list:
            if isinstance(scene_list, str):
                scene_list = [scene_list]
            if parsed.scene in scene_list:
                if check_intensity(triggers):
                    selected.append(interv)
                    matched = True
                    continue
        
        # 检查用户目标触发
        if "userGoal" in triggers:
            if parsed.userGoal == triggers["userGoal"]:
                if check_intensity(triggers):
                    selected.append(interv)
                    matched = True
                    continue
    
    return selected


def plan_reply(style: StyleProfile, parsed: ParsedState, interventions: list[InterventionConfig]) -> ReplyPlan:
    """
    规划回复结构（符合文档要求）
    
    不同风格的结构调整：
    - listener（极简倾听型）：弱化第三部分，主要提问
    - coach（学长直给型）：强化第三部分，把任务拆得更细
    - crisis_safe（危机安全型）：弱化第二、第三部分，重点放在安全提示和情绪陪伴
    """
    parts = []
    
    # 危机安全型：只保留情绪部分，弱化其他部分
    if style.id == "crisis_safe":
        parts = ["emotion"]
        use_three_part = False
    # 极简倾听型：弱化行动部分
    elif style.id == "listener":
        parts = ["emotion", "clarification"]
        use_three_part = False
    # 学长直给型：强化行动部分
    elif style.id == "coach":
        parts = ["emotion", "clarification", "action"]
        use_three_part = True
    # 其他风格：根据配置和干预模块决定
    else:
        use_three_part = style.actionFocus >= 3 and parsed.riskLevel != "high"
        
        # 情绪部分（大多数风格都有）
        if style.emotionFocus >= 3 or any(i.role == "emotion" for i in interventions):
            parts.append("emotion")
        
        # 澄清部分
        if style.analysisDepth >= 3 or any(i.role == "clarification" for i in interventions):
            parts.append("clarification")
        
        # 行动部分（高风险时不提供）
        if use_three_part and parsed.riskLevel != "high" and (
            style.actionFocus >= 3 or any(i.role == "action" for i in interventions)
        ):
            parts.append("action")
    
    # 如果没有任何部分，至少要有情绪部分
    if not parts:
        parts.append("emotion")
    
    structure = {
        "useThreePart": use_three_part,
        "parts": parts
    }
    
    return ReplyPlan(
        style=style,
        interventions=[i.id for i in interventions],
        structure=structure
    )


def generate_reply_with_algorithm(
    llm_provider: LLMProvider,
    messages: list[ChatMessage],
    user_profile: UserProfile,
) -> LLMResult:
    """
    使用对话算法生成回复
    
    流程：
    1. 解析用户消息 -> ParsedState
    2. 选择风格 -> StyleProfile
    3. 选择干预模块 -> list[InterventionConfig]
    4. 规划回复结构 -> ReplyPlan
    5. 调用LLM生成回复 -> LLMResult
    """
    # 1. 解析用户消息
    user_message = messages[-1] if messages else None
    if not user_message or user_message.role != "user":
        # 如果没有用户消息，返回默认回复
        return LLMResult(
            reply="我在这里倾听你的想法。",
            emotion="neutral",
            intensity=2,
            topics=["general"],
            risk_level="normal"
        )
    
    parsed = parse_user_message(user_message)
    
    # 2. 选择风格
    style = select_style(user_profile, parsed)
    
    # 3. 选择干预模块
    interventions = select_interventions(parsed, style)
    
    # 4. 规划回复结构
    plan = plan_reply(style, parsed, interventions)
    
    # 5. 调用LLM生成回复
    return llm_provider.generate_structured_reply(
        messages=messages,
        parsed=parsed,
        style=style,
        plan=plan,
        interventions=interventions
    )

