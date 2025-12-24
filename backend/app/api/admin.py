"""
管理员API - 用户和课程管理
仅管理员可访问
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.core.database import get_db
from app.core.security import get_current_active_user, require_role
from app.models.user import User, UserRole
from app.models.course import Course

router = APIRouter(prefix="/api/admin", tags=["管理员"])

class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    institution: Optional[str]
    created_at: Optional[str]
    
    class Config:
        from_attributes = True

class UserUpdateRequest(BaseModel):
    """用户更新请求"""
    is_active: Optional[bool] = None
    role: Optional[str] = None

@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """获取所有用户列表（仅管理员）"""
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "is_active": user.is_active,
            "institution": user.institution,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
        for user in users
    ]

@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user_update: UserUpdateRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """更新用户信息（仅管理员）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
    
    if user_update.role is not None:
        try:
            user.role = UserRole(user_update.role)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的角色")
    
    db.commit()
    db.refresh(user)
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.value,
        "is_active": user.is_active,
        "institution": user.institution,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """删除用户（仅管理员）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 不能删除自己
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除自己的账户")
    
    db.delete(user)
    db.commit()
    
    return {"message": "用户已删除"}

@router.get("/courses", response_model=List[dict])
async def get_all_courses(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """获取所有课程（仅管理员）"""
    courses = db.query(Course).order_by(Course.created_at.desc()).all()
    return [
        {
            "id": course.id,
            "name": course.name,
            "description": course.description,
            "teacher_id": course.teacher_id,
            "created_at": course.created_at.isoformat() if course.created_at else None
        }
        for course in courses
    ]


