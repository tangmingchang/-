"""
视频生成任务模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base


class VideoGenerationStatus(str, enum.Enum):
    """视频生成任务状态枚举"""
    PENDING = "PENDING"           # 等待中
    RUNNING = "RUNNING"           # 运行中
    SUCCEEDED = "SUCCEEDED"       # 成功
    FAILED = "FAILED"             # 失败
    CONCATENATING = "CONCATENATING"  # 拼接中（长视频）


class VideoGenerationJob(Base):
    """视频生成任务表"""
    __tablename__ = "video_generation_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(100), unique=True, nullable=False, index=True)  # 唯一任务ID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 用户ID
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)  # 关联项目（可选）
    
    # 任务参数
    engine = Column(String(50), nullable=False)  # 引擎类型：aliyun（DashScope通义万相）
    mode = Column(String(10), nullable=False)  # 模式：t2v, i2v
    prompt = Column(Text, nullable=False)  # 文本提示
    image_url = Column(String(500))  # 图片URL（图生视频时使用）
    audio_url = Column(String(500))  # 音频URL（可选）
    duration = Column(Integer, nullable=False)  # 视频时长（秒）
    resolution = Column(String(20), nullable=False)  # 分辨率：480P, 720P, 1080P
    model = Column(String(100))  # 使用的模型名称
    audio = Column(String(10), default="false")  # 是否自动配音（字符串存储）
    prompt_extend = Column(String(10), default="true")  # 是否自动润色Prompt
    
    # 任务状态
    status = Column(Enum(VideoGenerationStatus), default=VideoGenerationStatus.PENDING)
    error_message = Column(Text)  # 错误信息
    
    # 任务结果
    task_ids = Column(JSON)  # 子任务ID列表（长视频时可能有多个）
    video_url = Column(String(500))  # 视频URL（DashScope返回的临时URL）
    local_path = Column(String(500))  # 本地存储路径
    usage = Column(JSON)  # API使用量信息（时长、分辨率等）
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)  # 完成时间
    
    # 关系
    user = relationship("User", backref="video_generation_jobs")
    project = relationship("Project", backref="video_generation_jobs")

