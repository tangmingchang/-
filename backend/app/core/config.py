"""
应用配置
"""
from pydantic_settings import BaseSettings
from typing import List
import os
from functools import cached_property


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "影视制作教育智能体"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # OpenAI配置
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./film_education.db"
    
    # 安全配置
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS配置
    CORS_ORIGINS: str = (
        "http://localhost:5173,"
        "http://localhost:5174,"
        "http://localhost:3000,"
        "http://127.0.0.1:5173,"
        "http://127.0.0.1:5174"
    )
    
    def get_cors_origins(self) -> List[str]:
        """将CORS_ORIGINS字符串转换为列表"""
        if isinstance(self.CORS_ORIGINS, str):
            # 过滤掉空字符串
            origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
            return origins
        return self.CORS_ORIGINS if isinstance(self.CORS_ORIGINS, list) else []
    
    # 知识库配置
    KNOWLEDGE_BASE_PATH: str = "./knowledge_base"
    VECTOR_DB_PATH: str = "./vector_db"
    
    # Redis配置（用于Celery和缓存）
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Celery配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # 媒体文件存储配置
    MEDIA_ROOT: str = "./media"
    MEDIA_UPLOAD_MAX_SIZE: int = 500 * 1024 * 1024  # 500MB
    ALLOWED_IMAGE_EXTENSIONS: str = "jpg,jpeg,png,gif,webp"
    ALLOWED_VIDEO_EXTENSIONS: str = "mp4,avi,mov,wmv,flv"
    ALLOWED_AUDIO_EXTENSIONS: str = "mp3,wav,flac,aac"
    
    # AI模型配置
    STABLE_DIFFUSION_API_URL: str = ""  # Stable Diffusion API地址
    STABLE_DIFFUSION_API_KEY: str = ""
    WHISPER_MODEL: str = "base"  # whisper模型大小
    
    # 阿里云百炼（DashScope）配置 - 通义万相文生视频/图生视频
    DASHSCOPE_API_KEY: str = ""  # 阿里云百炼API Key（从环境变量读取，获取地址：https://dashscope.console.aliyun.com/apiKey）
    DASHSCOPE_BASE_URL: str = "https://dashscope.aliyuncs.com/api/v1"  # DashScope API基础URL（北京地域）
    # 通义万相模型配置
    WANX_T2V_MODEL: str = "wan2.5-t2v-preview"  # 文生视频模型（推荐：wan2.5-t2v-preview, wan2.2-t2v-plus）
    WANX_I2V_MODEL: str = "wan2.5-i2v-preview"  # 图生视频模型（推荐：wan2.5-i2v-preview, wan2.2-i2v-flash, wanx2.1-i2v-turbo）
    
    # 阿里云OSS配置（用于图片上传到公网）
    OSS_ACCESS_KEY_ID: str = ""  # OSS AccessKey ID
    OSS_ACCESS_KEY_SECRET: str = ""  # OSS AccessKey Secret
    OSS_BUCKET_NAME: str = ""  # OSS Bucket名称
    OSS_ENDPOINT: str = ""  # OSS Endpoint（如：oss-cn-beijing.aliyuncs.com）
    OSS_BUCKET_DOMAIN: str = ""  # OSS自定义域名（可选，如：https://cdn.example.com）
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # 忽略.env文件中的额外字段（如旧的PIKA_API_KEY、RUNWAY_API_KEY）


settings = Settings()

# 确保目录存在
os.makedirs(settings.KNOWLEDGE_BASE_PATH, exist_ok=True)
os.makedirs(settings.VECTOR_DB_PATH, exist_ok=True)
os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
os.makedirs(os.path.join(settings.MEDIA_ROOT, "images"), exist_ok=True)
os.makedirs(os.path.join(settings.MEDIA_ROOT, "videos"), exist_ok=True)
os.makedirs(os.path.join(settings.MEDIA_ROOT, "audios"), exist_ok=True)
os.makedirs(os.path.join(settings.MEDIA_ROOT, "documents"), exist_ok=True)

