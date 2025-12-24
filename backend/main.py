"""
影视制作教育智能体 - 后端主程序
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import os
from app.core.config import settings
from app.api import (
    chat, knowledge, health, auth, courses, projects, ai_generation, 
    evaluations, agent, websocket, script_analysis, editing_suggestions,
    audio_analysis, emotion_analysis, speech_to_text, agent_animation,
    visualization, gamification, video_editing, clip_analysis, tts_enhanced,
    dramatron, pdf_reader, video_generation, admin
)
from app.core.database import engine, Base
from app.models import *  # 导入所有模型

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="影视制作教育智能体平台API",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS配置
# 获取允许的源列表
cors_origins = settings.get_cors_origins()
# 在开发模式下，添加常见的开发端口
if settings.DEBUG:
    additional_origins = [
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    cors_origins = list(set(cors_origins + additional_origins))

# 如果需要添加其他生产环境地址，在这里添加
# production_origins = [
#     "http://your-domain.com",
#     "https://your-domain.com",
# ]
# cors_origins = list(set(cors_origins + production_origins))

# 确保包含所有必要的源
if "http://localhost:5174" not in cors_origins:
    cors_origins.append("http://localhost:5174")
if "http://127.0.0.1:5174" not in cors_origins:
    cors_origins.append("http://127.0.0.1:5174")
if "http://localhost:5173" not in cors_origins:
    cors_origins.append("http://localhost:5173")
if "http://127.0.0.1:5173" not in cors_origins:
    cors_origins.append("http://127.0.0.1:5173")


app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # 预检请求缓存时间（秒）
)


# 静态文件服务（用于头像等媒体文件）
media_dir = os.path.join(os.path.dirname(__file__), "media")
os.makedirs(media_dir, exist_ok=True)
os.makedirs(os.path.join(media_dir, "avatars"), exist_ok=True)

@app.get("/media/{file_path:path}")
async def serve_media(file_path: str):
    """提供媒体文件访问"""
    try:
        full_path = os.path.join(media_dir, file_path)
        
        if os.path.exists(full_path) and os.path.isfile(full_path):
            # 根据文件扩展名设置正确的媒体类型
            if file_path.lower().endswith(('.jpg', '.jpeg')):
                return FileResponse(full_path, media_type="image/jpeg")
            elif file_path.lower().endswith('.png'):
                return FileResponse(full_path, media_type="image/png")
            elif file_path.lower().endswith('.gif'):
                return FileResponse(full_path, media_type="image/gif")
            elif file_path.lower().endswith('.webp'):
                return FileResponse(full_path, media_type="image/webp")
            else:
                return FileResponse(full_path)
        else:
            raise HTTPException(status_code=404, detail=f"文件不存在: {file_path}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件访问错误: {str(e)}")

# 静态文件服务（用于books文件夹中的PDF文件）
books_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "public", "books")
os.makedirs(books_dir, exist_ok=True)

@app.get("/books/{file_path:path}")
async def serve_books(file_path: str):
    """提供books文件夹中的文件访问（PDF等）"""
    full_path = os.path.join(books_dir, file_path)
    if os.path.exists(full_path) and os.path.isfile(full_path):
        return FileResponse(full_path, media_type="application/pdf" if full_path.endswith('.pdf') else None)
    raise HTTPException(status_code=404, detail="文件不存在")

# 静态文件服务（用于knowledge_base中的文档）
knowledge_base_dir = os.path.join(os.path.dirname(__file__), "knowledge_base")
os.makedirs(knowledge_base_dir, exist_ok=True)

@app.get("/knowledge/{file_path:path}")
async def serve_knowledge(file_path: str):
    """提供knowledge_base文件夹中的文件访问（PDF、文档等）"""
    full_path = os.path.join(knowledge_base_dir, file_path)
    if os.path.exists(full_path) and os.path.isfile(full_path):
        # 根据文件扩展名设置媒体类型
        media_type = None
        if full_path.endswith('.pdf'):
            media_type = "application/pdf"
        elif full_path.endswith('.txt'):
            media_type = "text/plain"
        elif full_path.endswith('.docx'):
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif full_path.endswith('.doc'):
            media_type = "application/msword"
        elif full_path.endswith('.md'):
            media_type = "text/markdown"
        return FileResponse(full_path, media_type=media_type)
    raise HTTPException(status_code=404, detail="文件不存在")

# 注册路由
app.include_router(health.router, prefix="/api", tags=["健康检查"])
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(courses.router, prefix="/api/courses", tags=["课程管理"])
app.include_router(projects.router, prefix="/api/projects", tags=["项目管理"])
app.include_router(ai_generation.router, prefix="/api/ai", tags=["AI生成"])
app.include_router(evaluations.router, prefix="/api/evaluations", tags=["评估系统"])
app.include_router(agent.router, prefix="/api/agent", tags=["智能体协同"])
app.add_websocket_route("/ws/{room}", websocket.websocket_endpoint)
app.include_router(chat.router, prefix="/api", tags=["智能对话"])
app.include_router(knowledge.router, prefix="/api", tags=["知识库"])
app.include_router(admin.router, tags=["管理员"])

# 新增功能模块路由
app.include_router(script_analysis.router, prefix="/api/script", tags=["剧本分析"])
app.include_router(editing_suggestions.router, prefix="/api/editing", tags=["剪辑建议"])
app.include_router(audio_analysis.router, prefix="/api/audio", tags=["音频分析"])
app.include_router(emotion_analysis.router, prefix="/api/emotion", tags=["情绪分析"])
app.include_router(speech_to_text.router, prefix="/api/speech", tags=["语音识别"])
app.include_router(agent_animation.router, prefix="/api/animation", tags=["智能体动画"])
app.include_router(visualization.router, prefix="/api/visualization", tags=["可视化"])
app.include_router(gamification.router, prefix="/api/game", tags=["游戏化组件"])

# 新增集成模型的路由
app.include_router(video_editing.router, prefix="/api/video-editing", tags=["视频编辑"])
app.include_router(clip_analysis.router, prefix="/api/clip", tags=["图像分析"])
app.include_router(tts_enhanced.router, prefix="/api/tts", tags=["文本转语音"])
app.include_router(dramatron.router, prefix="/api", tags=["Dramatron剧本生成"])
app.include_router(pdf_reader.router, prefix="/api", tags=["PDF阅读器"])

# 视频生成路由（通义万相）
app.include_router(video_generation.router, tags=["视频生成"])

@app.get("/")
async def root():
    return {
        "message": "欢迎使用影视制作教育智能体平台",
        "version": settings.APP_VERSION,
        "docs": "/api/docs"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )

