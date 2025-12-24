"""
CLIP图像分析API
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List
from app.core.security import get_current_active_user
from app.models.user import User
from app.services.clip_service import clip_service
import os
import uuid
from app.core.config import settings

router = APIRouter()

class ImageTextMatchRequest(BaseModel):
    """图像文本匹配请求"""
    image_path: str
    text_options: List[str]

class ImageSearchRequest(BaseModel):
    """图像搜索请求"""
    query_text: str
    image_paths: List[str]
    top_k: int = 5

@router.post("/match")
async def match_image_text(
    request: ImageTextMatchRequest,
    current_user: User = Depends(get_current_active_user)
):
    """匹配图像和文本"""
    result = clip_service.match_image_text(
        request.image_path,
        request.text_options
    )
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@router.post("/search")
async def search_images(
    request: ImageSearchRequest,
    current_user: User = Depends(get_current_active_user)
):
    """根据文本搜索相似图像"""
    result = clip_service.find_similar_images(
        request.query_text,
        request.image_paths,
        request.top_k
    )
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result











