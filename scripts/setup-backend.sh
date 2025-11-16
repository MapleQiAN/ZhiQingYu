#!/bin/bash

# 后端环境初始化脚本（Linux/Mac）

set -e

echo "开始设置后端环境..."

# 检查Python版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python版本: $python_version"

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 升级pip
echo "升级pip..."
pip install --upgrade pip

# 安装依赖
echo "安装Python依赖..."
pip install -r requirements.txt

# 初始化数据库（通过运行应用自动创建）
echo "数据库将在首次运行时自动创建"

echo "后端环境设置完成！"
echo "启动命令: source venv/bin/activate && python -m app.main"

