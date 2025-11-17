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


def parse_user_message(message: ChatMessage, history: list[ChatMessage] = None) -> ParsedState:
    """
    解析用户消息，提取情绪、强度、场景等信息
    
    增强版本：
    - 支持更多情绪类型（13种）
    - 更细粒度的强度估算（1-10）
    - 考虑对话历史上下文
    - 更准确的场景和风险识别
    """
    content = message.content.lower()
    history = history or []
    
    # 扩展的情绪关键词映射（支持13种情绪）
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
        "neutral": []  # 默认情绪
    }
    
    # 检测情绪（支持多情绪）
    detected_emotions = []
    emotion_scores = {}  # 记录每个情绪的匹配强度
    
    for emotion, keywords in emotion_keywords.items():
        if emotion == "neutral":
            continue
        matches = sum(1 for kw in keywords if kw in content)
        if matches > 0:
            detected_emotions.append(emotion)
            emotion_scores[emotion] = matches
    
    # 如果没有检测到情绪，使用neutral
    if not detected_emotions:
        detected_emotions = ["neutral"]
    
    # 限制最多3个主要情绪
    if len(detected_emotions) > 3:
        detected_emotions = sorted(detected_emotions, key=lambda e: emotion_scores.get(e, 0), reverse=True)[:3]
    
    # 更细粒度的强度估算（1-10）
    intensity = 5  # 默认中等强度
    
    # 强度增强词（按强度分级）
    extreme_intensity_words = ["极度", "超级", "非常非常", "extremely", "extremely", "崩溃", "绝望"]
    high_intensity_words = ["非常", "特别", "很", "very", "really", "much"]
    medium_intensity_words = ["比较", "有点", "somewhat", "quite"]
    low_intensity_words = ["稍微", "一点点", "a bit", "slightly", "little"]
    
    if any(word in content for word in extreme_intensity_words):
        intensity = 9
    elif any(word in content for word in high_intensity_words):
        intensity = 7
    elif any(word in content for word in medium_intensity_words):
        intensity = 4
    elif any(word in content for word in low_intensity_words):
        intensity = 2
    
    # 根据情绪数量调整强度（多情绪叠加可能增加强度）
    if len(detected_emotions) > 1:
        intensity = min(10, intensity + 1)
    
    # 根据历史情绪调整强度（如果历史中有相似情绪，可能表示持续困扰）
    if history:
        recent_emotions = []
        for msg in history[-3:]:  # 只看最近3条消息
            if hasattr(msg, 'emotion') and msg.emotion:
                recent_emotions.append(msg.emotion)
        
        # 如果最近有相似情绪，可能表示持续困扰，适当提高强度
        if any(emotion in recent_emotions for emotion in detected_emotions):
            intensity = min(10, intensity + 1)
    
    # 扩展的场景识别
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
    
    detected_scene = "general"
    scene_scores = {}
    for scene, keywords in scene_keywords.items():
        matches = sum(1 for kw in keywords if kw in content)
        if matches > 0:
            scene_scores[scene] = matches
    
    if scene_scores:
        detected_scene = max(scene_scores, key=scene_scores.get)
    
    # 增强的风险等级检测
    high_risk_keywords = ["自杀", "自残", "不想活", "结束生命", "suicide", "kill myself", "self-harm", "不想活了"]
    medium_risk_keywords = ["绝望", "没有希望", "hopeless", "desperate", "撑不下去"]
    
    risk_level = "low"
    if any(kw in content for kw in high_risk_keywords):
        risk_level = "high"
        intensity = max(intensity, 9)  # 高风险时至少强度9
    elif any(kw in content for kw in medium_risk_keywords):
        risk_level = "medium"
        intensity = max(intensity, 7)
    elif intensity >= 8:
        risk_level = "medium"
    
    # 增强的用户目标识别
    user_goal = "want_relief"  # 默认想要缓解
    
    plan_keywords = ["怎么办", "建议", "如何", "how", "suggestion", "方法", "计划", "plan"]
    analysis_keywords = ["理解", "为什么", "why", "understand", "分析", "analyze", "原因"]
    listen_keywords = ["倾听", "听我说", "想聊聊", "想说话"]
    
    if any(kw in content for kw in plan_keywords):
        user_goal = "want_plan"
    elif any(kw in content for kw in analysis_keywords):
        user_goal = "want_clarification"
    elif any(kw in content for kw in listen_keywords):
        user_goal = "want_listen"
    
    return ParsedState(
        emotions=detected_emotions,
        intensity=intensity,
        scene=detected_scene,
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
    # 1. 解析用户消息（传入历史消息以考虑上下文）
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
    
    # 传入历史消息以考虑上下文
    parsed = parse_user_message(user_message, history=messages[:-1] if len(messages) > 1 else [])
    
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

