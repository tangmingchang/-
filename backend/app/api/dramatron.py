"""
Dramatron剧本生成API
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from app.core.security import get_current_active_user
from app.models.user import User
from app.services.dramatron_service import dramatron_service

router = APIRouter(prefix="/dramatron", tags=["dramatron"])

class StorylineRequest(BaseModel):
    """故事梗概请求"""
    storyline: str = Field(..., description="故事梗概（logline）")
    model: Optional[str] = Field(None, description="使用的模型名称")

class GenerateScriptRequest(BaseModel):
    """生成完整剧本请求"""
    storyline: str = Field(..., description="故事梗概")
    num_scenes: int = Field(5, ge=1, le=20, description="场景数量")
    num_characters: int = Field(3, ge=1, le=10, description="角色数量")
    model: Optional[str] = Field(None, description="使用的模型名称")

class GenerateTitleRequest(BaseModel):
    """生成标题请求"""
    storyline: str = Field(..., description="故事梗概")
    model: Optional[str] = Field(None, description="使用的模型名称")

class GenerateCharactersRequest(BaseModel):
    """生成角色请求"""
    storyline: str = Field(..., description="故事梗概")
    title: str = Field(..., description="剧本标题")
    num_characters: int = Field(3, ge=1, le=10, description="角色数量")
    model: Optional[str] = Field(None, description="使用的模型名称")

class GenerateScenesRequest(BaseModel):
    """生成场景请求"""
    storyline: str = Field(..., description="故事梗概")
    title: str = Field(..., description="剧本标题")
    characters: List[Dict[str, str]] = Field(..., description="角色列表")
    num_scenes: int = Field(5, ge=1, le=20, description="场景数量")
    model: Optional[str] = Field(None, description="使用的模型名称")

class GenerateDialogRequest(BaseModel):
    """生成对话请求"""
    storyline: str = Field(..., description="故事梗概")
    scene: Dict[str, Any] = Field(..., description="场景信息")
    characters: List[Dict[str, str]] = Field(..., description="角色列表")
    place_description: str = Field(..., description="地点描述")
    model: Optional[str] = Field(None, description="使用的模型名称")

@router.post("/generate-script", response_model=Dict[str, Any])
async def generate_full_script(
    request: GenerateScriptRequest,
    current_user: User = Depends(get_current_active_user)
):
    """生成完整剧本"""
    result = await dramatron_service.generate_full_script(
        storyline=request.storyline,
        num_scenes=request.num_scenes,
        num_characters=request.num_characters,
        model=request.model
    )
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@router.post("/generate-title", response_model=Dict[str, Any])
async def generate_title(
    request: GenerateTitleRequest,
    current_user: User = Depends(get_current_active_user)
):
    """生成剧本标题"""
    result = await dramatron_service.generate_title(
        storyline=request.storyline,
        model=request.model
    )
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@router.post("/generate-characters", response_model=Dict[str, Any])
async def generate_characters(
    request: GenerateCharactersRequest,
    current_user: User = Depends(get_current_active_user)
):
    """生成角色"""
    result = await dramatron_service.generate_characters(
        storyline=request.storyline,
        title=request.title,
        num_characters=request.num_characters,
        model=request.model
    )
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@router.post("/generate-scenes", response_model=Dict[str, Any])
async def generate_scenes(
    request: GenerateScenesRequest,
    current_user: User = Depends(get_current_active_user)
):
    """生成场景"""
    result = await dramatron_service.generate_scenes(
        storyline=request.storyline,
        title=request.title,
        characters=request.characters,
        num_scenes=request.num_scenes,
        model=request.model
    )
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@router.post("/generate-dialog", response_model=Dict[str, Any])
async def generate_dialog(
    request: GenerateDialogRequest,
    current_user: User = Depends(get_current_active_user)
):
    """生成对话"""
    result = await dramatron_service.generate_dialog(
        storyline=request.storyline,
        scene=request.scene,
        characters=request.characters,
        place_description=request.place_description,
        model=request.model
    )
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@router.get("/available")
async def check_available(current_user: User = Depends(get_current_active_user)):
    """检查Dramatron是否可用"""
    return {
        "available": dramatron_service.available,
        "model": dramatron_service.default_model if dramatron_service.available else None
    }

