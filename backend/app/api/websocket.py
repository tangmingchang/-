"""
WebSocket实时通信API
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List
import json
from app.core.security import verify_token

router = APIRouter()

class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str, room: str = "default"):
        """建立连接"""
        await websocket.accept()
        if room not in self.active_connections:
            self.active_connections[room] = []
        self.active_connections[room].append(websocket)
        # 存储用户ID到websocket的映射
        websocket.user_id = user_id
    
    def disconnect(self, websocket: WebSocket, room: str = "default"):
        """断开连接"""
        if room in self.active_connections:
            if websocket in self.active_connections[room]:
                self.active_connections[room].remove(websocket)
            if not self.active_connections[room]:
                del self.active_connections[room]
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """发送个人消息"""
        await websocket.send_json(message)
    
    async def broadcast(self, message: dict, room: str = "default", exclude: WebSocket = None):
        """广播消息到房间内所有连接"""
        if room in self.active_connections:
            for connection in self.active_connections[room]:
                if connection != exclude:
                    try:
                        await connection.send_json(message)
                    except:
                        # 连接已断开，移除
                        self.active_connections[room].remove(connection)

manager = ConnectionManager()

@router.websocket("/ws/{room}")
async def websocket_endpoint(websocket: WebSocket, room: str, token: str = None):
    """WebSocket端点"""
    # 验证token（简化处理，实际应该从query参数或header获取）
    user_id = "anonymous"
    if token:
        payload = verify_token(token)
        if payload:
            user_id = payload.get("sub", "anonymous")
    
    await manager.connect(websocket, user_id, room)
    
    try:
        # 发送欢迎消息
        await manager.send_personal_message({
            "type": "connected",
            "message": f"已连接到房间: {room}",
            "user_id": user_id
        }, websocket)
        
        # 通知房间内其他用户
        await manager.broadcast({
            "type": "user_joined",
            "user_id": user_id,
            "message": f"用户 {user_id} 加入了房间"
        }, room, exclude=websocket)
        
        while True:
            # 接收消息
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "ping":
                # 心跳检测
                await manager.send_personal_message({
                    "type": "pong"
                }, websocket)
            
            elif message_type == "message":
                # 普通消息，广播给房间内所有用户
                await manager.broadcast({
                    "type": "message",
                    "user_id": user_id,
                    "content": data.get("content", ""),
                    "timestamp": data.get("timestamp")
                }, room)
            
            elif message_type == "task_update":
                # 任务状态更新
                await manager.broadcast({
                    "type": "task_update",
                    "task_id": data.get("task_id"),
                    "status": data.get("status"),
                    "progress": data.get("progress"),
                    "result": data.get("result")
                }, room)
            
            elif message_type == "collaboration":
                # 协作消息（如实时编辑）
                await manager.broadcast({
                    "type": "collaboration",
                    "action": data.get("action"),
                    "data": data.get("data"),
                    "user_id": user_id
                }, room, exclude=websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, room)
        # 通知房间内其他用户
        await manager.broadcast({
            "type": "user_left",
            "user_id": user_id,
            "message": f"用户 {user_id} 离开了房间"
        }, room)

