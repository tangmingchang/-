"""
增强TTS API
集成Coqui TTS
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from app.core.security import get_current_active_user
from app.models.user import User
from app.services.tts_service import tts_service
import os
import uuid
from app.core.config import settings

router = APIRouter()

class TTSRequest(BaseModel):
    """TTS请求"""
    text: str
    language: str = "zh"
    speaker_wav: Optional[str] = None

@router.post("/synthesize")
async def synthesize_speech(
    request: TTSRequest,
    current_user: User = Depends(get_current_active_user)
):
    """合成语音"""
    output_path = os.path.join(
        settings.MEDIA_ROOT,
        "audios",
        f"tts_{uuid.uuid4()}.wav"
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    result = tts_service.synthesize(
        request.text,
        output_path,
        request.language,
        request.speaker_wav
    )
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return {
        "success": True,
        "audio_url": f"/media/audios/{os.path.basename(output_path)}",
        "output_path": output_path
    }

@router.get("/audio/{filename}")
async def get_audio_file(
    filename: str,
    current_user: User = Depends(get_current_active_user)
):
    """获取生成的音频文件"""
    file_path = os.path.join(settings.MEDIA_ROOT, "audios", filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="文件不存在")











