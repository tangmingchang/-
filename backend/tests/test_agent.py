"""
智能体协同调度层测试
"""
import pytest
from app.services.agent_orchestrator import orchestrator, SceneType

@pytest.mark.asyncio
async def test_script_writing_agent():
    """测试剧本写作智能体"""
    context = {
        "script_content": "第一场：室内，日。主角走进房间。",
        "action": "analyze"
    }
    
    result = await orchestrator.process_scene(
        SceneType.SCRIPT_WRITING,
        context,
        "student"
    )
    
    assert result["success"] is not None
    assert result["scene_type"] == "script_writing"

@pytest.mark.asyncio
async def test_storyboard_design_agent():
    """测试分镜设计智能体"""
    context = {
        "scene_description": "一个年轻人在城市街道上慢跑",
        "action": "generate"
    }
    
    result = await orchestrator.process_scene(
        SceneType.STORYBOARD_DESIGN,
        context,
        "student"
    )
    
    assert result["success"] is not None
    assert result["scene_type"] == "storyboard_design"

@pytest.mark.asyncio
async def test_invalid_scene_type():
    """测试无效场景类型"""
    result = await orchestrator.process_scene(
        "invalid_scene",  # type: ignore
        {},
        "student"
    )
    
    assert "error" in result












