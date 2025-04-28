#!/bin/bash
# GitHub爬虫工具Docker启动脚本

# 设置脚本执行权限
chmod +x start-docker.sh

# 确保github-scraper/data目录存在
mkdir -p github-scraper/data

# 创建环境变量文件
cat > github-scraper/.env << EOL
# API服务器配置
FLASK_APP=api_server.py
FLASK_ENV=production

# 飞书API配置(可选)
# FEISHU_APP_ID=cli_xxxxx
# FEISHU_APP_SECRET=xxxxxxxxxxxx
# FEISHU_GITHUB_SPREADSHEET_TOKEN=shtcnxxxxxxxxxx
# FEISHU_GITHUB_SHEET_ID=0
# FEISHU_WEBSITE_SPREADSHEET_TOKEN=shtcnxxxxxxxxxx
# FEISHU_WEBSITE_SHEET_ID=0

# GitHub API配置(可选)
# GITHUB_TOKEN=ghp_xxxxxxxxxxxx
EOL

echo "环境变量文件已创建或更新"
echo "如需配置飞书和GitHub API，请编辑github-scraper/.env文件"

echo "启动Docker服务..."
docker-compose up -d

echo "==================="
echo "服务已启动:"
echo "后端API服务器地址: http://localhost:5000"
echo "前端服务器地址: http://localhost:3000"
echo "==================="
echo "使用以下命令查看日志:"
echo "docker-compose logs -f"
echo "==================="
echo "使用以下命令停止服务:"
echo "docker-compose down" 