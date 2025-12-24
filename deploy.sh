#!/bin/bash
# 部署脚本 - 用于在云服务器上部署项目

set -e

echo "=========================================="
echo "开始部署影视教育AI智能助手平台"
echo "=========================================="

# 1. 进入项目目录
cd /root/python-znt || {
    echo "项目目录不存在，正在克隆..."
    git clone https://github.com/tangmingchang/-.git /root/python-znt
    cd /root/python-znt
}

# 2. 拉取最新代码
echo "正在拉取最新代码..."
git pull origin main

# 3. 停止现有容器
echo "停止现有容器..."
docker stop film-backend film-frontend 2>/dev/null || true
docker rm film-backend film-frontend 2>/dev/null || true

# 4. 构建后端镜像
echo "构建后端镜像..."
cd backend
docker build -t film-backend .
cd ..

# 5. 构建前端镜像
echo "构建前端镜像..."
cd frontend
docker build -t film-frontend .
cd ..

# 6. 启动后端容器
echo "启动后端容器..."
docker run -d \
  --name film-backend \
  --restart=always \
  -p 8000:8000 \
  -v /root/python-znt/backend/.env:/app/.env \
  -v /root/python-znt/backend/media:/app/media \
  -v /root/python-znt/backend/film_education.db:/app/film_education.db \
  -v /root/python-znt/backend/knowledge_base:/app/knowledge_base \
  -v /root/python-znt/backend/chroma_db:/app/chroma_db \
  film-backend

# 7. 启动前端容器
echo "启动前端容器..."
docker run -d \
  --name film-frontend \
  --restart=always \
  -p 80:80 \
  --link film-backend:backend \
  film-frontend

# 8. 等待服务启动
echo "等待服务启动..."
sleep 5

# 9. 检查服务状态
echo "检查服务状态..."
docker ps | grep -E "film-backend|film-frontend"

echo "=========================================="
echo "部署完成！"
echo "后端服务: http://39.105.198.28:8000"
echo "前端服务: http://39.105.198.28"
echo "=========================================="

