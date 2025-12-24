"""
游戏化组件API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.services.gamification_service import gamification_service

router = APIRouter()

class QuizAnswerRequest(BaseModel):
    """答题请求"""
    quiz_id: str
    user_answer: str

class StorySeedRequest(BaseModel):
    """故事种子请求"""
    character: Optional[str] = None
    scenario: Optional[str] = None
    conflict: Optional[str] = None

@router.get("/shot-quiz")
async def get_shot_quiz(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取镜头语法小游戏题目
    返回一张随机镜头图片和选项
    """
    try:
        quiz = gamification_service.generate_shot_quiz()
        
        return {
            "success": True,
            "quiz": quiz
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"生成题目失败: {str(e)}"
        )

@router.post("/shot-quiz/answer")
async def check_shot_quiz_answer(
    request: QuizAnswerRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    检查镜头语法小游戏答案
    """
    try:
        result = gamification_service.check_shot_quiz_answer(
            request.quiz_id,
            request.user_answer
        )
        
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"检查答案失败: {str(e)}"
        )

@router.post("/inspiration-dice")
async def roll_inspiration_dice(
    use_llm: bool = False,
    current_user: User = Depends(get_current_active_user)
):
    """
    掷灵感骰子
    随机生成创意点子
    """
    try:
        inspiration = gamification_service.roll_inspiration_dice(use_llm=use_llm)
        
        return {
            "success": True,
            "inspiration": inspiration
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"生成灵感失败: {str(e)}"
        )

@router.post("/story-seed")
async def generate_story_seed(
    request: StorySeedRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    生成故事种子
    可以指定部分元素，其他随机生成
    """
    try:
        elements = {}
        if request.character:
            elements["character"] = request.character
        if request.scenario:
            elements["scenario"] = request.scenario
        if request.conflict:
            elements["conflict"] = request.conflict
        
        seed = gamification_service.generate_story_seed(
            elements if elements else None
        )
        
        return {
            "success": True,
            "seed": seed
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"生成故事种子失败: {str(e)}"
        )

@router.get("/shot-type/{shot_type}")
async def get_shot_type_info(
    shot_type: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    获取镜头类型详细信息
    """
    try:
        info = gamification_service.get_shot_type_info(shot_type)
        
        return {
            "success": True,
            "info": info
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取镜头信息失败: {str(e)}"
        )

