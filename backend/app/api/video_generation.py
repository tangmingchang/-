"""
视频生成API
支持文生视频（T2V）和图生视频（I2V）
使用阿里云DashScope通义万相
"""
import os
import uuid
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.core.config import settings
from app.models.user import User
from app.models.video_generation import VideoGenerationJob, VideoGenerationStatus
from app.services.video_generation_service import video_generation_service
from app.services.dashscope_service import dashscope_service
from app.services.oss_service import image_upload_service

router = APIRouter(prefix="/api/video", tags=["视频生成"])


class VideoGenerationRequest(BaseModel):
    """视频生成请求"""
    engine: str = Field("aliyun", description="引擎类型：aliyun（DashScope通义万相）")
    mode: str = Field(..., description="生成模式：t2v（文生视频）或 i2v（图生视频）")
    prompt: str = Field(..., description="文本提示（中文）")
    image_url: Optional[str] = Field(None, description="图片URL（图生视频时必填）")
    audio_url: Optional[str] = Field(None, description="音频URL（可选，音频驱动）")
    duration: int = Field(5, ge=3, le=20, description="视频时长（秒，3-20）")
    resolution: str = Field("720P", description="分辨率：480P, 720P, 1080P")
    model: Optional[str] = Field(None, description="模型名称（可选，使用默认模型）")
    audio: bool = Field(True, description="是否自动配音（仅aliyun引擎的wan2.5支持）")
    prompt_extend: bool = Field(True, description="是否自动润色Prompt")
    project_id: Optional[int] = Field(None, description="关联项目ID（可选）")


class VideoGenerationResponse(BaseModel):
    """视频生成响应"""
    job_id: str
    status: str
    message: str
    task_ids: Optional[list] = None  # 长视频时可能有多个任务ID


async def process_video_generation(
    job_id: str,
    task_ids: list,
    segment_durations: list,
    db: Session
):
    """
    后台任务：等待所有子任务完成并拼接视频（长视频场景）
    """
    try:
        # 等待所有任务完成并拼接
        result = await video_generation_service.wait_and_concatenate_aliyun_tasks(
            task_ids=task_ids,
            segment_durations=segment_durations,
            max_wait_time=600,
            poll_interval=10
        )
        
        # 更新任务状态
        job = db.query(VideoGenerationJob).filter(VideoGenerationJob.job_id == job_id).first()
        if job:
            if "error" in result:
                job.status = VideoGenerationStatus.FAILED
                job.error_message = result.get("error", "未知错误")
            else:
                job.status = VideoGenerationStatus.SUCCEEDED
                job.local_path = result.get("output_path")
                job.completed_at = datetime.utcnow()
            
            db.commit()
    except Exception as e:
        # 更新任务为失败状态
        job = db.query(VideoGenerationJob).filter(VideoGenerationJob.job_id == job_id).first()
        if job:
            job.status = VideoGenerationStatus.FAILED
            job.error_message = str(e)
            db.commit()


