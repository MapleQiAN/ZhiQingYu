"""
风格系统相关的Pydantic模型
"""
from pydantic import BaseModel
from typing import Literal


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
    """情绪解析结果"""
    emotions: list[str]  # ['anxiety', 'guilt']
    intensity: int  # 1-10
    scene: str  # 'exam' | 'relationship' | ...
    riskLevel: Literal["low", "medium", "high"]
    userGoal: str  # 'want_relief' | 'want_plan' | ...


class UserProfile(BaseModel):
    """用户配置"""
    id: str
    preferredStyleId: str | None = None
    recentStyleOverrideId: str | None = None


class ReplyPlan(BaseModel):
    """回复规划"""
    style: StyleProfile
    interventions: list[str]  # 干预模块的 id 列表
    structure: dict  # 包含 useThreePart 和 parts


class InterventionConfig(BaseModel):
    """干预模块配置"""
    id: str
    triggers: dict  # 触发条件
    role: Literal["emotion", "clarification", "action"]  # 更偏向用于哪一段


