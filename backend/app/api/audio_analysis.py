"""
音频分析与配乐建议API
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.services.audio_service import audio_service
import os
import aiofiles
from app.core.config import settings

router = APIRouter()

class MusicGenerationRequest(BaseModel):
    """音乐生成请求"""
    prompt: str
    duration: int = 30
    scene_context: Optional[str] = None

class AudioAnalysisResponse(BaseModel):
    """音频分析响应"""
    success: bool
    quality_assessment: dict
    sound_events: list
    emotion_analysis: dict
    music_suggestions: dict

@router.post("/analyze", response_model=AudioAnalysisResponse)
async def analyze_audio(
    audio_file: UploadFile = File(...),
    scene_context: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    分析音频文件
    评估语音质量、识别声音事件、分析情绪并推荐配乐
    """
    # 检查文件类型
    allowed_extensions = ['.mp3', '.wav', '.flac', '.aac', '.m4a']
    file_ext = '.' + audio_file.filename.split('.')[-1].lower() if '.' in audio_file.filename else ''
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的音频格式。支持的类型: {', '.join(allowed_extensions)}"
        )
    
    # 保存上传的文件
    audio_dir = os.path.join(settings.MEDIA_ROOT, "audios")
    os.makedirs(audio_dir, exist_ok=True)
    
    audio_path = os.path.join(audio_dir, f"temp_{current_user.id}_{audio_file.filename}")
    
    try:
        # 保存文件
        async with aiofiles.open(audio_path, 'wb') as f:
            content = await audio_file.read()
            await f.write(content)
        
        # 分析音频
        result = audio_service.analyze_audio(audio_path, scene_context)
        
        return AudioAnalysisResponse(
            success=True,
            quality_assessment=result.get("quality_assessment", {}),
            sound_events=result.get("sound_events", []),
            emotion_analysis=result.get("emotion_analysis", {}),
            music_suggestions=result.get("music_suggestions", {})
        )
    
    except Exception as e:
        # 确保清理临时文件
        if os.path.exists(audio_path):
            os.remove(audio_path)
        raise HTTPException(
            status_code=500,
            detail=f"音频分析失败: {str(e)}"
        )

@router.post("/generate-music")
async def generate_music(
    request: MusicGenerationRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    生成配乐
    使用MusicGen根据文本描述生成音乐
    """
    try:
        music_path = audio_service.generate_music(
            request.prompt,
            duration=request.duration
        )
        
        if music_path:
            return {
                "success": True,
                "music_path": music_path,
                "duration": request.duration,
                "prompt": request.prompt
            }
        else:
            return {
                "success": False,
                "message": "音乐生成功能暂不可用，请检查MusicGen是否已安装",
                "suggestion": "可以使用推荐配乐功能"
            }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"音乐生成失败: {str(e)}"
        )

@router.post("/suggest-music")
async def suggest_music(
    scene_description: str,
    emotion: str,
    sound_events: list,
    current_user: User = Depends(get_current_active_user)
):
    """
    推荐配乐
    根据场景描述、情绪和声音事件推荐合适的配乐
    """
    try:
        suggestions = audio_service.suggest_music(
            scene_description,
            emotion,
            sound_events
        )
        
        return {
            "success": True,
            "suggestions": suggestions
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"配乐推荐失败: {str(e)}"
        )

