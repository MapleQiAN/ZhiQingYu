"""
全局错误处理中间件
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.schemas.common import ApiResponse, ErrorDetail


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求验证错误"""
    errors = exc.errors()
    error_messages = [f"{err['loc']}: {err['msg']}" for err in errors]
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ApiResponse(
            data=None,
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message="; ".join(error_messages)
            )
        ).model_dump()
    )


async def general_exception_handler(request: Request, exc: Exception):
    """处理一般异常"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ApiResponse(
            data=None,
            error=ErrorDetail(
                code="INTERNAL_ERROR",
                message=f"服务器内部错误: {str(exc)}"
            )
        ).model_dump()
    )

