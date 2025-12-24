"""
剧本分析与结构理解API
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.services.script_analysis_service import script_analysis_service
import aiofiles

router = APIRouter()

class ScriptAnalysisRequest(BaseModel):
    """剧本分析请求"""
    script_content: str
    analysis_type: Optional[str] = "full"  # full, structure_only, deep_analysis_only

class ScriptNodeRequest(BaseModel):
    """剧本节点生成请求"""
    character: str  # 人物
    location: str  # 地点
    action: str  # 事件/动作
    emotion: Optional[str] = None  # 情绪
    time: Optional[str] = None  # 时间
    additional_context: Optional[str] = None  # 额外上下文

class ScriptAnalysisResponse(BaseModel):
    """剧本分析响应"""
    success: bool
    parsed_structure: dict
    deep_analysis: dict
    statistics: dict
    message: Optional[str] = None

@router.post("/analyze", response_model=ScriptAnalysisResponse)
async def analyze_script(
    request: ScriptAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    分析剧本结构
    使用ScreenPy解析剧本，结合LLM进行深度分析
    """
    try:
        result = await script_analysis_service.analyze_script(request.script_content)
        
        return ScriptAnalysisResponse(
            success=True,
            parsed_structure=result.get("parsed_structure", {}),
            deep_analysis=result.get("deep_analysis", {}),
            statistics=result.get("statistics", {}),
            message="剧本分析完成"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"剧本分析失败: {str(e)}"
        )

@router.post("/analyze/upload")
async def analyze_script_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    上传剧本文件进行分析
    支持.txt, .docx等格式
    """
    # 检查文件类型
    allowed_extensions = ['.txt', '.docx', '.doc']
    file_ext = '.' + file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型。支持的类型: {', '.join(allowed_extensions)}"
        )
    
    try:
        # 读取文件内容
        content = await file.read()
        
        # 如果是文本文件，直接解码
        if file_ext == '.txt':
            script_content = content.decode('utf-8')
        else:
            # 对于docx等格式，需要使用相应库解析
            # 这里简化处理
            script_content = content.decode('utf-8', errors='ignore')
        
        # 分析剧本
        result = await script_analysis_service.analyze_script(script_content)
        
        return {
            "success": True,
            "filename": file.filename,
            "result": result
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"文件处理失败: {str(e)}"
        )

@router.post("/generate-node")
async def generate_script_node(
    request: ScriptNodeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    根据标签生成剧本节点
    将人物、地点、事件等信息组合成标准剧本格式的场景
    """
    try:
        # 构建场景标题
        location_type = "INT." if any(keyword in request.location.lower() for keyword in ['内', '室', '房间', '办公室', '家']) else "EXT."
        scene_title = f"{location_type} {request.location} - {request.time or '白天'}"
        
        # 构建场景描述
        scene_description = f"{request.character}在{request.location}"
        if request.emotion:
            scene_description += f"，情绪{request.emotion}"
        scene_description += f"。{request.action}"
        
        if request.additional_context:
            scene_description += f"\n{request.additional_context}"
        
        # 生成标准剧本格式
        script_node = f"""
{scene_title}

{scene_description}

{request.character.upper()}
（{request.emotion or '平静'}）
{request.action}
"""
        
        return {
            "success": True,
            "script_node": script_node.strip(),
            "scene_title": scene_title,
            "character": request.character,
            "location": request.location,
            "action": request.action,
            "emotion": request.emotion,
            "time": request.time
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"生成剧本节点失败: {str(e)}"
        )

@router.get("/tags")
async def get_script_tags():
    """
    获取可用的标签选项
    返回人物、地点、事件、情绪等标签列表
    """
    return {
        "characters": [
            "年轻的创业者", "经验丰富的导演", "迷茫的学生", "退休的老人",
            "忙碌的医生", "艺术家", "程序员", "教师", "记者", "警察",
            "商人", "科学家", "音乐家", "运动员", "厨师", "律师"
        ],
        "locations": [
            "咖啡厅", "办公室", "学校教室", "医院", "公园", "图书馆",
            "电影院", "餐厅", "家", "街道", "机场", "火车站",
            "海边", "山顶", "森林", "城市广场", "博物馆", "工作室",
            "录音棚", "摄影棚", "废弃工厂", "老房子", "现代公寓", "乡村小屋"
        ],
        "actions": [
            "思考人生", "等待某人", "阅读文件", "打电话", "写日记",
            "观看窗外", "整理物品", "准备出发", "回忆过去", "规划未来",
            "做出决定", "面对困难", "庆祝成功", "处理危机", "寻找答案",
            "告别朋友", "迎接挑战", "分享秘密", "解决问题", "创造奇迹"
        ],
        "emotions": [
            "平静", "焦虑", "兴奋", "悲伤", "愤怒", "快乐",
            "困惑", "坚定", "犹豫", "自信", "恐惧", "希望",
            "失望", "惊喜", "怀念", "期待", "紧张", "放松"
        ],
        "times": [
            "清晨", "上午", "中午", "下午", "傍晚", "夜晚",
            "深夜", "黎明", "黄昏", "午夜"
        ]
    }

@router.get("/characters/{script_id}")
async def get_script_characters(
    script_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    获取剧本中的角色列表
    """
    # 这里应该从数据库查询剧本
    # 简化实现
    return {
        "script_id": script_id,
        "characters": []
    }

