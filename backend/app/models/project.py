"""
项目模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base

class ProjectStatus(str, enum.Enum):
    """项目状态枚举"""
    DRAFT = "draft"           # 草稿
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"   # 已完成
    SUBMITTED = "submitted"   # 已提交

class Project(Base):
    """项目表"""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.DRAFT)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    course = relationship("Course", back_populates="projects")
    owner = relationship("User", back_populates="projects")
    scripts = relationship("Script", back_populates="project", cascade="all, delete-orphan")
    storyboards = relationship("Storyboard", back_populates="project", cascade="all, delete-orphan")
    media_assets = relationship("MediaAsset", back_populates="project", cascade="all, delete-orphan")
    evaluations = relationship("Evaluation", back_populates="project", cascade="all, delete-orphan")
    versions = relationship("ProjectVersion", back_populates="project", cascade="all, delete-orphan")

class ProjectVersion(Base):
    """项目版本表（版本控制）"""
    __tablename__ = "project_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    version_number = Column(String(50), nullable=False)
    description = Column(Text)
    snapshot_data = Column(JSON)  # 版本快照数据
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    project = relationship("Project", back_populates="versions")

class Script(Base):
    """剧本表"""
    __tablename__ = "scripts"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(200))
    content = Column(Text, nullable=False)  # 剧本文本内容
    file_path = Column(String(500))  # 原始文件路径
    analysis_result = Column(JSON)  # AI分析结果（结构、人物、对白等）
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    project = relationship("Project", back_populates="scripts")

class Storyboard(Base):
    """分镜表"""
    __tablename__ = "storyboards"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    scene_number = Column(Integer)  # 场景编号
    description = Column(Text)  # 场景描述
    image_path = Column(String(500))  # 分镜图像路径
    shot_type = Column(String(50))  # 景别（远景、中景、近景等）
    camera_angle = Column(String(50))  # 机位角度
    camera_movement = Column(String(50))  # 镜头运动
    notes = Column(Text)  # 备注说明
    order = Column(Integer, default=0)  # 顺序
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    project = relationship("Project", back_populates="storyboards")

class MediaAsset(Base):
    """媒体素材表"""
    __tablename__ = "media_assets"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(200), nullable=False)
    asset_type = Column(String(50), nullable=False)  # image, video, audio
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)  # 文件大小（字节）
    mime_type = Column(String(100))
    thumbnail_path = Column(String(500))  # 缩略图路径
    asset_metadata = Column(JSON)  # 元数据（分辨率、时长等）
    is_ai_generated = Column(Boolean, default=False)  # 是否AI生成
    ai_model = Column(String(100))  # 使用的AI模型
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    project = relationship("Project", back_populates="media_assets")

