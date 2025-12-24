"""
评估系统API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from app.core.database import get_db
from app.core.security import get_current_active_user, require_role
from app.models.user import User, UserRole
from app.models.project import Project, Script, Storyboard
from app.models.evaluation import Evaluation, EvaluationType
from app.services.ai_service import ai_service
import json
import re

router = APIRouter()

class EvaluationCreate(BaseModel):
    """创建评估模型"""
    project_id: int
    evaluation_type: EvaluationType
    # 技术指标
    cinematography_score: Optional[float] = None
    editing_score: Optional[float] = None
    sound_score: Optional[float] = None
    overall_technical_score: Optional[float] = None
    # 艺术指标
    narrative_score: Optional[float] = None
    visual_aesthetics_score: Optional[float] = None
    emotional_impact_score: Optional[float] = None
    overall_artistic_score: Optional[float] = None
    # 评语
    technical_feedback: Optional[str] = None
    artistic_feedback: Optional[str] = None
    overall_comment: Optional[str] = None
    suggestions: Optional[str] = None

class EvaluationResponse(BaseModel):
    """评估响应模型"""
    id: int
    project_id: int
    evaluator_user_id: Optional[int]
    evaluation_type: EvaluationType
    cinematography_score: Optional[float]
    editing_score: Optional[float]
    sound_score: Optional[float]
    overall_technical_score: Optional[float]
    narrative_score: Optional[float]
    visual_aesthetics_score: Optional[float]
    emotional_impact_score: Optional[float]
    overall_artistic_score: Optional[float]
    technical_feedback: Optional[str]
    artistic_feedback: Optional[str]
    overall_comment: Optional[str]
    suggestions: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.post("/", response_model=EvaluationResponse, status_code=status.HTTP_201_CREATED)
async def create_evaluation(
    evaluation_data: EvaluationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建评估"""
    # 检查项目是否存在
    project = db.query(Project).filter(Project.id == evaluation_data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 权限检查
    if evaluation_data.evaluation_type == EvaluationType.TEACHER:
        # 教师评估：必须是教师或管理员，且项目属于其课程
        if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
            raise HTTPException(status_code=403, detail="只有教师可以创建教师评估")
    elif evaluation_data.evaluation_type == EvaluationType.PEER:
        # 同伴互评：必须是学生，且不能评估自己的项目
        if current_user.role != UserRole.STUDENT:
            raise HTTPException(status_code=403, detail="只有学生可以创建同伴互评")
        if project.owner_id == current_user.id:
            raise HTTPException(status_code=400, detail="不能评估自己的项目")
    elif evaluation_data.evaluation_type == EvaluationType.SELF:
        # 自评：必须是项目所有者
        if project.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="只能评估自己的项目")
    
    evaluation = Evaluation(
        project_id=evaluation_data.project_id,
        evaluator_user_id=current_user.id if evaluation_data.evaluation_type != EvaluationType.AI_AUTO else None,
        evaluation_type=evaluation_data.evaluation_type,
        cinematography_score=evaluation_data.cinematography_score,
        editing_score=evaluation_data.editing_score,
        sound_score=evaluation_data.sound_score,
        overall_technical_score=evaluation_data.overall_technical_score,
        narrative_score=evaluation_data.narrative_score,
        visual_aesthetics_score=evaluation_data.visual_aesthetics_score,
        emotional_impact_score=evaluation_data.emotional_impact_score,
        overall_artistic_score=evaluation_data.overall_artistic_score,
        technical_feedback=evaluation_data.technical_feedback,
        artistic_feedback=evaluation_data.artistic_feedback,
        overall_comment=evaluation_data.overall_comment,
        suggestions=evaluation_data.suggestions
    )
    
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)
    return evaluation

