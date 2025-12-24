"""
认证API
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import timedelta
from app.core.database import get_db
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_active_user,
    require_role
)
from app.core.config import settings
from app.models.user import User, UserRole

router = APIRouter()

class UserRegister(BaseModel):
    """用户注册模型"""
    username: str
    email: EmailStr
    password: str
    full_name: str
    role: UserRole = UserRole.STUDENT
    institution: Optional[str] = None

class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    username: str
    email: str
    full_name: str
    avatar_url: Optional[str] = None
    role: str  # 改为字符串类型，避免枚举序列化问题
    is_active: bool
    institution: Optional[str] = None
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    """令牌响应模型"""
    access_token: str
    token_type: str

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户名是否已存在
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否已存在
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )
    
    # 创建新用户
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role=user_data.role,
        institution=user_data.institution
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # 注册成功后自动登录，返回token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.username, "role": db_user.role.value},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """用户登录"""
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    password_valid = verify_password(form_data.password, user.hashed_password)
    
    if not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户已被禁用"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户信息"""
    print(f"[用户信息] 获取用户信息: username={current_user.username}, role={current_user.role.value}")
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name or "",
        "avatar_url": current_user.avatar_url,
        "role": current_user.role.value,  # 转换为字符串值
        "is_active": current_user.is_active,
        "institution": current_user.institution
    }

class UserUpdate(BaseModel):
    """用户信息更新模型"""
    username: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    institution: Optional[str] = None

@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新用户个人信息"""
    # 更新用户名（如果提供）
    if user_update.username is not None:
        # 检查用户名是否已被其他用户使用
        existing_user = db.query(User).filter(
            User.username == user_update.username,
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="该用户名已被使用"
            )
        current_user.username = user_update.username
    
    # 注意：full_name 不允许修改，所以这里不处理
    # if user_update.full_name is not None:
    #     current_user.full_name = user_update.full_name
    
    if user_update.avatar_url is not None:
        current_user.avatar_url = user_update.avatar_url
    if user_update.institution is not None:
        current_user.institution = user_update.institution
    
    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """上传用户头像"""
    import os
    import uuid
    from app.core.config import settings
    
    # 检查文件类型
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="只支持图片文件"
        )
    
    # 创建头像存储目录
    avatar_dir = os.path.join(settings.MEDIA_ROOT, "avatars")
    os.makedirs(avatar_dir, exist_ok=True)
    
    # 生成唯一文件名
    file_ext = os.path.splitext(file.filename)[1] or ".jpg"
    file_name = f"{current_user.id}_{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(avatar_dir, file_name)
    
    # 保存文件
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    # 更新用户头像URL（相对路径）
    avatar_url = f"/media/avatars/{file_name}"
    current_user.avatar_url = avatar_url
    db.commit()
    db.refresh(current_user)
    
    return {
        "avatar_url": avatar_url,
        "message": "头像上传成功"
    }

@router.get("/students")
async def get_teacher_students(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取教师管理的所有学生（不按课程）"""
    # 权限检查：只有教师和管理员可以查看学生列表
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="无权访问此资源")
    
    # 如果是教师，获取所有学生（不区分课程）
    # 如果是管理员，获取所有学生
    if current_user.role == UserRole.TEACHER:
        # 获取所有学生
        students = db.query(User).filter(User.role == UserRole.STUDENT).all()
    else:
        # 管理员获取所有学生
        students = db.query(User).filter(User.role == UserRole.STUDENT).all()
    
    result = []
    for student in students:
        result.append({
            "id": student.id,
            "username": student.username,
            "full_name": student.full_name,
            "email": student.email,
            "avatar_url": student.avatar_url,
            "institution": student.institution
        })
    
    return result

@router.get("/students/{student_id}/projects")
async def get_student_projects(
    student_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取学生的所有项目和媒体资产"""
    # 权限检查：只有教师和管理员可以查看学生项目
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="无权访问此资源")
    
    # 检查学生是否存在
    student = db.query(User).filter(User.id == student_id, User.role == UserRole.STUDENT).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    
    # 获取学生的所有项目
    from app.models.project import Project, MediaAsset
    projects = db.query(Project).filter(Project.owner_id == student_id).all()
    
    result = []
    for project in projects:
        # 获取项目的媒体资产
        media_assets = db.query(MediaAsset).filter(MediaAsset.project_id == project.id).all()
        
        result.append({
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "media_assets": [
                {
                    "id": asset.id,
                    "name": asset.name,
                    "asset_type": asset.asset_type,
                    "file_path": asset.file_path,
                    "file_size": asset.file_size,
                    "mime_type": asset.mime_type,
                    "created_at": asset.created_at.isoformat() if asset.created_at else None
                }
                for asset in media_assets
            ]
        })
    
    return result

