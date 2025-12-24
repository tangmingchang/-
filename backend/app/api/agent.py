"""
智能体协同API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any
from app.core.security import get_current_active_user
from app.models.user import User
from app.services.agent_orchestrator import orchestrator, SceneType

router = APIRouter()

class SceneRequest(BaseModel):
    """场景请求模型"""
    scene_type: str
    context: Dict[str, Any]

@router.post("/process")
async def process_scene(
    request: SceneRequest,
    current_user: User = Depends(get_current_active_user)
):
    """处理场景，调用相应的智能体"""
    try:
        scene_type = SceneType(request.scene_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的场景类型: {request.scene_type}"
        )
    
    result = await orchestrator.process_scene(
        scene_type=scene_type,
        context=request.context,
        user_role=current_user.role.value
    )
    
    return result

@router.get("/scenes")
async def list_scenes():
    """获取所有可用的场景类型"""
    return {
        "scenes": [
            {
                "type": scene.value,
                "name": {
                    "script_writing": "剧本写作",
                    "storyboard_design": "分镜设计",
                    "video_editing": "视频剪辑",
                    "color_grading": "调色",
                    "sound_design": "声音设计",
                    "evaluation": "评估"
                }.get(scene.value, scene.value)
            }
            for scene in SceneType
        ]
    }












