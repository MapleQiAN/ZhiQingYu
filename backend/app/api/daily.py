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
from app.schemas.daily import DailySummaryItem, DailyListResponse, DailyDetailResponse
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
    获取单日详情
    """
    try:
        # 解析日期
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        # 查询摘要
        summary = db.query(DailySummary).filter(DailySummary.date == target_date).first()
        
        if not summary:
            # 如果没有摘要，返回空数据
            return ApiResponse(
                data=DailyDetailResponse(
                    date=target_date,
                    summary_text=None,
                    main_emotion=None,
                    avg_intensity=None,
                    main_topics=None,
                    messages=[]
                ),
                error=None
            )
        
        # 查询当天的代表性消息（最多5条）
        messages = db.query(Message).filter(
            func.date(Message.created_at) == target_date
        ).order_by(Message.created_at.asc()).limit(5).all()
        
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
        
        return ApiResponse(
            data=DailyDetailResponse(
                date=summary.date,
                summary_text=summary.summary_text,
                main_emotion=summary.main_emotion,
                avg_intensity=summary.avg_intensity,
                main_topics=summary.main_topics,
                messages=message_items
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
