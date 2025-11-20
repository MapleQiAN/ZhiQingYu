"""
日记API路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime
from typing import Optional
from app.db import get_db
from app.models import DailySummary, Message
from app.schemas.daily import DailySummaryItem, DailyListResponse, DailyDetailResponse, TopicGroup
from app.schemas.message import MessageItem
from app.schemas.common import ApiResponse, ErrorDetail

router = APIRouter()


@router.get("/daily", response_model=ApiResponse[DailyListResponse])
async def get_daily_list(
    from_date: str = Query(..., alias="from", description="起始日期 (YYYY-MM-DD)"),
    to_date: str = Query(..., alias="to", description="结束日期 (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    获取日期范围内的日记列表
    """
    try:
        # 解析日期
        from_dt = datetime.strptime(from_date, "%Y-%m-%d").date()
        to_dt = datetime.strptime(to_date, "%Y-%m-%d").date()
        
        # 查询范围内的摘要
        summaries = db.query(DailySummary).filter(
            DailySummary.date >= from_dt,
            DailySummary.date <= to_dt
        ).order_by(DailySummary.date.desc()).all()
        
        items = [
            DailySummaryItem(
                date=summary.date,
                summary_text=summary.summary_text,
                main_emotion=summary.main_emotion,
                avg_intensity=summary.avg_intensity
            )
            for summary in summaries
        ]
        
        return ApiResponse(
            data=DailyListResponse(items=items),
            error=None
        )
    
    except ValueError as e:
        error_detail = ErrorDetail(
            code="INVALID_DATE_FORMAT",
            message=f"日期格式错误: {str(e)}"
        )
        return ApiResponse(data=None, error=error_detail)
    except Exception as e:
        error_detail = ErrorDetail(
            code="DAILY_LIST_ERROR",
            message=f"获取日记列表时发生错误: {str(e)}"
        )
        return ApiResponse(data=None, error=error_detail)


@router.get("/daily/{date_str}", response_model=ApiResponse[DailyDetailResponse])
async def get_daily_detail(
    date_str: str,
    db: Session = Depends(get_db)
):
    """
    获取单日详情，按主题聚合消息
    """
    try:
        from collections import defaultdict
        
        # 解析日期
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        # 查询摘要
        summary = db.query(DailySummary).filter(DailySummary.date == target_date).first()
        
        # 查询当天的所有消息
        messages = db.query(Message).filter(
            func.date(Message.created_at) == target_date
        ).order_by(Message.created_at.asc()).all()
        
        message_items = [
            MessageItem(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                emotion=msg.emotion,
                intensity=msg.intensity,
                topics=msg.topics,
                created_at=msg.created_at
            )
            for msg in messages
        ]
        
        # 按主题分组消息
        topic_groups_dict = defaultdict(list)
        topic_emotions = defaultdict(list)  # 记录每个主题下的情绪
        
        for msg_item in message_items:
            # 如果消息有主题，将消息添加到对应主题组
            if msg_item.topics and len(msg_item.topics) > 0:
                for topic in msg_item.topics:
                    topic_groups_dict[topic].append(msg_item)
                    if msg_item.emotion:
                        topic_emotions[topic].append(msg_item.emotion)
            else:
                # 没有主题的消息归到"其他"主题
                topic_groups_dict["其他"].append(msg_item)
                if msg_item.emotion:
                    topic_emotions["其他"].append(msg_item.emotion)
        
        # 构建主题分组列表
        topic_groups = []
        # 优先使用summary中的main_topics顺序
        main_topics = summary.main_topics if summary and summary.main_topics else []
        
        # 先添加main_topics中的主题
        processed_topics = set()
        for topic in main_topics:
            if topic in topic_groups_dict:
                # 计算该主题的主要情绪
                emotions = topic_emotions.get(topic, [])
                emotion_summary = None
                if emotions:
                    # 统计情绪频率
                    emotion_counts = {}
                    for emo in emotions:
                        emotion_counts[emo] = emotion_counts.get(emo, 0) + 1
                    emotion_summary = max(emotion_counts.items(), key=lambda x: x[1])[0] if emotion_counts else None
                
                topic_groups.append(TopicGroup(
                    topic=topic,
                    messages=topic_groups_dict[topic],
                    emotion_summary=emotion_summary,
                    message_count=len(topic_groups_dict[topic])
                ))
                processed_topics.add(topic)
        
        # 添加其他主题（不在main_topics中的）
        for topic, msgs in topic_groups_dict.items():
            if topic not in processed_topics:
                emotions = topic_emotions.get(topic, [])
                emotion_summary = None
                if emotions:
                    emotion_counts = {}
                    for emo in emotions:
                        emotion_counts[emo] = emotion_counts.get(emo, 0) + 1
                    emotion_summary = max(emotion_counts.items(), key=lambda x: x[1])[0] if emotion_counts else None
                
                topic_groups.append(TopicGroup(
                    topic=topic,
                    messages=msgs,
                    emotion_summary=emotion_summary,
                    message_count=len(msgs)
                ))
        
        # 如果没有摘要，返回空数据
        if not summary:
            return ApiResponse(
                data=DailyDetailResponse(
                    date=target_date,
                    summary_text=None,
                    main_emotion=None,
                    avg_intensity=None,
                    main_topics=None,
                    messages=message_items,
                    topic_groups=topic_groups
                ),
                error=None
            )
        
        return ApiResponse(
            data=DailyDetailResponse(
                date=summary.date,
                summary_text=summary.summary_text,
                main_emotion=summary.main_emotion,
                avg_intensity=summary.avg_intensity,
                main_topics=summary.main_topics,
                messages=message_items,  # 保留原有字段以兼容
                topic_groups=topic_groups
            ),
            error=None
        )
    
    except ValueError as e:
        error_detail = ErrorDetail(
            code="INVALID_DATE_FORMAT",
            message=f"日期格式错误: {str(e)}"
        )
        return ApiResponse(data=None, error=error_detail)
    except Exception as e:
        error_detail = ErrorDetail(
            code="DAILY_DETAIL_ERROR",
            message=f"获取单日详情时发生错误: {str(e)}"
        )
        return ApiResponse(data=None, error=error_detail)
