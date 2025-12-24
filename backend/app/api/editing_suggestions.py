"""
AI剪辑建议API
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.services.editing_service import editing_service
import os
import aiofiles
from app.core.config import settings

router = APIRouter()

class EditingAnalysisResponse(BaseModel):
    """剪辑分析响应"""
    success: bool
    scenes: List[dict]
    audio_analysis: dict
    shot_types: List[dict]
    suggestions: List[dict]
    statistics: dict

@router.post("/analyze", response_model=EditingAnalysisResponse)
async def analyze_video_for_editing(
    video_file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    分析视频并生成剪辑建议
    上传视频文件，返回场景检测、节奏分析和剪辑建议
    """
    # 检查文件类型
    allowed_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv']
    file_ext = '.' + video_file.filename.split('.')[-1].lower() if '.' in video_file.filename else ''
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的视频格式。支持的类型: {', '.join(allowed_extensions)}"
        )
    
    # 保存上传的文件
    video_dir = os.path.join(settings.MEDIA_ROOT, "videos")
    os.makedirs(video_dir, exist_ok=True)
    
    video_path = os.path.join(video_dir, f"temp_{current_user.id}_{video_file.filename}")
    
    try:
        # 保存文件
        async with aiofiles.open(video_path, 'wb') as f:
            content = await video_file.read()
            await f.write(content)
        
        # 分析视频
        result = editing_service.analyze_video(video_path)
        
        # 清理临时文件（可选）
        # os.remove(video_path)
        
        return EditingAnalysisResponse(
            success=True,
            scenes=result.get("scenes", []),
            audio_analysis=result.get("audio_analysis", {}),
            shot_types=result.get("shot_types", []),
            suggestions=result.get("suggestions", []),
            statistics=result.get("statistics", {})
        )
    
    except Exception as e:
        # 确保清理临时文件
        if os.path.exists(video_path):
            os.remove(video_path)
        raise HTTPException(
            status_code=500,
            detail=f"视频分析失败: {str(e)}"
        )

@router.post("/suggestions")
async def get_editing_suggestions(
    scenes: List[dict],
    audio_analysis: dict,
    shot_types: List[dict],
    current_user: User = Depends(get_current_active_user)
):
    """
    基于已有分析数据生成剪辑建议
    """
    try:
        suggestions = editing_service.generate_editing_suggestions(
            scenes, audio_analysis, shot_types
        )
        
        return {
            "success": True,
            "suggestions": suggestions,
            "count": len(suggestions)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"生成建议失败: {str(e)}"
        )

