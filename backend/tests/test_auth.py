"""
认证API测试
"""
import pytest
from fastapi.testclient import TestClient
from app.core.database import Base, engine, SessionLocal
from app.models.user import User
from app.core.security import get_password_hash
from main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    """每个测试前重置数据库"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_user():
    """创建测试用户"""
    db = SessionLocal()
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpass123"),
        full_name="Test User",
        role="student"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user

def test_register_user():
    """测试用户注册"""
    response = client.post("/api/auth/register", json={
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "password123",
        "full_name": "New User",
        "role": "student"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert "id" in data

def test_register_duplicate_username(test_user):
    """测试重复用户名注册"""
    response = client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "another@example.com",
        "password": "password123",
        "full_name": "Another User",
        "role": "student"
    })
    assert response.status_code == 400

def test_login_success(test_user):
    """测试登录成功"""
    response = client.post(
        "/api/auth/login",
        data={
            "username": "testuser",
            "password": "testpass123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(test_user):
    """测试错误密码登录"""
    response = client.post(
        "/api/auth/login",
        data={
            "username": "testuser",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401

def test_get_current_user(test_user):
    """测试获取当前用户信息"""
    # 先登录获取token
    login_response = client.post(
        "/api/auth/login",
        data={
            "username": "testuser",
            "password": "testpass123"
        }
    )
    token = login_response.json()["access_token"]
    
    # 使用token获取用户信息
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"