@router.post("/upload-image")
async def upload_image_for_video(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    上传图片用于图生视频
    自动将图片上传到公网可访问的位置（OSS或图床）
    
    Returns:
        包含公网图片URL的响应
    """
    # 检查文件类型
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="只支持图片文件（jpg, png, gif, webp等）"
        )
    
    # 读取文件内容
    file_content = await file.read()
    file_ext = os.path.splitext(file.filename)[1] or ".jpg"
    
    # 上传到公网
    upload_result = await image_upload_service.upload_image_content(
        file_content=file_content,
        file_ext=file_ext,
        use_fallback=True
    )
    
    if upload_result.get("success"):
        return {
            "success": True,
            "image_url": upload_result["public_url"],
            "message": upload_result.get("message", "图片上传成功"),
            "object_key": upload_result.get("object_key")
        }
    else:
        raise HTTPException(
            status_code=500,
            detail=f"图片上传失败: {upload_result.get('message', '未知错误')}"
        )


@router.post("/generate", response_model=VideoGenerationResponse)
async def generate_video(
    engine: str = Form("aliyun"),
    mode: str = Form(...),
    prompt: str = Form(...),
    image_url: Optional[str] = Form(None),
    audio_url: Optional[str] = Form(None),
    duration: str = Form("5"),  # 接收字符串，然后转换
    resolution: str = Form("720P"),
    model: Optional[str] = Form(None),
    audio: str = Form("true"),  # 接收字符串，然后转换
    prompt_extend: str = Form("true"),  # 接收字符串，然后转换
    project_id: Optional[int] = Form(None),
    image_file: Optional[UploadFile] = File(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    生成视频（统一接口）
    
    支持：
    - 文生视频（T2V）：根据文本描述生成视频
    - 图生视频（I2V）：根据图片生成动态视频（支持直接上传图片文件）
    - 引擎：aliyun（DashScope通义万相）
    - 时长：3-20秒（超过10秒会自动分段生成并拼接）
    
    图生视频时，可以：
    1. 直接上传图片文件（image_file参数）
    2. 或提供公网可访问的图片URL（image_url参数）
    """
    # 处理图片上传（如果是图生视频且提供了图片文件）
    if mode == "i2v" and image_file:
        try:
            # 读取图片文件
            file_content = await image_file.read()
            file_ext = os.path.splitext(image_file.filename)[1] or ".jpg"
            print(f"[视频生成] 开始上传图片: filename={image_file.filename}, size={len(file_content)} bytes, ext={file_ext}")
            
            # 上传到公网
            upload_result = await image_upload_service.upload_image_content(
                file_content=file_content,
                file_ext=file_ext,
                use_fallback=True
            )
            
            print(f"[视频生成] 图片上传结果: {upload_result}")
            
            if upload_result.get("success"):
                image_url = upload_result["public_url"]
                print(f"[视频生成] 图片上传成功: {image_url}")
            else:
                # 如果上传失败，尝试保存到本地并使用本地HTTP服务
                error_msg = upload_result.get('message', '未知错误')
                print(f"[视频生成] 图片上传失败: {error_msg}，尝试使用本地文件方案")
                
                # 保存图片到本地media目录
                # uuid已在文件顶部导入，不需要重复导入
                import base64
                from pathlib import Path
                
                # 保存图片到本地media目录
                backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                media_dir = os.path.join(backend_dir, "media", "images")
                os.makedirs(media_dir, exist_ok=True)
                
                # 生成唯一文件名
                filename = f"{uuid.uuid4().hex}{file_ext}"
                local_path = os.path.join(media_dir, filename)
                
                # 保存文件
                with open(local_path, "wb") as f:
                    f.write(file_content)
                
                # 使用本地HTTP服务URL
                # 注意：DashScope API需要公网可访问的URL，但我们可以使用base64编码
                # 在dashscope_service中会检测localhost URL并自动转换为base64
                api_url = os.getenv("API_URL", "http://localhost:8000")
                image_url = f"{api_url}/media/images/{filename}"
                print(f"[视频生成] 图片已保存到本地: {local_path}")
                print(f"[视频生成] 使用本地URL（将在DashScope服务中转换为base64）: {image_url}")
        except HTTPException:
            raise
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"[视频生成] 图片上传异常: {e}")
            print(f"[视频生成] 异常堆栈: {error_trace}")
            raise HTTPException(
                status_code=500,
                detail=f"图片上传处理失败: {str(e)}"
            )
    
    # 转换类型参数（FormData发送的是字符串）
    try:
        duration_int = int(duration) if isinstance(duration, str) else duration
        # 验证duration范围
        if duration_int < 3 or duration_int > 20:
            raise HTTPException(
                status_code=400,
                detail=f"视频时长必须在3-20秒之间，当前值: {duration_int}"
            )
    except HTTPException:
        raise
    except (ValueError, TypeError) as e:
        print(f"[视频生成] duration转换失败: {duration}, 错误: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"无效的时长参数: {duration}，必须是3-20之间的整数"
        )
    
    try:
        audio_bool = audio.lower() in ("true", "1", "yes") if isinstance(audio, str) else bool(audio)
    except Exception as e:
        print(f"[视频生成] audio转换失败: {audio}, 错误: {e}")
        audio_bool = True  # 默认值
    
    try:
        prompt_extend_bool = prompt_extend.lower() in ("true", "1", "yes") if isinstance(prompt_extend, str) else bool(prompt_extend)
    except Exception as e:
        print(f"[视频生成] prompt_extend转换失败: {prompt_extend}, 错误: {e}")
        prompt_extend_bool = True  # 默认值
    
    # 验证必需参数
    if not prompt or not prompt.strip():
        raise HTTPException(
            status_code=400,
            detail="prompt参数不能为空"
        )
    
    # 验证图生视频必须提供图片
    if mode == "i2v" and not image_url:
        raise HTTPException(
            status_code=400,
            detail="图生视频模式需要提供图片：请上传图片文件（image_file）或提供图片URL（image_url）"
        )
    
    # 生成唯一任务ID
    job_id = f"video_{uuid.uuid4().hex[:16]}"
    
    # 创建任务记录
    job = VideoGenerationJob(
        job_id=job_id,
        user_id=current_user.id,
        project_id=project_id,
        engine=engine,
        mode=mode,
        prompt=prompt,
        image_url=image_url,  # 使用处理后的图片URL
        audio_url=audio_url,
        duration=duration_int,
        resolution=resolution,
        model=model,
        audio="true" if audio_bool else "false",
        prompt_extend="true" if prompt_extend_bool else "false",
        status=VideoGenerationStatus.PENDING
    )
    try:
        db.add(job)
        db.commit()
        db.refresh(job)
    except Exception as e:
        print(f"[视频生成] 数据库操作失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"创建任务记录失败: {str(e)}"
        )
    
    try:
        # 调用视频生成服务
        print(f"[视频生成] 开始生成视频: mode={mode}, prompt={prompt[:50]}..., duration={duration_int}, resolution={resolution}")
        print(f"[视频生成] 参数详情: audio={audio_bool}, prompt_extend={prompt_extend_bool}, image_url={'已提供' if image_url else '未提供'}")
        
        result = await video_generation_service.generate_video(
            engine=engine,
            mode=mode,
            prompt=prompt,
            image_url=image_url,  # 使用处理后的图片URL
            audio_url=audio_url,
            duration=duration_int,
            resolution=resolution,
            model=model,
            audio=audio_bool,
            prompt_extend=prompt_extend_bool
        )
        
        print(f"[视频生成] 生成服务返回: {result}")
        print(f"[视频生成] 返回结果类型: {type(result)}, 包含的键: {list(result.keys()) if isinstance(result, dict) else '非字典类型'}")
        
        # 检查result是否为None或空
        if not result:
            print(f"[视频生成] 错误: 生成服务返回空结果")
            raise HTTPException(
                status_code=500,
                detail="视频生成服务返回空结果"
            )
        
        # 处理结果
        if "error" in result:
            # 更新任务状态为失败
            job.status = VideoGenerationStatus.FAILED
            job.error_message = result.get("error", "未知错误")
            db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": result.get("error"),
                    "message": result.get("message", "视频生成失败"),
                    "help": result.get("help", {})
                }
            )
        
        # 检查是否是长视频（需要拼接）
        if "task_ids" in result:
            # 长视频：需要等待所有任务完成并拼接
            task_ids = result["task_ids"]
            segment_durations = result.get("segment_durations", [])
            
            # 更新任务记录
            job.status = VideoGenerationStatus.CONCATENATING
            job.task_ids = task_ids
            db.commit()
            
            # 启动后台任务处理拼接
            background_tasks.add_task(
                process_video_generation,
                job_id=job_id,
                task_ids=task_ids,
                segment_durations=segment_durations,
                db=db
            )
            
            return VideoGenerationResponse(
                job_id=job_id,
                status="CONCATENATING",
                message=f"已创建{len(task_ids)}个分段任务，正在后台处理拼接",
                task_ids=task_ids
            )
        else:
            # 单次生成任务
            task_id = result.get("task_id")
            if task_id:
                # 更新任务记录
                job.status = VideoGenerationStatus.RUNNING
                job.task_ids = [task_id]
                db.commit()
                
                return VideoGenerationResponse(
                    job_id=job_id,
                    status="RUNNING",
                    message="视频生成任务已创建，请使用job_id查询状态",
                    task_ids=[task_id]
                )
            else:
                # 直接返回结果
                if "video_url" in result or "local_path" in result:
                    job.status = VideoGenerationStatus.SUCCEEDED
                    job.local_path = result.get("local_path") or result.get("video_url")
                    job.completed_at = datetime.utcnow()
                    db.commit()
                    
                    return VideoGenerationResponse(
                        job_id=job_id,
                        status="SUCCEEDED",
                        message="视频生成成功"
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="视频生成服务返回格式异常"
                    )
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[视频生成] 发生未捕获的异常: {str(e)}")
        print(f"[视频生成] 异常堆栈: {error_trace}")
        
        # 更新任务状态为失败
        try:
            job.status = VideoGenerationStatus.FAILED
            job.error_message = str(e)[:500]  # 限制错误信息长度
            db.commit()
        except Exception as db_error:
            print(f"[视频生成] 更新任务状态失败: {db_error}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "视频生成失败",
                "message": str(e),
                "type": type(e).__name__
            }
        )


