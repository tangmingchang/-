# 影视制作教育智能体平台

一个基于FastAPI和React的影视制作教育平台，提供智能对话、知识库管理、课程学习、项目创作等功能。

## 技术栈

### 后端
- FastAPI
- SQLAlchemy (SQLite)
- Python 3.11+

### 前端
- React 18
- TypeScript
- Vite
- Tailwind CSS

## 快速开始

### 后端启动

```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
python main.py
```

后端将在 `http://localhost:8000` 启动，API文档：`http://localhost:8000/api/docs`

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

前端将在 `http://localhost:5173` 启动

## 项目结构

```
python-znt/
├── backend/          # 后端代码
│   ├── app/          # 应用核心
│   ├── main.py       # 入口文件
│   └── requirements.txt
└── frontend/         # 前端代码
    ├── src/          # 源代码
    └── package.json
```

## 主要功能

- 用户认证与权限管理
- 智能对话系统
- 知识库管理
- 课程学习
- 项目创作与管理
- 剧本分析
- 视频生成
- AI辅助功能

## 环境配置

后端配置在 `backend/app/core/config.py`，可通过环境变量或 `.env` 文件配置。

前端开发环境自动通过Vite代理访问后端，无需额外配置。

## 数据库

默认使用SQLite数据库 `film_education.db`，首次启动会自动创建表结构。

## 许可证

本项目用于教育目的。
