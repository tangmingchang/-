"""
课程管理API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from app.core.database import get_db
from app.core.security import get_current_active_user, require_role
from app.models.user import User, UserRole
from app.models.course import Course, CourseEnrollment, Chapter, CourseResource, ChapterResource

router = APIRouter()

class CourseCreate(BaseModel):
    """创建课程模型"""
    name: str
    description: Optional[str] = None

class CourseResponse(BaseModel):
    """课程响应模型"""
    id: int
    name: str
    description: Optional[str]
    teacher_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ChapterCreate(BaseModel):
    """创建章节模型"""
    title: str
    content: Optional[str] = None
    order: int = 0

class ChapterResponse(BaseModel):
    """章节响应模型"""
    id: int
    course_id: int
    title: str
    content: Optional[str]
    order: int
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.post("/", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    course_data: CourseCreate,
    current_user: User = Depends(require_role(UserRole.TEACHER, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """创建课程（仅教师和管理员）"""
    course = Course(
        name=course_data.name,
        description=course_data.description,
        teacher_id=current_user.id
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course

@router.get("/", response_model=List[CourseResponse])
async def list_courses(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取课程列表"""
    if current_user.role == UserRole.TEACHER:
        # 教师看到自己创建的课程
        courses = db.query(Course).filter(Course.teacher_id == current_user.id).all()
    elif current_user.role == UserRole.ADMIN:
        # 管理员看到所有课程
        courses = db.query(Course).all()
    else:
        # 学生看到已加入的课程
        enrollments = db.query(CourseEnrollment).filter(
            CourseEnrollment.student_id == current_user.id
        ).all()
        course_ids = [e.course_id for e in enrollments]
        courses = db.query(Course).filter(Course.id.in_(course_ids)).all()
    
    return courses

# 注意：更具体的路由必须放在更通用的路由之前
# 例如 /{course_id}/students 必须在 /{course_id} 之前

@router.get("/{course_id}/students")
async def get_course_students(
    course_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取课程的学生列表（仅教师和管理员）"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    
    # 权限检查：只有教师和管理员可以查看学生列表
    if current_user.role == UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="无权访问此资源")
    
    # 如果是教师，检查是否是课程教师
    if current_user.role == UserRole.TEACHER and course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此课程的学生列表")
    
    # 获取所有注册该课程的学生
    enrollments = db.query(CourseEnrollment).filter(
        CourseEnrollment.course_id == course_id
    ).all()
    
    students = []
    for enrollment in enrollments:
        student = db.query(User).filter(User.id == enrollment.student_id).first()
        if student:
            students.append({
                "id": student.id,
                "username": student.username,
                "full_name": student.full_name,
                "email": student.email,
                "avatar_url": student.avatar_url,
                "enrolled_at": enrollment.enrolled_at.isoformat() if enrollment.enrolled_at else None
            })
    
    return students

@router.get("/{course_id}/student-projects")
async def get_course_student_projects(
    course_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取课程中所有学生的项目（仅教师和管理员）"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    
    # 权限检查：只有教师和管理员可以查看学生项目
    if current_user.role == UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="无权访问此资源")
    
    # 如果是教师，检查是否是课程教师
    if current_user.role == UserRole.TEACHER and course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此课程的学生项目")
    
    # 获取该课程的所有项目
    from app.models.project import Project
    projects = db.query(Project).filter(Project.course_id == course_id).all()
    
    # 获取项目所有者信息
    result = []
    for project in projects:
        owner = db.query(User).filter(User.id == project.owner_id).first()
        if owner:
            result.append({
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "status": project.status,
                "created_at": project.created_at.isoformat() if project.created_at else None,
                "owner": {
                    "id": owner.id,
                    "username": owner.username,
                    "full_name": owner.full_name,
                    "avatar_url": owner.avatar_url
                }
            })
    
    return result

@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取课程详情"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    
    # 权限检查：教师只能看自己的课程，学生只能看已加入的课程
    if current_user.role == UserRole.STUDENT:
        enrollment = db.query(CourseEnrollment).filter(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.student_id == current_user.id
        ).first()
        if not enrollment:
            raise HTTPException(status_code=403, detail="无权访问此课程")
    elif current_user.role == UserRole.TEACHER and course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此课程")
    
    return course

@router.post("/{course_id}/enroll", status_code=status.HTTP_201_CREATED)
async def enroll_course(
    course_id: int,
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: Session = Depends(get_db)
):
    """学生加入课程"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    
    # 检查是否已加入
    existing = db.query(CourseEnrollment).filter(
        CourseEnrollment.course_id == course_id,
        CourseEnrollment.student_id == current_user.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="已加入此课程")
    
    enrollment = CourseEnrollment(
        course_id=course_id,
        student_id=current_user.id
    )
    db.add(enrollment)
    db.commit()
    
    return {"message": "成功加入课程"}

@router.post("/{course_id}/chapters", response_model=ChapterResponse, status_code=status.HTTP_201_CREATED)
async def create_chapter(
    course_id: int,
    chapter_data: ChapterCreate,
    current_user: User = Depends(require_role(UserRole.TEACHER, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """创建章节（仅教师）"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    
    if course.teacher_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="无权操作此课程")
    
    chapter = Chapter(
        course_id=course_id,
        title=chapter_data.title,
        content=chapter_data.content,
        order=chapter_data.order
    )
    db.add(chapter)
    db.commit()
    db.refresh(chapter)
    return chapter

@router.get("/{course_id}/chapters", response_model=List[ChapterResponse])
async def list_chapters(
    course_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取课程章节列表"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    
    # 权限检查
    if current_user.role == UserRole.STUDENT:
        enrollment = db.query(CourseEnrollment).filter(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.student_id == current_user.id
        ).first()
        if not enrollment:
            raise HTTPException(status_code=403, detail="无权访问此课程")
    
    chapters = db.query(Chapter).filter(Chapter.course_id == course_id).order_by(Chapter.order).all()
    return chapters

class CourseResourceResponse(BaseModel):
    """课程资源响应模型"""
    id: int
    course_id: int
    title: str
    resource_type: Optional[str]
    file_path: Optional[str]
    description: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.get("/{course_id}/resources", response_model=List[CourseResourceResponse])
async def list_course_resources(
    course_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取课程资源列表"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    
    # 权限检查
    if current_user.role == UserRole.STUDENT:
        enrollment = db.query(CourseEnrollment).filter(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.student_id == current_user.id
        ).first()
        if not enrollment:
            raise HTTPException(status_code=403, detail="无权访问此课程")
    
    resources = db.query(CourseResource).filter(CourseResource.course_id == course_id).all()
    return resources