@router.get("/job/{job_id}")
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    查询视频生成任务状态
    
    返回任务状态、进度、结果等信息
    """
    # 查询任务
    job = db.query(VideoGenerationJob).filter(
        VideoGenerationJob.job_id == job_id,
        VideoGenerationJob.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 如果任务还在运行中（有task_ids），查询最新状态
    if job.status in [VideoGenerationStatus.PENDING, VideoGenerationStatus.RUNNING, VideoGenerationStatus.CONCATENATING]:
        if job.task_ids and job.engine == "aliyun":
            # 查询所有子任务的状态
            all_succeeded = True
            all_failed = True
            latest_status = None
            
            for task_id in job.task_ids:
                status_result = await dashscope_service.get_task_status(task_id)
                task_status = status_result.get("status")
                
                if task_status == "SUCCEEDED":
                    all_failed = False
                    # 更新本地路径（如果还没有）
                    if not job.local_path and status_result.get("local_path"):
                        job.local_path = status_result.get("local_path")
                    # 更新使用量信息
                    if status_result.get("usage"):
                        job.usage = status_result.get("usage")
                elif task_status == "FAILED":
                    all_succeeded = False
                    if not job.error_message:
                        job.error_message = status_result.get("error", "任务执行失败")
                else:
                    all_succeeded = False
                    all_failed = False
                
                latest_status = task_status
            
            # 更新任务状态
            if all_succeeded:
                if job.status == VideoGenerationStatus.CONCATENATING:
                    # 拼接任务可能还在后台处理，不更新状态
                    pass
                else:
                    job.status = VideoGenerationStatus.SUCCEEDED
                    job.completed_at = datetime.utcnow()
            elif all_failed:
                job.status = VideoGenerationStatus.FAILED
            
            db.commit()
    
    # 构建响应
    response = {
        "job_id": job.job_id,
        "status": job.status.value,
        "engine": job.engine,
        "mode": job.mode,
        "prompt": job.prompt,
        "duration": job.duration,
        "resolution": job.resolution,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
    }
    
    # 添加结果信息
    if job.status == VideoGenerationStatus.SUCCEEDED:
        if job.local_path:
            # 确保路径存在
            if os.path.exists(job.local_path):
                # 生成访问URL（相对路径，前端需要拼接base URL）
                filename = os.path.basename(job.local_path)
                response["video_url"] = f"/media/videos/{filename}"
                response["local_path"] = job.local_path
                response["absolute_path"] = os.path.abspath(job.local_path)
                response["file_size"] = os.path.getsize(job.local_path)
            else:
                response["warning"] = f"视频文件不存在: {job.local_path}"
        if job.usage:
            response["usage"] = job.usage
    
    if job.status == VideoGenerationStatus.FAILED:
        response["error"] = job.error_message
    
    if job.task_ids:
        response["task_ids"] = job.task_ids
    
    return response


@router.get("/jobs")
async def list_jobs(
    project_id: Optional[int] = None,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    列出用户的视频生成任务
    """
    query = db.query(VideoGenerationJob).filter(
        VideoGenerationJob.user_id == current_user.id
    )
    
    if project_id:
        query = query.filter(VideoGenerationJob.project_id == project_id)
    
    jobs = query.order_by(VideoGenerationJob.created_at.desc()).offset(offset).limit(limit).all()
    total = query.count()
    
    return {
        "total": total,
        "jobs": [
            {
                "job_id": job.job_id,
                "status": job.status.value,
                "engine": job.engine,
                "mode": job.mode,
                "prompt": job.prompt[:100] + "..." if len(job.prompt) > 100 else job.prompt,
                "duration": job.duration,
                "resolution": job.resolution,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            }
            for job in jobs
        ]
    }

