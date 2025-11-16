"""
统计相关的Pydantic模型
"""
from pydantic import BaseModel
from typing import Dict


class EmotionStatsOverview(BaseModel):
    """情绪统计概览"""
    trend: list[Dict[str, any]]  # [{"date": "2025-01-10", "score": -2}, ...]
    emotion_distribution: Dict[str, float]  # {"sadness": 0.3, "joy": 0.2, ...}
    top_topics: list[Dict[str, any]]  # [{"topic": "study", "count": 8}, ...]

