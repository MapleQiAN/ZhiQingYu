@echo off
REM 后端启动脚本（Windows）

cd /d "%~dp0\..\backend"

REM 激活虚拟环境
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo 警告: 虚拟环境不存在，请先运行 setup-backend.bat
)

REM 启动服务
echo 启动后端服务...
python -m app.main

pause

