@echo off
REM GitHub爬虫工具启动脚本 - Windows版本

REM 获取脚本所在目录
cd /d "%~dp0"

REM 检查虚拟环境是否存在
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 安装依赖
echo 安装依赖...
pip install -r requirements.txt

REM 启动后端API服务器
echo 启动后端API服务器...
start "API服务器" cmd /c "python api_server.py"

REM 切换到前端目录
cd frontend

REM 检查前端依赖是否已安装
if not exist "node_modules" (
    echo 安装前端依赖...
    call npm install
)

REM 启动前端开发服务器
echo 启动前端开发服务器...
start "前端开发服务器" cmd /c "npm start"

REM 输出访问地址
echo ===================
echo 后端API服务器地址: http://localhost:5000
echo 前端开发服务器地址: http://localhost:3000
echo ===================
echo 关闭命令窗口以停止所有服务

REM 保持窗口打开
pause 