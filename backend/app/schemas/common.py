"""
通用响应模型
"""
from pydantic import BaseModel
from typing import Optional, Any, Generic, TypeVar

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """错误详情"""
    code: str
    message: str


class ApiResponse(BaseModel, Generic[T]):
    """统一API响应格式"""
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None

