"""
课程模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Course(Base):
    """课程表"""
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    teacher = relationship("User", back_populates="courses_taught", foreign_keys=[teacher_id])
    enrollments = relationship("CourseEnrollment", back_populates="course", cascade="all, delete-orphan")
    chapters = relationship("Chapter", back_populates="course", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="course", cascade="all, delete-orphan")
    resources = relationship("CourseResource", back_populates="course", cascade="all, delete-orphan")

class CourseEnrollment(Base):
    """课程注册表（学生加入课程）"""
    __tablename__ = "course_enrollments"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    enrolled_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    course = relationship("Course", back_populates="enrollments")
    student = relationship("User", back_populates="course_enrollments")

class Chapter(Base):
    """课程章节表"""
    __tablename__ = "chapters"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text)
    order = Column(Integer, default=0)  # 章节顺序
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    course = relationship("Course", back_populates="chapters")
    resources = relationship("ChapterResource", back_populates="chapter", cascade="all, delete-orphan")

class CourseResource(Base):
    """课程资源表（课件、视频等）"""
    __tablename__ = "course_resources"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String(200), nullable=False)
    resource_type = Column(String(50))  # ppt, video, pdf, link等
    file_path = Column(String(500))  # 文件路径或URL
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    course = relationship("Course", back_populates="resources")

class ChapterResource(Base):
    """章节资源表"""
    __tablename__ = "chapter_resources"
    
    id = Column(Integer, primary_key=True, index=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=False)
    title = Column(String(200), nullable=False)
    resource_type = Column(String(50))
    file_path = Column(String(500))
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    chapter = relationship("Chapter", back_populates="resources")












