@echo off
REM 后端环境初始化脚本（Windows）

echo 开始设置后端环境...

REM 检查Python
python --version
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.11+
    exit /b 1
)

REM 创建虚拟环境
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
echo 激活虚拟环境...
call venv\Scripts\activate.bat

REM 升级pip
echo 升级pip...
python -m pip install --upgrade pip

REM 安装依赖
echo 安装Python依赖...
pip install -r requirements.txt

REM 初始化数据库
echo 数据库将在首次运行时自动创建

echo 后端环境设置完成！
echo 启动命令: venv\Scripts\activate && python -m app.main

pause

