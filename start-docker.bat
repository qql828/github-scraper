@echo off
REM GitHub爬虫工具Docker启动脚本 - Windows版本

REM 确保github-scraper/data目录存在
if not exist "github-scraper\data" (
    mkdir "github-scraper\data"
)

REM 创建环境变量文件
echo # API服务器配置 > github-scraper\.env
echo FLASK_APP=api_server.py >> github-scraper\.env
echo FLASK_ENV=production >> github-scraper\.env
echo. >> github-scraper\.env
echo # 飞书API配置(可选) >> github-scraper\.env
echo # FEISHU_APP_ID=cli_xxxxx >> github-scraper\.env
echo # FEISHU_APP_SECRET=xxxxxxxxxxxx >> github-scraper\.env
echo # FEISHU_GITHUB_SPREADSHEET_TOKEN=shtcnxxxxxxxxxx >> github-scraper\.env
echo # FEISHU_GITHUB_SHEET_ID=0 >> github-scraper\.env
echo # FEISHU_WEBSITE_SPREADSHEET_TOKEN=shtcnxxxxxxxxxx >> github-scraper\.env
echo # FEISHU_WEBSITE_SHEET_ID=0 >> github-scraper\.env
echo. >> github-scraper\.env
echo # GitHub API配置(可选) >> github-scraper\.env
echo # GITHUB_TOKEN=ghp_xxxxxxxxxxxx >> github-scraper\.env

echo 环境变量文件已创建或更新
echo 如需配置飞书和GitHub API，请编辑github-scraper\.env文件

echo 启动Docker服务...
docker-compose up -d

echo ===================
echo 服务已启动:
echo 后端API服务器地址: http://localhost:5000
echo 前端服务器地址: http://localhost:3000
echo ===================
echo 使用以下命令查看日志:
echo docker-compose logs -f
echo ===================
echo 使用以下命令停止服务:
echo docker-compose down

pause 