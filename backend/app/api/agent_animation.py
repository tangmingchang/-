"""
智能体反馈动画API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.services.agent_animation_service import agent_animation_service

router = APIRouter()

class AnimationRequest(BaseModel):
    """动画请求"""
    text: Optional[str] = None
    action: Optional[str] = None  # nod, shake, smile, think, point, speak
    context: Optional[str] = None
    emotion: str = "neutral"  # positive, negative, thinking, confirming, explaining
    avatar_image: Optional[str] = None

class AnimationResponse(BaseModel):
    """动画响应"""
    success: bool
    animation_type: str
    animation_path: Optional[str] = None
    animation_data: Optional[str] = None
    action: Optional[dict] = None
    message: Optional[str] = None

@router.post("/generate", response_model=AnimationResponse)
async def generate_animation(
    request: AnimationRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    生成智能体动画
    根据文本、动作或上下文生成相应的动画反馈
    """
    try:
        # 如果提供了文本且较长，生成说话动画
        if request.text and len(request.text) > 10:
            result = agent_animation_service.generate_speaking_animation(
                request.text,
                avatar_image=request.avatar_image
            )
        # 如果指定了动作，生成手势动画
        elif request.action:
            result = agent_animation_service.generate_gesture_animation(
                request.action,
                avatar_image=request.avatar_image
            )
        # 否则根据上下文生成反馈动画
        elif request.context:
            result = agent_animation_service.generate_feedback_animation(
                request.context,
                emotion=request.emotion,
                avatar_image=request.avatar_image
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="请提供text、action或context中的至少一个"
            )
        
        return AnimationResponse(
            success=result.get("success", False),
            animation_type=result.get("animation_type", "unknown"),
            animation_path=result.get("animation_path"),
            animation_data=result.get("animation_data"),
            action=result.get("action"),
            message=result.get("message")
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"生成动画失败: {str(e)}"
        )

@router.post("/speaking")
async def generate_speaking_animation(
    text: str,
    avatar_image: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """
    生成说话动画
    使用Wav2Lip将文本转换为说话动画
    """
    try:
        result = agent_animation_service.generate_speaking_animation(
            text,
            avatar_image=avatar_image
        )
        
        return {
            "success": result.get("success", False),
            "animation": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"生成说话动画失败: {str(e)}"
        )

@router.post("/gesture")
async def generate_gesture_animation(
    action: str,
    avatar_image: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """
    生成手势动画
    支持的动作: nod, shake, smile, think, point
    """
    try:
        result = agent_animation_service.generate_gesture_animation(
            action,
            avatar_image=avatar_image
        )
        
        return {
            "success": result.get("success", False),
            "animation": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"生成手势动画失败: {str(e)}"
        )

@router.get("/trigger-rules")
async def get_animation_trigger_rules(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取动画触发规则
    返回不同情境下应该触发的动画类型
    """
    rules = agent_animation_service.get_animation_trigger_rules()
    
    return {
        "success": True,
        "rules": rules
    }

