# 1. 选择官方Python镜像作为基础（推荐使用特定版本，如3.11，确保一致性）
FROM python:3.11-slim

# 2. 设置容器内的工作目录
WORKDIR /app

# 3. 复制依赖列表文件（优先复制此文件，可独立利用Docker缓存层，加速构建）
COPY requirements.txt .

# 4. 安装Python依赖（使用清华镜像加速，适用于国内网络）
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 5. 复制后端所有源代码到容器工作目录
COPY . .

# 6. 暴露后端服务运行的端口（根据你的实际端口修改，如8000, 5000, 8080等）
EXPOSE 8000

# 7. 定义容器启动时执行的命令（这是关键，根据你的项目启动方式修改）
# 以下是几种常见Python框架的启动命令示例：
#    Flask: CMD ["python", "app.py"] 或 CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
#    FastAPI: CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
#    Django: CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
