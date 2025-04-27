#!/bin/bash
# GitHub爬虫工具启动脚本

# 获取脚本所在目录
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate || source venv/Scripts/activate

# 安装依赖
echo "安装依赖..."
pip install -r requirements.txt

# 启动后端API服务器
echo "启动后端API服务器..."
python api_server.py &
API_PID=$!

# 切换到前端目录
cd frontend

# 检查前端依赖是否已安装
if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi

# 启动前端开发服务器
echo "启动前端开发服务器..."
npm start &
FE_PID=$!

# 捕获中断信号，关闭所有进程
trap 'echo "关闭服务器..."; kill $API_PID; kill $FE_PID; exit' INT

# 输出访问地址
echo "==================="
echo "后端API服务器地址: http://localhost:5000"
echo "前端开发服务器地址: http://localhost:3000"
echo "==================="
echo "按 Ctrl+C 停止所有服务"

# 等待用户中断
wait 