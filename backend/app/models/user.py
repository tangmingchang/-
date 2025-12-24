"""
用户模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base

class UserRole(str, enum.Enum):
    """用户角色枚举"""
    STUDENT = "student"  # 学生
    TEACHER = "teacher"  # 教师
    ADMIN = "admin"      # 管理员

class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    avatar_url = Column(String(500))  # 头像URL
    role = Column(Enum(UserRole), default=UserRole.STUDENT, nullable=False)
    is_active = Column(Boolean, default=True)
    institution = Column(String(200))  # 所属机构
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    courses_taught = relationship("Course", back_populates="teacher", foreign_keys="Course.teacher_id")
    course_enrollments = relationship("CourseEnrollment", back_populates="student")
    projects = relationship("Project", back_populates="owner")
    evaluations_given = relationship("Evaluation", back_populates="evaluator_user", foreign_keys="Evaluation.evaluator_user_id")

