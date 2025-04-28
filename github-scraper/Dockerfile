FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制源代码
COPY . .

# 创建数据目录
RUN mkdir -p /app/data

# 添加执行权限
RUN chmod +x /app/docker-entrypoint.sh

# 设置环境变量
ENV FLASK_APP=api_server.py
ENV FLASK_ENV=production
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ALLOW_ORIGIN=*

# 默认端口
EXPOSE 5000

# 启动命令
ENTRYPOINT ["/app/docker-entrypoint.sh"] 