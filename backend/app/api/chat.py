"""
智能对话API
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import uuid
import json
from datetime import datetime
from app.services.ai_service import ai_service
from app.models.chat import Conversation, Message
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User

router = APIRouter()

class ChatMessage(BaseModel):
    """聊天消息模型"""
    role: str
    content: str
    conversation_id: Optional[str] = None

class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str
    conversation_id: Optional[str] = None
    stream: bool = False

class ChatResponse(BaseModel):
    """聊天响应模型"""
    conversation_id: str
    message: str
    role: str
    timestamp: str

# WebSocket连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

manager = ConnectionManager()

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """普通聊天接口"""
    try:
        # 获取或创建会话
        conversation_id = request.conversation_id or str(uuid.uuid4())
        conversation = db.query(Conversation).filter(
            Conversation.session_id == conversation_id
        ).first()
        
        if not conversation:
            conversation = Conversation(
                session_id=conversation_id,
                title=request.message[:50]  # 使用第一条消息作为标题
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
        
        # 保存用户消息
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=request.message
        )
        db.add(user_message)
        
        # 获取对话历史
        history = db.query(Message).filter(
            Message.conversation_id == conversation.id
        ).order_by(Message.created_at).all()
        
        # 格式化消息
        messages = []
        for msg in history:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # 添加当前用户消息
        messages.append({
            "role": "user",
            "content": request.message
        })
        
        # 调用AI服务
        formatted_messages = ai_service.format_messages(messages)
        response = await ai_service.chat_completion(formatted_messages)
        
        # 获取AI回复
        if hasattr(response, 'choices') and len(response.choices) > 0:
            ai_content = response.choices[0].message.content
        else:
            ai_content = str(response)
        
        # 保存AI回复
        ai_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=ai_content
        )
        db.add(ai_message)
        db.commit()
        
        return ChatResponse(
            conversation_id=conversation_id,
            message=ai_content,
            role="assistant",
            timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/chat/ws")
async def websocket_chat(websocket: WebSocket):
    """WebSocket聊天接口（WebSocket不支持Depends，需要手动验证token）"""
    await manager.connect(websocket)
    conversation_id = str(uuid.uuid4())
    from app.core.database import SessionLocal
    db = SessionLocal()
    
    try:
        # 创建新会话
        conversation = Conversation(
            session_id=conversation_id,
            title="新对话"
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        
        # 发送会话ID
        await websocket.send_text(json.dumps({
            "type": "session",
            "conversation_id": conversation_id
        }))
        
        messages = []
        
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            user_message = message_data.get("message", "")
            
            if not user_message:
                continue
            
            # 保存用户消息
            user_msg = Message(
                conversation_id=conversation.id,
                role="user",
                content=user_message
            )
            db.add(user_msg)
            db.commit()
            
            # 添加用户消息到历史
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            # 格式化消息
            formatted_messages = ai_service.format_messages(messages)
            
            # 流式响应
            await websocket.send_text(json.dumps({
                "type": "start",
                "role": "assistant"
            }))
            
            ai_content = ""
            async for chunk in ai_service.stream_chat_completion(formatted_messages):
                ai_content += chunk
                await websocket.send_text(json.dumps({
                    "type": "chunk",
                    "content": chunk
                }))
            
            # 保存AI回复
            ai_msg = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=ai_content
            )
            db.add(ai_msg)
            db.commit()
            
            # 添加AI消息到历史
            messages.append({
                "role": "assistant",
                "content": ai_content
            })
            
            await websocket.send_text(json.dumps({
                "type": "end"
            }))
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": str(e)
        }))
    finally:
        db.close()

@router.get("/conversations")
async def get_conversations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取所有对话"""
    conversations = db.query(Conversation).order_by(
        Conversation.created_at.desc()
    ).limit(50).all()
    
    return [
        {
            "id": conv.id,  # 返回数据库ID，而不是session_id
            "session_id": conv.session_id,
            "title": conv.title or "未命名对话",
            "created_at": conv.created_at.isoformat() if conv.created_at else None
        }
        for conv in conversations
    ]

@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取对话消息"""
    # 支持通过ID或session_id查询
    try:
        conv_id = int(conversation_id)
        conversation = db.query(Conversation).filter(
            Conversation.id == conv_id
        ).first()
    except ValueError:
        # 如果不是数字，按session_id查询
        conversation = db.query(Conversation).filter(
            Conversation.session_id == conversation_id
        ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    messages = db.query(Message).filter(
        Message.conversation_id == conversation.id
    ).order_by(Message.created_at).all()
    
    return [
        {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "created_at": msg.created_at.isoformat() if msg.created_at else None
        }
        for msg in messages
    ]

