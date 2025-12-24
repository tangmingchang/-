# 构建阶段
FROM node:18-alpine AS builder

WORKDIR /app

# 优先复制依赖定义文件，利用Docker缓存层
COPY package.json package-lock.json ./

RUN npm ci

# 复制源代码并构建
COPY . .

RUN npm run build

# 运行阶段：使用极简的Nginx服务
FROM nginx:alpine

# 将构建产物复制到Nginx目录（Vite构建输出在dist目录）
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制Nginx配置文件（可选，用于SPA路由支持）
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露80端口
EXPOSE 80

# Nginx已在基础镜像中默认启动
CMD ["nginx", "-g", "daemon off;"]

