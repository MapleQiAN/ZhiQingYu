#!/bin/bash

# 前端构建脚本（Linux/Mac）

set -e

echo "开始设置前端环境..."

# 检查Node.js版本
node_version=$(node --version)
echo "Node.js版本: $node_version"

# 检查pnpm
if ! command -v pnpm &> /dev/null; then
    echo "安装pnpm..."
    npm install -g pnpm
fi

# 安装依赖
echo "安装前端依赖..."
cd "$(dirname "$0")/../web"
pnpm install

# 构建生产版本（可选）
if [ "$1" == "build" ]; then
    echo "构建生产版本..."
    pnpm run build
    echo "构建完成！"
else
    echo "前端环境设置完成！"
    echo "开发模式启动命令: pnpm run dev"
fi

