"""
视频编辑API
集成MoviePy和Auto-Editor
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List
from app.core.security import get_current_active_user
from app.models.user import User
from app.services.video_editing_service import video_editing_service
from app.services.auto_editor_service import auto_editor_service
import os
import uuid
from app.core.config import settings

router = APIRouter()

class VideoCutRequest(BaseModel):
    """视频裁剪请求"""
    video_path: str
    start_time: float
    end_time: float

class VideoConcatenateRequest(BaseModel):
    """视频拼接请求"""
    video_paths: List[str]

class VideoTextOverlayRequest(BaseModel):
    """视频文字叠加请求"""
    video_path: str
    text: str
    position: str = "center"
    font_size: int = 50
    color: str = "white"
    duration: Optional[float] = None

class AutoEditRequest(BaseModel):
    """自动剪辑请求"""
    video_path: str
    method: str = "audio"  # audio, motion
    threshold: float = 0.04
    margin: float = 0.2

@router.post("/cut")
async def cut_video(
    request: VideoCutRequest,
    current_user: User = Depends(get_current_active_user)
):
    """裁剪视频"""
    output_path = os.path.join(
        settings.MEDIA_ROOT,
        "videos",
        f"cut_{uuid.uuid4()}.mp4"
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    result = video_editing_service.cut_video(
        request.video_path,
        request.start_time,
        request.end_time,
        output_path
    )
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@router.post("/concatenate")
async def concatenate_videos(
    request: VideoConcatenateRequest,
    current_user: User = Depends(get_current_active_user)
):
    """拼接多个视频"""
    output_path = os.path.join(
        settings.MEDIA_ROOT,
        "videos",
        f"concat_{uuid.uuid4()}.mp4"
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    result = video_editing_service.concatenate_videos(
        request.video_paths,
        output_path
    )
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@router.post("/add-text")
async def add_text_overlay(
    request: VideoTextOverlayRequest,
    current_user: User = Depends(get_current_active_user)
):
    """添加文字叠加"""
    output_path = os.path.join(
        settings.MEDIA_ROOT,
        "videos",
        f"text_{uuid.uuid4()}.mp4"
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    result = video_editing_service.add_text_overlay(
        request.video_path,
        request.text,
        output_path,
        request.position,
        request.font_size,
        request.color,
        request.duration
    )
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@router.post("/auto-edit")
async def auto_edit_video(
    request: AutoEditRequest,
    current_user: User = Depends(get_current_active_user)
):
    """自动剪辑视频"""
    output_path = os.path.join(
        settings.MEDIA_ROOT,
        "videos",
        f"auto_{uuid.uuid4()}.mp4"
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    result = auto_editor_service.auto_edit(
        request.video_path,
        output_path,
        request.method,
        request.threshold,
        request.margin
    )
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@router.get("/info/{video_path:path}")
async def get_video_info(
    video_path: str,
    current_user: User = Depends(get_current_active_user)
):
    """获取视频信息"""
    result = video_editing_service.get_video_info(video_path)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result











