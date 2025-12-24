"""
语音识别API
使用Whisper进行语音转文字
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
try:
    from app.services.speech_service import speech_service
except Exception:
    speech_service = None

try:
    from app.services.whisperx_service import whisperx_service
except Exception:
    whisperx_service = None
import os
import aiofiles
from app.core.config import settings

router = APIRouter()

class TranscriptionRequest(BaseModel):
    """转写请求"""
    language: Optional[str] = None  # 语言代码，如 "zh", "en"
    task: str = "transcribe"  # transcribe 或 translate

class TranscriptionResponse(BaseModel):
    """转写响应"""
    success: bool
    text: str
    segments: list
    language: str
    subtitle_file: Optional[str] = None

@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    audio_file: UploadFile = File(...),
    language: Optional[str] = None,
    task: str = "transcribe",
    generate_subtitle: bool = True,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    转写音频文件
    将语音转换为文字，可选择生成字幕文件
    """
    # 检查文件类型
    allowed_extensions = ['.mp3', '.wav', '.flac', '.aac', '.m4a', '.mp4', '.avi', '.mov']
    file_ext = '.' + audio_file.filename.split('.')[-1].lower() if '.' in audio_file.filename else ''
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式。支持的类型: {', '.join(allowed_extensions)}"
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
        
        # 转写（优先使用WhisperX如果可用）
        use_whisperx = whisperx_service and whisperx_service.whisperx_available
        
        if use_whisperx and whisperx_service:
            result = whisperx_service.transcribe(
                audio_path,
                language=language,
                align=True,
                diarize=False
            )
            if "error" in result:
                # WhisperX失败，回退到普通Whisper
                use_whisperx = False
        
        if not use_whisperx:
            if not speech_service:
                raise HTTPException(
                    status_code=503,
                    detail="语音识别服务不可用，请检查服务配置"
                )
            if generate_subtitle:
                result = speech_service.transcribe_with_subtitle(
                    audio_path,
                    output_dir=audio_dir,
                    language=language
                )
            else:
                result = speech_service.transcribe(audio_path, language=language, task=task)
        
        return TranscriptionResponse(
            success=True,
            text=result.get("text", ""),
            segments=result.get("segments", []),
            language=result.get("language", language or "unknown"),
            subtitle_file=result.get("subtitle_file")
        )
    
    except Exception as e:
        # 确保清理临时文件
        if os.path.exists(audio_path):
            os.remove(audio_path)
        raise HTTPException(
            status_code=500,
            detail=f"语音转写失败: {str(e)}"
        )

@router.post("/batch-transcribe")
async def batch_transcribe(
    audio_files: list[UploadFile] = File(...),
    language: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """
    批量转写多个音频文件
    """
    results = []
    
    for audio_file in audio_files:
        try:
            # 保存文件
            audio_dir = os.path.join(settings.MEDIA_ROOT, "audios")
            os.makedirs(audio_dir, exist_ok=True)
            
            audio_path = os.path.join(audio_dir, f"temp_{current_user.id}_{audio_file.filename}")
            
            async with aiofiles.open(audio_path, 'wb') as f:
                content = await audio_file.read()
                await f.write(content)
            
            # 转写
            if not speech_service:
                raise HTTPException(
                    status_code=503,
                    detail="语音识别服务不可用，请检查服务配置"
                )
            result = speech_service.transcribe(audio_path, language=language)
            result["filename"] = audio_file.filename
            results.append(result)
        
        except Exception as e:
            results.append({
                "filename": audio_file.filename,
                "success": False,
                "error": str(e)
            })
    
    return {
        "success": True,
        "results": results,
        "total": len(results)
    }

@router.post("/generate-subtitle")
async def generate_subtitle_from_segments(
    segments: list,
    output_filename: str = "subtitle.srt",
    current_user: User = Depends(get_current_active_user)
):
    """
    从分段数据生成字幕文件
    """
    try:
        audio_dir = os.path.join(settings.MEDIA_ROOT, "audios")
        os.makedirs(audio_dir, exist_ok=True)
        
        subtitle_path = os.path.join(audio_dir, output_filename)
        
        if not speech_service:
            raise HTTPException(
                status_code=503,
                detail="语音识别服务不可用，请检查服务配置"
            )
        speech_service.generate_subtitle_file(segments, subtitle_path)
        
        return {
            "success": True,
            "subtitle_file": subtitle_path,
            "segments_count": len(segments)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"生成字幕文件失败: {str(e)}"
        )

