"""
统计相关的Pydantic模型
"""
from pydantic import BaseModel
from typing import Dict, Any, Optional


class EmotionStatsOverview(BaseModel):
    """情绪统计概览"""
    trend: list[Dict[str, Any]]  # [{"date": "2025-01-10", "score": -2}, ...]
    emotion_distribution: Dict[str, float]  # {"sadness": 0.3, "joy": 0.2, ...}
    top_topics: list[Dict[str, Any]]  # [{"topic": "study", "count": 8}, ...]


class TokensUsageStats(BaseModel):
    """Tokens使用统计"""
    total_prompt_tokens: int  # 总输入tokens
    total_completion_tokens: int  # 总输出tokens
    total_tokens: int  # 总tokens
    daily_usage: list[Dict[str, Any]]  # [{"date": "2025-01-10", "prompt_tokens": 1000, "completion_tokens": 500, "total_tokens": 1500}, ...]
    message_count: int  # 消息数量

