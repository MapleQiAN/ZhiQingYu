"""
对话算法核心流程（增强版：支持5步骤系统）
实现风格系统、5步骤对话流程、快速/深聊模式、体验模式
"""
from app.schemas.chat import ChatMessage
from app.schemas.style import (
    StyleProfile, ParsedState, UserProfile, ReplyPlan, InterventionConfig, ConversationState
)
from app.core.llm_provider import LLMProvider, LLMResult
from app.core.style_resolver import StyleResolver
from app.core.intervention_manager import get_intervention_manager
from app.core.step_controller import StepController
from app.core.five_step_planner import FiveStepPlanner
from app.core.risk_detection import detect_self_harm_keywords, detect_violence_keywords


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
    
    # 检测自伤和暴力关键词
    has_self_harm = detect_self_harm_keywords(message.content)
    has_violence = detect_violence_keywords(message.content)
    
    # 生成问题摘要（用于Step 1的问题复述）
    problem_summary = message.content[:100] if len(message.content) > 100 else message.content
    
    return ParsedState(
        emotions=detected_emotions,
        intensity=intensity,
        scene=detected_scene,
        riskLevel=risk_level,
        userGoal=user_goal,
        hasSelfHarmKeywords=has_self_harm,
        hasViolenceKeywords=has_violence,
        problemSummary=problem_summary
    )


def extract_resources_from_conversation(messages: list[ChatMessage]) -> dict:
    """
    从对话历史中提取用户已有资源信息
    
    Returns:
        dict: 包含用户努力过什么、有谁支持过他等信息，如果没有则返回None
    """
    resources = {
        "efforts": [],  # 用户努力过什么
        "supporters": [],  # 有谁支持过他
    }
    
    # 合并所有用户消息内容
    user_messages = [msg.content.lower() for msg in messages if msg.role == "user"]
    if not user_messages:
        return None
    
    full_text = " ".join(user_messages)
    
    # 提取用户努力过的内容
    import re
    effort_patterns = [
        r"我(?:试过|做过|努力|尝试|用过|试了|努力过)(.{0,50})",
        r"曾经(?:试过|做过|努力|尝试|用过)(.{0,50})",
        r"之前(?:试过|做过|努力|尝试|用过)(.{0,50})",
    ]
    
    for pattern in effort_patterns:
        matches = re.findall(pattern, full_text)
        for match in matches:
            effort = match.strip()
            if effort and len(effort) > 2 and effort not in resources["efforts"]:
                resources["efforts"].append(effort[:100])  # 限制长度
    
    # 提取支持者信息
    supporter_patterns = [
        r"(?:朋友|家人|父母|老师|同学|同事)(.{0,30})",
        r"有(?:朋友|家人|父母|老师|同学|同事)(.{0,30})",
        r"(?:朋友|家人|父母|老师|同学|同事)(?:支持|帮助|陪伴)(.{0,30})",
    ]
    
    for pattern in supporter_patterns:
        matches = re.findall(pattern, full_text)
        for match in matches:
            supporter = match.strip()
            if supporter and len(supporter) > 1 and supporter not in resources["supporters"]:
                resources["supporters"].append(supporter[:100])  # 限制长度
    
    # 如果没有提取到具体内容，但有关键词，也记录
    effort_keywords = ["试过", "做过", "努力", "尝试", "用过", "试了", "努力过"]
    supporter_keywords = ["朋友", "家人", "父母", "老师", "同学", "同事"]
    
    if not resources["efforts"] and any(kw in full_text for kw in effort_keywords):
        resources["efforts"] = ["用户提到尝试过一些方法"]
    if not resources["supporters"] and any(kw in full_text for kw in supporter_keywords):
        resources["supporters"] = ["用户提到有支持者"]
    
    # 如果没有任何资源信息，返回None
    if not resources["efforts"] and not resources["supporters"]:
        return None
    
    return resources


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


