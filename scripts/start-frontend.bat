@echo off
REM 前端启动脚本（Windows）

cd /d "%~dp0\..\web"

REM 启动开发服务器
echo 启动前端开发服务器...
call pnpm run dev

pause

