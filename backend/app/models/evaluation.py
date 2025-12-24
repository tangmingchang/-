"""
评估模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Enum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base

class EvaluationType(str, enum.Enum):
    """评估类型枚举"""
    AI_AUTO = "ai_auto"        # AI自动评估
    TEACHER = "teacher"        # 教师评估
    PEER = "peer"             # 同伴互评
    SELF = "self"             # 自评

class Evaluation(Base):
    """评估表"""
    __tablename__ = "evaluations"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    evaluator_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 评估人（教师或学生）
    evaluation_type = Column(Enum(EvaluationType), nullable=False)
    
    # 技术指标评分（0-10分）
    cinematography_score = Column(Float)  # 摄影技术
    editing_score = Column(Float)  # 剪辑质量
    sound_score = Column(Float)  # 声音质量
    overall_technical_score = Column(Float)  # 总体技术分
    
    # 艺术指标评分（0-10分）
    narrative_score = Column(Float)  # 叙事
    visual_aesthetics_score = Column(Float)  # 视觉美感
    emotional_impact_score = Column(Float)  # 情感感染力
    overall_artistic_score = Column(Float)  # 总体艺术分
    
    # 评语和反馈
    technical_feedback = Column(Text)  # 技术反馈
    artistic_feedback = Column(Text)  # 艺术反馈
    overall_comment = Column(Text)  # 总体评语
    suggestions = Column(Text)  # 改进建议
    teacher_feedback_box = Column(Text)  # 教师留言箱
    
    # 详细分析结果（JSON格式）
    detailed_analysis = Column(JSON)  # AI分析的详细数据
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    project = relationship("Project", back_populates="evaluations")
    evaluator_user = relationship("User", back_populates="evaluations_given", foreign_keys=[evaluator_user_id])