@router.get("/project/{project_id}", response_model=List[EvaluationResponse])
async def list_project_evaluations(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取项目的所有评估"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 权限检查：学生只能看自己项目的评估
    if current_user.role == UserRole.STUDENT and project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此项目的评估")
    
    evaluations = db.query(Evaluation).filter(
        Evaluation.project_id == project_id
    ).order_by(Evaluation.created_at.desc()).all()
    
    return evaluations

@router.post("/project/{project_id}/ai-evaluate")
async def ai_evaluate_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """AI自动评估项目（调用智能对话API进行评估）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 权限检查
    if current_user.role == UserRole.STUDENT and project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权评估此项目")
    
    # 获取项目的剧本和分镜内容
    scripts = db.query(Script).filter(Script.project_id == project_id).all()
    storyboards = db.query(Storyboard).filter(Storyboard.project_id == project_id).order_by(Storyboard.order).all()
    
    if not scripts and not storyboards:
        raise HTTPException(status_code=400, detail="项目没有剧本或分镜内容，无法进行评估")
    
    # 构建项目内容摘要
    project_content = f"项目名称：{project.name}\n项目描述：{project.description or '无'}\n\n"
    
    if scripts:
        project_content += "剧本内容：\n"
        for i, script in enumerate(scripts, 1):
            project_content += f"\n【剧本 {i}】{script.title or '未命名'}\n{script.content}\n"
    
    if storyboards:
        project_content += "\n分镜内容：\n"
        for storyboard in storyboards:
            project_content += f"\n场景 {storyboard.scene_number or storyboard.order + 1}：{storyboard.description}\n"
            if storyboard.shot_type:
                project_content += f"景别：{storyboard.shot_type}\n"
            if storyboard.camera_angle:
                project_content += f"镜头角度：{storyboard.camera_angle}\n"
            if storyboard.notes:
                project_content += f"备注：{storyboard.notes}\n"
    
    # 构建评估提示词
    evaluation_prompt = f"""请对以下影视制作项目进行全面评估，从技术和艺术两个维度给出评分和详细反馈。

{project_content}

请按照以下JSON格式返回评估结果：
{{
    "technical_scores": {{
        "cinematography_score": 0-10,
        "editing_score": 0-10,
        "sound_score": 0-10,
        "overall_technical_score": 0-10
    }},
    "artistic_scores": {{
        "narrative_score": 0-10,
        "visual_aesthetics_score": 0-10,
        "emotional_impact_score": 0-10,
        "overall_artistic_score": 0-10
    }},
    "feedback": {{
        "technical_feedback": "技术层面的详细反馈",
        "artistic_feedback": "艺术层面的详细反馈",
        "overall_comment": "总体评价",
        "suggestions": "改进建议"
    }}
}}

请确保：
1. 所有评分都是0-10之间的数字
2. 反馈内容要具体、有建设性
3. 只返回JSON，不要有其他文字"""
    
    try:
        # 调用智能对话的AI服务（使用和智能对话页面相同的方式）
        messages = ai_service.format_messages(
            conversation_history=[{"role": "user", "content": evaluation_prompt}],
            system_prompt="你是一位专业的影视制作评估专家，擅长从技术和艺术两个维度评估影视作品。"
        )
        
        # 使用和智能对话页面完全相同的调用方式
        # 使用和智能对话页面完全相同的调用方式
        response = await ai_service.chat_completion(
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )
        
        # 获取AI回复内容（使用和智能对话页面相同的方式）
        if hasattr(response, 'choices') and len(response.choices) > 0:
            ai_content = response.choices[0].message.content
        else:
            # 如果格式不对，尝试其他方式
            ai_content = str(response)
        
        # 尝试从回复中提取JSON
        json_match = re.search(r'\{[\s\S]*\}', ai_content)
        if json_match:
            evaluation_data = json.loads(json_match.group())
        else:
            # 如果无法解析JSON，创建默认评估
            evaluation_data = {
                "technical_scores": {
                    "cinematography_score": 7.0,
                    "editing_score": 7.0,
                    "sound_score": 7.0,
                    "overall_technical_score": 7.0
                },
                "artistic_scores": {
                    "narrative_score": 7.0,
                    "visual_aesthetics_score": 7.0,
                    "emotional_impact_score": 7.0,
                    "overall_artistic_score": 7.0
                },
                "feedback": {
                    "technical_feedback": ai_content[:500] if len(ai_content) > 500 else ai_content,
                    "artistic_feedback": "",
                    "overall_comment": ai_content,
                    "suggestions": ""
                }
            }
        
        # 创建评估记录
        technical_scores = evaluation_data.get("technical_scores", {})
        artistic_scores = evaluation_data.get("artistic_scores", {})
        feedback = evaluation_data.get("feedback", {})
        
        evaluation = Evaluation(
            project_id=project_id,
            evaluator_user_id=None,  # AI评估没有评估者
            evaluation_type=EvaluationType.AI_AUTO,
            cinematography_score=technical_scores.get("cinematography_score"),
            editing_score=technical_scores.get("editing_score"),
            sound_score=technical_scores.get("sound_score"),
            overall_technical_score=technical_scores.get("overall_technical_score"),
            narrative_score=artistic_scores.get("narrative_score"),
            visual_aesthetics_score=artistic_scores.get("visual_aesthetics_score"),
            emotional_impact_score=artistic_scores.get("emotional_impact_score"),
            overall_artistic_score=artistic_scores.get("overall_artistic_score"),
            technical_feedback=feedback.get("technical_feedback"),
            artistic_feedback=feedback.get("artistic_feedback"),
            overall_comment=feedback.get("overall_comment"),
            suggestions=feedback.get("suggestions")
        )
        
        db.add(evaluation)
        db.commit()
        db.refresh(evaluation)
        
        return {
            "status": "completed",
            "message": "AI评估已完成",
            "evaluation_id": evaluation.id
        }
    
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"AI返回的评估结果格式错误: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"AI评估失败: {str(e)}")











