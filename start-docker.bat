@echo off
REM GitHub爬虫工具Docker启动脚本 - Windows版本

REM 检查docker是否安装
where docker >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo 错误: 没有找到docker命令。请安装Docker: https://docs.docker.com/get-docker/
    pause
    exit /b 1
)

REM 检查docker-compose
where docker-compose >nul 2>&1
if %ERRORLEVEL% neq 0 (
    REM 检查是否可以使用docker compose命令（Docker新版本使用）
    docker compose version >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo 错误: 没有找到docker-compose或docker compose命令。
        echo 请安装Docker Compose: https://docs.docker.com/compose/install/
        echo 或者使用Docker Desktop，它已包含Docker Compose。
        pause
        exit /b 1
    ) else (
        echo 检测到新版Docker Compose (docker compose)，将使用它替代docker-compose
        REM 创建临时批处理文件作为docker-compose别名
        echo @echo off > "%TEMP%\docker-compose.bat"
        echo docker compose %* >> "%TEMP%\docker-compose.bat"
        set "PATH=%TEMP%;%PATH%"
    )
)

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

if %ERRORLEVEL% neq 0 (
    echo 错误: 启动Docker服务失败。
    echo 如果你使用的是新版Docker，请尝试使用 'docker compose up -d' 命令。
    echo 或者安装docker-compose: https://docs.docker.com/compose/install/
    pause
    exit /b 1
)

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