def determine_conversation_stage(
    conversation_state: ConversationState | None,
    turn_count: int,
    parsed: ParsedState,
    messages: list[ChatMessage]
) -> tuple[str, bool]:
    """
    确定当前对话阶段和是否应该显示"开始关心吧！"按钮
    
    阶段流程：
    1. chatting: 普通陪聊（0-1轮）
    2. exploring: 情绪与事件探索（2-4轮）
    3. summarizing: 小结与校准（1轮）
    4. inviting: 邀请生成关心卡（显示按钮）
    5. card_generated: 已生成卡片
    
    Returns:
        (stage, should_show_button): 当前阶段和是否显示按钮
    """
    if not conversation_state:
        # 新对话，从chatting开始
        if turn_count == 0:
            return "chatting", False
        else:
            return "exploring", False
    
    current_stage = conversation_state.conversationStage
    
    # 如果已经生成卡片，保持card_generated状态
    if current_stage == "card_generated":
        return "card_generated", False
    
    # 如果高风险，不进入邀请阶段
    if parsed.riskLevel == "high":
        return current_stage, False
    
    # 根据轮数和阶段判断
    if current_stage == "chatting":
        if turn_count >= 1:
            return "exploring", False
        return "chatting", False
    
    elif current_stage == "exploring":
        # 探索阶段：2-4轮，收集足够信息后进入小结
        if turn_count >= 4:  # 至少4轮对话后进入小结阶段
            return "summarizing", False
        return "exploring", False
    
    elif current_stage == "summarizing":
        # 小结阶段：用户回复后，根据是否校正进入邀请阶段
        # 如果用户回复表示确认或校正，进入邀请阶段
        # 这里通过检查用户消息来判断（简单实现：如果用户消息较短且包含确认词，认为已校正）
        if turn_count > conversation_state.turnCount:
            # 用户已回复，进入邀请阶段
            return "inviting", True
        return "summarizing", False
    
    elif current_stage == "inviting":
        # 邀请阶段保持，直到用户点击按钮
        return "inviting", True
    
    return current_stage, False


