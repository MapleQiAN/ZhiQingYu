#!/bin/bash

# 前端启动脚本（Linux/Mac）

cd "$(dirname "$0")/../web"

# 启动开发服务器
echo "启动前端开发服务器..."
pnpm run dev

