"""
统计相关的Pydantic模型
"""
from pydantic import BaseModel
from typing import Dict, Any


class EmotionStatsOverview(BaseModel):
    """情绪统计概览"""
    trend: list[Dict[str, Any]]  # [{"date": "2025-01-10", "score": -2}, ...]
    emotion_distribution: Dict[str, float]  # {"sadness": 0.3, "joy": 0.2, ...}
    top_topics: list[Dict[str, Any]]  # [{"topic": "study", "count": 8}, ...]

