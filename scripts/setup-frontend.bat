@echo off
REM 前端构建脚本（Windows）

echo 开始设置前端环境...

REM 检查Node.js
node --version
if errorlevel 1 (
    echo 错误: 未找到Node.js，请先安装Node.js 18+
    exit /b 1
)

REM 检查pnpm
pnpm --version
if errorlevel 1 (
    echo 安装pnpm...
    call npm install -g pnpm
)

REM 安装依赖
echo 安装前端依赖...
cd /d "%~dp0\..\web"
call pnpm install

REM 构建生产版本（可选）
if "%1"=="build" (
    echo 构建生产版本...
    call pnpm run build
    echo 构建完成！
) else (
    echo 前端环境设置完成！
    echo 开发模式启动命令: pnpm run dev
)

pause

