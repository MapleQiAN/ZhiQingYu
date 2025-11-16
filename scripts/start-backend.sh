#!/bin/bash

# 后端启动脚本（Linux/Mac）

cd "$(dirname "$0")/../backend"

# 激活虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "警告: 虚拟环境不存在，请先运行 setup-backend.sh"
fi

# 启动服务
echo "启动后端服务..."
python -m app.main

