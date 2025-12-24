"""
课程管理API测试
"""
import pytest
from fastapi.testclient import TestClient
from app.core.database import Base, engine, SessionLocal
from app.models.user import User
from app.models.course import Course
from app.core.security import get_password_hash, create_access_token
from main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    """每个测试前重置数据库"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def teacher_user():
    """创建教师用户"""
    db = SessionLocal()
    user = User(
        username="teacher",
        email="teacher@example.com",
        hashed_password=get_password_hash("password"),
        full_name="Teacher",
        role="teacher"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user

@pytest.fixture
def student_user():
    """创建学生用户"""
    db = SessionLocal()
    user = User(
        username="student",
        email="student@example.com",
        hashed_password=get_password_hash("password"),
        full_name="Student",
        role="student"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user

def get_auth_headers(user: User):
    """获取认证头"""
    token = create_access_token({"sub": user.username, "role": user.role})
    return {"Authorization": f"Bearer {token}"}

def test_create_course(teacher_user):
    """测试创建课程"""
    headers = get_auth_headers(teacher_user)
    response = client.post(
        "/api/courses/",
        json={
            "name": "测试课程",
            "description": "这是一门测试课程"
        },
        headers=headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "测试课程"
    assert data["teacher_id"] == teacher_user.id

def test_student_cannot_create_course(student_user):
    """测试学生不能创建课程"""
    headers = get_auth_headers(student_user)
    response = client.post(
        "/api/courses/",
        json={
            "name": "测试课程",
            "description": "这是一门测试课程"
        },
        headers=headers
    )
    assert response.status_code == 403

def test_list_courses(teacher_user):
    """测试获取课程列表"""
    # 先创建课程
    db = SessionLocal()
    course = Course(
        name="测试课程",
        description="测试",
        teacher_id=teacher_user.id
    )
    db.add(course)
    db.commit()
    db.close()
    
    headers = get_auth_headers(teacher_user)
    response = client.get("/api/courses/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "测试课程"