def generate_reply_with_algorithm(
    llm_provider: LLMProvider,
    messages: list[ChatMessage],
    user_profile: UserProfile,
    conversation_state: ConversationState | None = None,
    chat_mode: str | None = None,
) -> tuple[LLMResult, ConversationState]:
    """
    使用对话算法生成回复（增强版：支持5步骤系统和多阶段对话流程）
    
    完整流程（符合文档要求）：
    1. 接收用户输入，更新对话上下文
    2. 判断用户是否发出了风格或模式相关指令，更新对话状态
    3. 执行情绪解析与风险检测，得到结构化信息
    4. 根据风险程度、用户偏好与场景，选择当前风格
    5. 根据当前体验模式与对话进度，确定本轮要执行的步骤集合
    6. 针对选定的步骤，规划本轮回复内容
    7. 在生成之前或之后，进行安全与质量检查
    8. 输出给用户
    9. 更新对话状态（包括多阶段流程状态）
    
    Returns:
        (LLMResult, ConversationState): 回复结果和更新后的对话状态
    """
    # 1. 接收用户输入
    user_message = messages[-1] if messages else None
    if not user_message or user_message.role != "user":
        # 如果没有用户消息，返回默认回复
        default_state = conversation_state or ConversationState()
        return (
            LLMResult(
                reply="我在这里倾听你的想法。",
                emotion="neutral",
                intensity=2,
                topics=["general"],
                risk_level="low"
            ),
            default_state
        )
    
    # 2. 判断用户是否发出了风格或模式相关指令（已在user_profile中处理）
    # 这里可以进一步检测用户输入中的模式切换指令
    
    # 3. 执行情绪解析与风险检测
    parsed = parse_user_message(user_message, history=messages[:-1] if len(messages) > 1 else [])
    
    # 3.5. 更新对话轮数和阶段
    if not conversation_state:
        conversation_state = ConversationState()
    conversation_state.turnCount = len([m for m in messages if m.role == "user"])
    
    # 确定当前阶段和是否显示按钮
    stage, should_show_button = determine_conversation_stage(
        conversation_state,
        conversation_state.turnCount,
        parsed,
        messages
    )
    conversation_state.conversationStage = stage
    
    # 4. 根据风险程度、用户偏好与场景，选择当前风格
    # 高风险时强制使用crisis_safe风格
    style = select_style(user_profile, parsed)
    
    # 5. 根据当前体验模式与对话进度，确定本轮要执行的步骤集合
    step_controller = StepController()
    experience_mode = None
    if getattr(user_profile, "preferredExperienceMode", None):
        experience_mode = user_profile.preferredExperienceMode
    if conversation_state and getattr(conversation_state, "experienceMode", None):
        experience_mode = conversation_state.experienceMode
    # 如果前端明确指定了chat_mode，优先使用；否则通过step_controller自动判断
    if chat_mode:
        mode = chat_mode
        # 深聊模式下，一次性执行所有5个步骤
        if chat_mode == "deep":
            steps_to_execute = [1, 2, 3, 4, 5]
        else:
            # 快速模式：根据体验模式决定步骤
            _, steps_to_execute, experience_mode = step_controller.determine_mode_and_steps(
                parsed=parsed,
                user_profile=user_profile,
                conversation_state=conversation_state,
                user_input=user_message.content
            )
            mode = "quick"
    else:
        mode, steps_to_execute, experience_mode = step_controller.determine_mode_and_steps(
            parsed=parsed,
            user_profile=user_profile,
            conversation_state=conversation_state,
            user_input=user_message.content
        )
    
    # 6. 选择干预模块
    interventions = select_interventions(parsed, style)
    
    # 7. 针对选定的步骤，规划本轮回复内容
    five_step_planner = FiveStepPlanner()
    plan = five_step_planner.plan_steps(
        parsed=parsed,
        style=style,
        interventions=interventions,
        steps_to_execute=steps_to_execute,
        conversation_state=conversation_state.model_dump() if conversation_state else None
    )
    
    # 8. 调用LLM生成回复
    # 深聊模式下，分别调用5次AI请求，每个步骤一次
    if mode == "deep" and len(steps_to_execute) == 5:
        llm_result = llm_provider.generate_deep_chat_reply(
            messages=messages,
            parsed=parsed,
            style=style,
            plan=plan,
            interventions=interventions
        )
    else:
        # 快速模式或非完整5步骤：使用原来的方法
        llm_result = llm_provider.generate_structured_reply(
            messages=messages,
            parsed=parsed,
            style=style,
            plan=plan,
            interventions=interventions,
            conversation_stage=stage
        )
    
    # 8.5. 根据阶段调整回复内容（如果需要）
    if stage == "inviting":
        # 在邀请阶段，在回复末尾添加邀请文案
        if not llm_result.reply.endswith("我可以基于刚刚的聊天帮你做一张今天的关心卡"):
            llm_result.reply += "\n\n我可以基于刚刚的聊天帮你做一张今天的关心卡，里面会有我听见的重点、一点温柔但不虚的分析，以及一些你现在就能尝试的小行动。"
    
    # 设置是否显示按钮
    llm_result.should_show_card_button = should_show_button
    
    # 9. 更新对话状态
    updated_state = step_controller.update_conversation_state(
        conversation_state=conversation_state,
        executed_steps=steps_to_execute,
        mode=mode,
        experience_mode=experience_mode,
        step_content=plan.stepContents
    )
    
    # 更新多阶段流程状态
    updated_state.conversationStage = stage
    updated_state.turnCount = conversation_state.turnCount
    
    # 收集结构化信息（用于后续生成关心卡）
    if not updated_state.structuredInfo:
        updated_state.structuredInfo = {}
    
    # 更新结构化信息
    if parsed.emotions:
        updated_state.structuredInfo["emotion_primary"] = parsed.emotions[0]
    updated_state.structuredInfo["emotion_intensity"] = parsed.intensity
    updated_state.structuredInfo["topic"] = parsed.scene
    updated_state.structuredInfo["trigger"] = user_message.content[:200]  # 触发事件摘要
    updated_state.structuredInfo["need"] = parsed.userGoal
    
    # 提取resources信息（用户已有资源，比如努力过什么、有谁支持过他）
    resources = extract_resources_from_conversation(messages)
    if resources:
        updated_state.structuredInfo["resources"] = resources
    
    # 在summarizing阶段，如果用户回复了校正信息，更新结构化信息
    # 注意：这里stage是当前阶段，如果上一轮是summarizing且用户现在回复了，stage应该是inviting
    # 所以我们需要检查上一轮的状态
    previous_stage = conversation_state.conversationStage if conversation_state else None
    if previous_stage == "summarizing" and stage == "inviting":
        # 上一轮是summarizing，现在进入inviting，说明用户已经回复了
        # 检查用户回复是否包含校正信息
        correction_keywords = ["不对", "不是", "漏了", "还有", "其实", "应该是", "更准确", "更贴切", "纠正", "补充"]
        if any(kw in user_message.content for kw in correction_keywords):
            # 用户提供了校正，重新解析用户消息以更新结构化信息
            corrected_parsed = parse_user_message(user_message, history=messages[:-1])
            if corrected_parsed.emotions:
                updated_state.structuredInfo["emotion_primary"] = corrected_parsed.emotions[0]
            updated_state.structuredInfo["emotion_intensity"] = corrected_parsed.intensity
            if corrected_parsed.scene != "general":
                updated_state.structuredInfo["topic"] = corrected_parsed.scene
            if corrected_parsed.userGoal:
                updated_state.structuredInfo["need"] = corrected_parsed.userGoal
    
    return llm_result, updated_state

