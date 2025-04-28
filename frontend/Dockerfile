FROM node:18-alpine as build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# 设置API URL环境变量，这会被docker-compose中的环境变量覆盖
ARG REACT_APP_API_URL=http://localhost:5000
ENV REACT_APP_API_URL=$REACT_APP_API_URL

# 设置容器内部API URL环境变量
ARG REACT_APP_CONTAINER_API_URL=http://backend:5000
ENV REACT_APP_CONTAINER_API_URL=$REACT_APP_CONTAINER_API_URL

# 构建生产版本
RUN npm run build

# 用轻量级的nginx来提供静态服务
FROM nginx:alpine

# 复制nginx配置
COPY ./nginx.conf /etc/nginx/conf.d/default.conf

# 从构建阶段复制生成的静态文件
COPY --from=build /app/build /usr/share/nginx/html

# 默认端口
EXPOSE 3000

# nginx默认使用80端口，我们需要修改它
CMD ["nginx", "-g", "daemon off;"] 