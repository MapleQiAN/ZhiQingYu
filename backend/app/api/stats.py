"""
统计API路由
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime, timedelta
from collections import Counter, defaultdict
from app.db import get_db
from app.models import Message, DailySummary
from app.schemas.stats import EmotionStatsOverview, TokensUsageStats
from app.schemas.common import ApiResponse, ErrorDetail

router = APIRouter()


# 情绪得分映射
EMOTION_SCORE_MAP = {
    "joy": 1,
    "relief": 1,
    "calm": 1,
    "neutral": 0,
    "sadness": -1,
    "anxiety": -1,
    "anger": -1,
    "tired": -1,
}


@router.get("/stats/overview", response_model=ApiResponse[EmotionStatsOverview])
async def get_stats_overview(
    days: int = Query(default=7, ge=1, le=365, description="统计天数"),
    db: Session = Depends(get_db)
):
    """
    获取情绪统计概览
    """
    try:
        # 计算日期范围
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)
        
        # 查询范围内的消息
        messages = db.query(Message).filter(
            func.date(Message.created_at) >= start_date,
            func.date(Message.created_at) <= end_date,
            Message.emotion.isnot(None)
        ).all()
        
        # 1. 计算趋势（按日期分组）
        daily_scores = defaultdict(list)
        for msg in messages:
            msg_date = msg.created_at.date()
            emotion = msg.emotion
            score = EMOTION_SCORE_MAP.get(emotion, 0)
            daily_scores[msg_date].append(score)
        
        # 生成趋势数据（包含所有日期，即使没有消息）
        trend = []
        current_date = start_date
        while current_date <= end_date:
            if current_date in daily_scores:
                avg_score = sum(daily_scores[current_date]) / len(daily_scores[current_date])
            else:
                avg_score = 0.0
            
            trend.append({
                "date": current_date.isoformat(),
                "score": round(avg_score, 2)
            })
            current_date += timedelta(days=1)
        
        # 2. 计算情绪分布
        emotion_counts = Counter(msg.emotion for msg in messages if msg.emotion)
        total = len(messages)
        emotion_distribution = {
            emotion: round(count / total, 3) if total > 0 else 0.0
            for emotion, count in emotion_counts.items()
        }
        
        # 3. 计算热门主题
        topic_counts = Counter()
        for msg in messages:
            if msg.topics:
                for topic in msg.topics:
                    topic_counts[topic] += 1
        
        top_topics = [
            {"topic": topic, "count": count}
            for topic, count in topic_counts.most_common(10)
        ]
        
        return ApiResponse(
            data=EmotionStatsOverview(
                trend=trend,
                emotion_distribution=emotion_distribution,
                top_topics=top_topics
            ),
            error=None
        )
    
    except Exception as e:
        error_detail = ErrorDetail(
            code="STATS_ERROR",
            message=f"获取统计信息时发生错误: {str(e)}"
        )
        return ApiResponse(data=None, error=error_detail)


@router.get("/stats/tokens", response_model=ApiResponse[TokensUsageStats])
async def get_tokens_stats(
    days: int = Query(default=30, ge=1, le=365, description="统计天数"),
    db: Session = Depends(get_db)
):
    """
    获取Tokens使用统计
    """
    try:
        # 计算日期范围
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)
        
        # 查询范围内的助手消息（只有助手消息有tokens统计）
        messages = db.query(Message).filter(
            func.date(Message.created_at) >= start_date,
            func.date(Message.created_at) <= end_date,
            Message.role == "assistant",
            Message.total_tokens.isnot(None)
        ).all()
        
        # 计算总计
        total_prompt_tokens = sum(msg.prompt_tokens or 0 for msg in messages)
        total_completion_tokens = sum(msg.completion_tokens or 0 for msg in messages)
        total_tokens = sum(msg.total_tokens or 0 for msg in messages)
        
        # 按日期分组统计
        daily_usage_dict = defaultdict(lambda: {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        })
        
        for msg in messages:
            msg_date = msg.created_at.date()
            daily_usage_dict[msg_date]["prompt_tokens"] += msg.prompt_tokens or 0
            daily_usage_dict[msg_date]["completion_tokens"] += msg.completion_tokens or 0
            daily_usage_dict[msg_date]["total_tokens"] += msg.total_tokens or 0
        
        # 生成每日使用数据（包含所有日期，即使没有消息）
        daily_usage = []
        current_date = start_date
        while current_date <= end_date:
            if current_date in daily_usage_dict:
                daily_usage.append({
                    "date": current_date.isoformat(),
                    "prompt_tokens": daily_usage_dict[current_date]["prompt_tokens"],
                    "completion_tokens": daily_usage_dict[current_date]["completion_tokens"],
                    "total_tokens": daily_usage_dict[current_date]["total_tokens"]
                })
            else:
                daily_usage.append({
                    "date": current_date.isoformat(),
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                })
            current_date += timedelta(days=1)
        
        return ApiResponse(
            data=TokensUsageStats(
                total_prompt_tokens=total_prompt_tokens,
                total_completion_tokens=total_completion_tokens,
                total_tokens=total_tokens,
                daily_usage=daily_usage,
                message_count=len(messages)
            ),
            error=None
        )
    
    except Exception as e:
        error_detail = ErrorDetail(
            code="TOKENS_STATS_ERROR",
            message=f"获取Tokens统计信息时发生错误: {str(e)}"
        )
        return ApiResponse(data=None, error=error_detail)
