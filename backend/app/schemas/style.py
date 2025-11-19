"""
风格系统相关的Pydantic模型
"""
from pydantic import BaseModel
from typing import Literal, Optional


class StyleProfile(BaseModel):
    """风格配置"""
    id: str
    name: str
    description: str
    tone: Literal["gentle", "neutral", "firm", "playful"]
    directness: Literal[1, 2, 3, 4, 5]
    analysisDepth: Literal[1, 2, 3, 4, 5]
    emotionFocus: Literal[1, 2, 3, 4, 5]
    actionFocus: Literal[1, 2, 3, 4, 5]
    jokingLevel: Literal[0, 1, 2, 3, 4, 5]
    confrontationLevel: Literal[0, 1, 2, 3, 4, 5]
    useGentleQuestions: bool
    usePsychoEducation: bool
    safetyBias: Literal["high", "medium"]


class ParsedState(BaseModel):
    """情绪解析结果（增强版）"""
    emotions: list[str]  # ['anxiety', 'guilt']
    intensity: int  # 1-10
    scene: str  # 'exam' | 'relationship' | ...
    riskLevel: Literal["low", "medium", "high"]
    userGoal: str  # 'want_listen' | 'want_clarification' | 'want_plan' | 'want_relief' | 'unknown'
    # 新增字段
    hasSelfHarmKeywords: bool = False  # 是否包含自伤关键词
    hasViolenceKeywords: bool = False  # 是否包含暴力关键词
    problemSummary: Optional[str] = None  # 问题摘要（用于Step 1的问题复述）


class UserProfile(BaseModel):
    """用户配置"""
    id: str
    preferredStyleId: str | None = None
    recentStyleOverrideId: str | None = None
    # 新增：体验模式偏好
    preferredExperienceMode: Optional[Literal["A", "B", "C", "D"]] = None  # A:只想被听 B:想搞懂 C:想要建议 D:系统深聊


class ConversationState(BaseModel):
    """对话状态（用于多轮对话控制）"""
    currentMode: Literal["quick", "deep"] = "quick"  # 快速模式 or 深聊模式
    experienceMode: Optional[Literal["A", "B", "C", "D"]] = None  # 当前体验模式
    currentStep: Optional[int] = None  # 当前步骤编号 (1-5)，None表示未开始
    completedSteps: list[int] = []  # 已完成的步骤列表
    stepHistory: list[dict] = []  # 步骤历史记录（用于Step 5的回顾）
    problemContext: Optional[dict] = None  # 问题上下文（用于多轮对话中保持信息）
    # 多阶段对话流程控制
    conversationStage: Literal["chatting", "exploring", "summarizing", "inviting", "card_generated"] = "chatting"  # 对话阶段
    turnCount: int = 0  # 对话轮数
    structuredInfo: Optional[dict] = None  # 结构化信息收集（emotion_primary, topic, trigger, need, resources等）


class ReplyPlan(BaseModel):
    """回复规划（增强版）"""
    style: StyleProfile
    interventions: list[str]  # 干预模块的 id 列表
    structure: dict  # 包含 useThreePart 和 parts
    # 新增：5步骤规划
    stepsToExecute: list[int] = []  # 本轮要执行的步骤编号列表 (1-5)
    stepContents: dict[int, dict] = {}  # 每个步骤的具体内容规划
    # stepContents格式: {1: {"emotion_mirror": "...", "problem_restate": "..."}, ...}


class InterventionConfig(BaseModel):
    """干预模块配置"""
    id: str
    triggers: dict  # 触发条件
    role: Literal["emotion", "clarification", "action"]  # 更偏向用于哪一段


