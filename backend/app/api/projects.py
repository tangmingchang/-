"""
项目管理API（创作空间）
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import os
import uuid
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.core.config import settings
from app.models.user import User
from app.models.project import Project, ProjectStatus, Script, Storyboard, MediaAsset
from app.models.course import Course, CourseEnrollment
from app.services.dashscope_service import dashscope_service

router = APIRouter()

class ProjectCreate(BaseModel):
    """创建项目模型"""
    name: str
    description: Optional[str] = None
    course_id: int

class ProjectResponse(BaseModel):
    """项目响应模型"""
    id: int
    name: str
    description: Optional[str]
    course_id: int
    owner_id: int
    status: ProjectStatus
    created_at: datetime
    
    class Config:
        from_attributes = True

class ScriptCreate(BaseModel):
    """创建剧本模型"""
    title: Optional[str] = None
    content: str

class ScriptResponse(BaseModel):
    """剧本响应模型"""
    id: int
    project_id: int
    title: Optional[str]
    content: str
    analysis_result: Optional[dict]
    created_at: datetime
    
    class Config:
        from_attributes = True

class StoryboardCreate(BaseModel):
    """创建分镜模型"""
    scene_number: Optional[int] = None
    description: str
    shot_type: Optional[str] = None
    camera_angle: Optional[str] = None
    camera_movement: Optional[str] = None
    notes: Optional[str] = None
    order: int = 0

class StoryboardResponse(BaseModel):
    """分镜响应模型"""
    id: int
    project_id: int
    scene_number: Optional[int]
    description: str
    image_path: Optional[str]
    shot_type: Optional[str]
    camera_angle: Optional[str]
    camera_movement: Optional[str]
    notes: Optional[str]
    order: int
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建项目"""
    # 检查课程是否存在且用户有权限
    course = db.query(Course).filter(Course.id == project_data.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    
    # 学生只能在自己的课程中创建项目
    if current_user.role.value == "student":
        enrollment = db.query(CourseEnrollment).filter(
            CourseEnrollment.course_id == project_data.course_id,
            CourseEnrollment.student_id == current_user.id
        ).first()
        if not enrollment:
            raise HTTPException(status_code=403, detail="无权在此课程中创建项目")
    
    project = Project(
        name=project_data.name,
        description=project_data.description,
        course_id=project_data.course_id,
        owner_id=current_user.id
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    course_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取项目列表"""
    query = db.query(Project)
    
    # 学生只能看到自己的项目
    if current_user.role.value == "student":
        query = query.filter(Project.owner_id == current_user.id)
    
    if course_id:
        query = query.filter(Project.course_id == course_id)
    
    projects = query.all()
    return projects

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取项目详情"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 权限检查
    if current_user.role.value == "student" and project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此项目")
    
    return project

@router.post("/{project_id}/scripts", response_model=ScriptResponse, status_code=status.HTTP_201_CREATED)
async def create_script(
    project_id: int,
    script_data: ScriptCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建剧本"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 权限检查
    if current_user.role.value == "student" and project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此项目")
    
    script = Script(
        project_id=project_id,
        title=script_data.title,
        content=script_data.content
    )
    db.add(script)
    db.commit()
    db.refresh(script)
    return script

@router.get("/{project_id}/scripts", response_model=List[ScriptResponse])
async def list_scripts(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取项目剧本列表"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 权限检查
    if current_user.role.value == "student" and project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此项目")
    
    scripts = db.query(Script).filter(Script.project_id == project_id).all()
    return scripts

@router.put("/{project_id}/scripts/{script_id}", response_model=ScriptResponse)
async def update_script(
    project_id: int,
    script_id: int,
    script_data: ScriptCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新剧本"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 权限检查
    if current_user.role.value == "student" and project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此项目")
    
    script = db.query(Script).filter(
        Script.id == script_id,
        Script.project_id == project_id
    ).first()
    if not script:
        raise HTTPException(status_code=404, detail="剧本不存在")
    
    script.title = script_data.title
    script.content = script_data.content
    db.commit()
    db.refresh(script)
    return script

@router.delete("/{project_id}/scripts/{script_id}", status_code=status.HTTP_200_OK)
async def delete_script(
    project_id: int,
    script_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除剧本"""
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 权限检查
        if current_user.role.value == "student" and project.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权操作此项目")
        
        script = db.query(Script).filter(
            Script.id == script_id,
            Script.project_id == project_id
        ).first()
        if not script:
            raise HTTPException(status_code=404, detail="剧本不存在")
        
        db.delete(script)
        db.commit()
        return {"message": "剧本已删除", "status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除剧本时发生错误: {str(e)}")

# 注意：更具体的路由（带storyboard_id的）要放在更通用的路由之前
@router.put("/{project_id}/storyboards/{storyboard_id}", response_model=StoryboardResponse)
async def update_storyboard(
    project_id: int,
    storyboard_id: int,
    storyboard_data: StoryboardCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新分镜"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 权限检查
    if current_user.role.value == "student" and project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此项目")
    
    storyboard = db.query(Storyboard).filter(
        Storyboard.id == storyboard_id,
        Storyboard.project_id == project_id
    ).first()
    if not storyboard:
        raise HTTPException(status_code=404, detail="分镜不存在")
    
    storyboard.scene_number = storyboard_data.scene_number
    storyboard.description = storyboard_data.description
    storyboard.shot_type = storyboard_data.shot_type
    storyboard.camera_angle = storyboard_data.camera_angle
    storyboard.camera_movement = storyboard_data.camera_movement
    storyboard.notes = storyboard_data.notes
    storyboard.order = storyboard_data.order
    db.commit()
    db.refresh(storyboard)
    return storyboard

@router.delete("/{project_id}/storyboards/{storyboard_id}", status_code=status.HTTP_200_OK)
async def delete_storyboard(
    project_id: int,
    storyboard_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除分镜"""
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 权限检查
        if current_user.role.value == "student" and project.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权操作此项目")
        
        storyboard = db.query(Storyboard).filter(
            Storyboard.id == storyboard_id,
            Storyboard.project_id == project_id
        ).first()
        if not storyboard:
            raise HTTPException(status_code=404, detail="分镜不存在")
        
        db.delete(storyboard)
        db.commit()
        return {"message": "分镜已删除", "status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除分镜时发生错误: {str(e)}")

@router.post("/{project_id}/storyboards", response_model=StoryboardResponse, status_code=status.HTTP_201_CREATED)
async def create_storyboard(
    project_id: int,
    storyboard_data: StoryboardCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建分镜"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 权限检查
    if current_user.role.value == "student" and project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此项目")
    
    storyboard = Storyboard(
        project_id=project_id,
        scene_number=storyboard_data.scene_number,
        description=storyboard_data.description,
        shot_type=storyboard_data.shot_type,
        camera_angle=storyboard_data.camera_angle,
        camera_movement=storyboard_data.camera_movement,
        notes=storyboard_data.notes,
        order=storyboard_data.order
    )
    db.add(storyboard)
    db.commit()
    db.refresh(storyboard)
    return storyboard

@router.get("/{project_id}/storyboards", response_model=List[StoryboardResponse])
async def list_storyboards(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取项目分镜列表"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 权限检查
    if current_user.role.value == "student" and project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此项目")
    
    storyboards = db.query(Storyboard).filter(
        Storyboard.project_id == project_id
    ).order_by(Storyboard.order).all()
    return storyboards

class GenerateImageRequest(BaseModel):
    """生成图片请求"""
    prompt: Optional[str] = None

@router.post("/{project_id}/storyboards/{storyboard_id}/generate-image")
async def generate_storyboard_image(
    project_id: int,
    storyboard_id: int,
    request: GenerateImageRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """为分镜生成图片（文生图）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 权限检查
    if current_user.role.value == "student" and project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此项目")
    
    storyboard = db.query(Storyboard).filter(
        Storyboard.id == storyboard_id,
        Storyboard.project_id == project_id
    ).first()
    if not storyboard:
        raise HTTPException(status_code=404, detail="分镜不存在")
    
    # 如果没有提供prompt，使用分镜描述
    prompt = request.prompt or storyboard.description or "分镜画面"
    
    try:
        # 调用DashScope文生图API
        # 尝试多个模型名称（根据DashScope API文档，模型名称可能有不同格式）
        models_to_try = [
            "wan2.6-t2i",  # 通义万相2.6-文生图
            "wan2.5-t2i-preview",  # 通义万相2.5-文生图-Preview
            "wan2.2-t2i-plus",  # 通义万相2.2-文生图-Plus
            "wan2.2-t2i-flash",  # 通义万相2.2-文生图-Flash
            "wan2.1-t2i-plus",  # 通义万相2.1-文生图-Plus
            "wanx-v1"  # 旧版本
        ]
        
        result = None
        last_error = None
        
        for model_name in models_to_try:
            try:
                print(f"[分镜文生图] 尝试模型: {model_name}")
                result = await dashscope_service.generate_text_to_image(
                    prompt=prompt,
                    model=model_name,
                    size="1024*1024",
                    n=1
                )
                
                if result.get("success"):
                    print(f"[分镜文生图] 模型 {model_name} 调用成功")
                    break
                else:
                    last_error = result.get("error", "未知错误")
                    print(f"[分镜文生图] 模型 {model_name} 失败: {last_error}")
                    # 如果是模型不存在错误，继续尝试下一个
                    if "Model not exist" in last_error or "模型不存在" in last_error:
                        continue
                    else:
                        # 其他错误，停止尝试
                        break
            except Exception as e:
                last_error = str(e)
                print(f"[分镜文生图] 模型 {model_name} 异常: {e}")
                # 继续尝试下一个模型
                continue
        
        if result and result.get("success") and result.get("images"):
            image_url = result["images"][0]
            
            # 更新分镜的图片路径
            storyboard.image_path = image_url
            db.commit()
            db.refresh(storyboard)
            
            return {
                "success": True,
                "image_url": image_url,
                "message": "图片生成成功"
            }
        else:
            error_msg = result.get("error", "未知错误") if result else (last_error or "所有模型都尝试失败")
            raise HTTPException(status_code=500, detail=f"图片生成失败: {error_msg}")
    
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        db.rollback()
        import traceback
        error_detail = traceback.format_exc()
        print(f"[分镜文生图] 异常详情:\n{error_detail}")
        raise HTTPException(status_code=500, detail=f"生成图片时发生错误: {str(e)}")

@router.post("/{project_id}/media/upload")
async def upload_media(
    project_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """上传媒体文件"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 权限检查
    if current_user.role.value == "student" and project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此项目")
    
    # 确定文件类型和存储路径
    content_type = file.content_type or ""
    if content_type.startswith("image/"):
        asset_type = "image"
        upload_dir = os.path.join(settings.MEDIA_ROOT, "images")
    elif content_type.startswith("video/"):
        asset_type = "video"
        upload_dir = os.path.join(settings.MEDIA_ROOT, "videos")
    elif content_type.startswith("audio/"):
        asset_type = "audio"
        upload_dir = os.path.join(settings.MEDIA_ROOT, "audios")
    else:
        raise HTTPException(status_code=400, detail="不支持的文件类型")
    
    os.makedirs(upload_dir, exist_ok=True)
    
    # 生成唯一文件名
    file_ext = os.path.splitext(file.filename)[1]
    file_name = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(upload_dir, file_name)
    
    # 保存文件
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # 创建媒体资产记录
    media_asset = MediaAsset(
        project_id=project_id,
        name=file.filename,
        asset_type=asset_type,
        file_path=file_path,
        file_size=len(content),
        mime_type=content_type
    )
    db.add(media_asset)
    db.commit()
    db.refresh(media_asset)
    
    return {
        "id": media_asset.id,
        "name": media_asset.name,
        "asset_type": media_asset.asset_type,
        "file_path": media_asset.file_path,
        "file_size": media_asset.file_size
    }











