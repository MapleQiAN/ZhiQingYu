"""
ZhiQingYu - AI情绪陪伴应用后端主入口
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from app.db import engine, Base
from app.api import chat, daily, stats, ai_config
from app.middleware.error_handler import validation_exception_handler, general_exception_handler

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ZhiQingYu API",
    description="AI情绪陪伴应用后端API",
    version="0.1.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Next.js默认端口
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册错误处理器
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# 注册路由
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(daily.router, prefix="/api", tags=["daily"])
app.include_router(stats.router, prefix="/api", tags=["stats"])
app.include_router(ai_config.router, prefix="/api", tags=["ai-config"])


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok", "service": "ZhiQingYu"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

