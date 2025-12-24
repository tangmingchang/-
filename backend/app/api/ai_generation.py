"""
AI生成API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.project import Project, MediaAsset
from app.tasks.ai_tasks import (
    generate_image_task,
    generate_video_from_text_task,
    generate_video_from_image_task,
    analyze_script_task
)
import os
import uuid

router = APIRouter()

class ImageGenerationRequest(BaseModel):
    """图像生成请求"""
    prompt: str
    negative_prompt: Optional[str] = None
    width: int = 512
    height: int = 512
    project_id: Optional[int] = None

class VideoGenerationRequest(BaseModel):
    """视频生成请求（文生视频）"""
    prompt: str
    duration: int = 5
    project_id: Optional[int] = None

class ImageToVideoRequest(BaseModel):
    """图生视频请求"""
    image_url: str
    prompt: Optional[str] = None
    duration: int = 5  # 视频时长（秒）
    project_id: Optional[int] = None

class ScriptAnalysisRequest(BaseModel):
    """剧本分析请求"""
    script_content: str
    script_id: Optional[int] = None

@router.post("/generate-image")
async def generate_image(
    request: ImageGenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """生成图像（异步任务）"""
    from app.celery_app import CELERY_AVAILABLE
    
    if not CELERY_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Celery未安装，异步任务功能不可用。请运行: pip install celery redis"
        )
    
    # 启动异步任务
    task = generate_image_task.delay(
        request.prompt,
        negative_prompt=request.negative_prompt,
        width=request.width,
        height=request.height
    )
    
    return {
        "task_id": task.id,
        "status": "processing",
        "message": "图像生成任务已提交"
    }

@router.post("/generate-video")
async def generate_video(
    request: VideoGenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    生成视频（已废弃，请使用 /api/video/generate）
    此接口保留用于向后兼容，实际调用新的视频生成API
    """
    from app.services.video_generation_service import video_generation_service
    
    try:
        # 使用新的DashScope通义万相服务
        result = await video_generation_service.generate_video(
            engine="aliyun",
            mode="t2v",
            prompt=request.prompt,
            duration=request.duration,
            resolution="720P",
            audio=True,
            prompt_extend=True
        )
        
        if result and 'error' not in result:
            # 如果有task_id，需要等待任务完成
            if 'task_id' in result:
                # 返回任务ID，让前端轮询
                return {
                    "success": True,
                    "task_id": result.get('task_id'),
                    "message": "视频生成任务已创建，请使用 /api/video/job/{task_id} 查询状态",
                    "deprecated": True,
                    "new_endpoint": "/api/video/generate"
                }
            elif 'local_path' in result or 'video_url' in result:
                video_url = result.get('video_url') or result.get('local_path', '')
                # 保存到项目（如果指定）
                if request.project_id:
                    project = db.query(Project).filter(Project.id == request.project_id).first()
                    if project and project.owner_id == current_user.id:
                        media_asset = MediaAsset(
                            project_id=request.project_id,
                            name=f"Generated Video: {request.prompt[:50]}",
                            asset_type="video",
                            file_path=video_url,
                            file_size=0,
                            mime_type="video/mp4"
                        )
                        db.add(media_asset)
                        db.commit()
                
                return {
                    "success": True,
                    "video_url": video_url,
                    "message": "视频生成成功",
                    "deprecated": True,
                    "new_endpoint": "/api/video/generate"
                }
        
        error_msg = result.get('error', '未知错误') if result else '服务不可用'
        return {
            "success": False,
            "message": f"视频生成失败: {error_msg}",
            "error": error_msg,
            "deprecated": True,
            "new_endpoint": "/api/video/generate"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"视频生成失败: {str(e)}",
            "error": str(e),
            "deprecated": True,
            "new_endpoint": "/api/video/generate"
        }

@router.post("/image-to-video")
async def image_to_video(
    request: ImageToVideoRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    图生视频（已废弃，请使用 /api/video/generate）
    此接口保留用于向后兼容，实际调用新的视频生成API
    """
    from app.services.video_generation_service import video_generation_service
    
    try:
        # 使用新的DashScope通义万相服务
        result = await video_generation_service.generate_video(
            engine="aliyun",
            mode="i2v",
            prompt=request.prompt or "让图片中的场景动起来",
            image_url=request.image_url,
            duration=request.duration,
            resolution="720P",
            audio=True,
            prompt_extend=True
        )
        
        if result and 'error' not in result:
            # 如果有task_id，需要等待任务完成
            if 'task_id' in result:
                # 返回任务ID，让前端轮询
                return {
                    "success": True,
                    "task_id": result.get('task_id'),
                    "message": "视频生成任务已创建，请使用 /api/video/job/{task_id} 查询状态",
                    "duration": request.duration,
                    "deprecated": True,
                    "new_endpoint": "/api/video/generate"
                }
            elif 'local_path' in result or 'video_url' in result:
                video_url = result.get('video_url') or result.get('local_path', '')
                # 保存到项目（如果指定）
                if request.project_id:
                    project = db.query(Project).filter(Project.id == request.project_id).first()
                    if project and project.owner_id == current_user.id:
                        media_asset = MediaAsset(
                            project_id=request.project_id,
                            name=f"Generated Video from Image",
                            asset_type="video",
                            file_path=video_url,
                            file_size=0,
                            mime_type="video/mp4"
                        )
                        db.add(media_asset)
                        db.commit()
                
                return {
                    "success": True,
                    "video_url": video_url,
                    "message": "视频生成成功",
                    "duration": request.duration,
                    "deprecated": True,
                    "new_endpoint": "/api/video/generate"
                }
        
        error_msg = result.get('error', '未知错误') if result else '服务不可用'
        return {
            "success": False,
            "message": f"视频生成失败: {error_msg}",
            "error": error_msg,
            "deprecated": True,
            "new_endpoint": "/api/video/generate"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"视频生成失败: {str(e)}",
            "error": str(e),
            "deprecated": True,
            "new_endpoint": "/api/video/generate"
        }

@router.post("/analyze-script")
async def analyze_script(
    request: ScriptAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    分析剧本（使用通义千问进行深度分析）
    """
    try:
        from app.services.script_analysis_service import script_analysis_service
        result = await script_analysis_service.analyze_script(request.script_content)
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/task/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """获取任务状态"""
    from app.celery_app import celery_app, CELERY_AVAILABLE
    
    if not CELERY_AVAILABLE:
        return {
            "task_id": task_id,
            "status": "error",
            "error": "Celery未安装，异步任务功能不可用。请运行: pip install celery redis"
        }
    
    task = celery_app.AsyncResult(task_id)
    
    if task.state == "PENDING":
        response = {
            "task_id": task_id,
            "status": "pending",
            "message": "任务等待中"
        }
    elif task.state == "PROGRESS":
        response = {
            "task_id": task_id,
            "status": "processing",
            "progress": task.info.get("progress", 0),
            "message": task.info.get("message", "处理中")
        }
    elif task.state == "SUCCESS":
        response = {
            "task_id": task_id,
            "status": "completed",
            "result": task.result
        }
    else:
        response = {
            "task_id": task_id,
            "status": "failed",
            "error": str(task.info)
        }
    
    return response

