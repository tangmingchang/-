"""
情绪分析与可视化反馈API
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.services.emotion_service import emotion_service
from app.services.visualization_service import visualization_service
import os
import aiofiles
from app.core.config import settings

router = APIRouter()

class EmotionAnalysisRequest(BaseModel):
    """情绪分析请求"""
    script_content: Optional[str] = None
    scenes: Optional[List[dict]] = None
    audio_path: Optional[str] = None

class EmotionAnalysisResponse(BaseModel):
    """情绪分析响应"""
    success: bool
    text_emotion: Optional[dict] = None
    scene_emotions: Optional[List[dict]] = None
    speech_emotion: Optional[dict] = None
    visualization: Optional[dict] = None

@router.post("/analyze", response_model=EmotionAnalysisResponse)
async def analyze_emotions(
    request: EmotionAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    分析情绪
    结合文本和语音进行多模态情绪分析
    """
    try:
        result = emotion_service.analyze_emotions(
            script_content=request.script_content,
            scenes=request.scenes,
            audio_path=request.audio_path
        )
        
        return EmotionAnalysisResponse(
            success=True,
            text_emotion=result.get("text_emotion"),
            scene_emotions=result.get("scene_emotions"),
            speech_emotion=result.get("speech_emotion"),
            visualization=result.get("visualization")
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"情绪分析失败: {str(e)}"
        )

@router.post("/analyze/audio")
async def analyze_audio_emotion(
    audio_file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    分析音频情绪
    """
    # 保存文件
    audio_dir = os.path.join(settings.MEDIA_ROOT, "audios")
    os.makedirs(audio_dir, exist_ok=True)
    
    audio_path = os.path.join(audio_dir, f"temp_{current_user.id}_{audio_file.filename}")
    
    try:
        async with aiofiles.open(audio_path, 'wb') as f:
            content = await audio_file.read()
            await f.write(content)
        
        result = emotion_service.analyze_speech_emotion(audio_path)
        
        return {
            "success": True,
            "emotion": result
        }
    except Exception as e:
        if os.path.exists(audio_path):
            os.remove(audio_path)
        raise HTTPException(
            status_code=500,
            detail=f"音频情绪分析失败: {str(e)}"
        )

@router.post("/visualize/radar")
async def generate_emotion_radar(
    categories: List[str],
    values: List[float],
    title: str = "情绪雷达图",
    current_user: User = Depends(get_current_active_user)
):
    """
    生成情绪雷达图
    """
    try:
        chart_data = visualization_service.generate_radar_chart(
            categories, values, title
        )
        
        return {
            "success": True,
            "chart_data": chart_data,
            "format": "base64_png"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"生成雷达图失败: {str(e)}"
        )

@router.post("/visualize/heatmap")
async def generate_emotion_heatmap(
    data_matrix: List[List[float]],
    x_labels: List[str],
    y_labels: List[str],
    title: str = "情绪热力图",
    current_user: User = Depends(get_current_active_user)
):
    """
    生成情绪热力图
    """
    try:
        chart_data = visualization_service.generate_heatmap(
            data_matrix, x_labels, y_labels, title
        )
        
        return {
            "success": True,
            "chart_data": chart_data,
            "format": "base64_png"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"生成热力图失败: {str(e)}"
        )

@router.post("/visualize/timeline")
async def generate_emotion_timeline(
    time_points: List[str],
    values: List[float],
    title: str = "情绪时间线",
    y_label: str = "情绪强度",
    current_user: User = Depends(get_current_active_user)
):
    """
    生成情绪时间线图表
    """
    try:
        chart_data = visualization_service.generate_timeline_chart(
            time_points, values, title, y_label
        )
        
        return {
            "success": True,
            "chart_data": chart_data,
            "format": "base64_png"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"生成时间线图表失败: {str(e)}"
        )

