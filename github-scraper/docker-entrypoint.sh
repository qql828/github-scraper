#!/bin/bash
# Docker容器的入口脚本

# 创建必要的目录
mkdir -p /app/data

# 加载环境变量
if [ -f .env ]; then
  echo "加载.env文件..."
  export $(grep -v '^#' .env | xargs)
fi

# 启动API服务器
echo "启动API服务器..."
exec python api_server.py 