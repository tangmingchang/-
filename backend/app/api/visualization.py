"""
可视化反馈API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.services.visualization_service import visualization_service

router = APIRouter()

class RadarChartRequest(BaseModel):
    """雷达图请求"""
    categories: List[str]
    values: List[float]
    title: str = "雷达图"

class HeatmapRequest(BaseModel):
    """热力图请求"""
    data_matrix: List[List[float]]
    x_labels: List[str]
    y_labels: List[str]
    title: str = "热力图"

class TimelineRequest(BaseModel):
    """时间线图表请求"""
    time_points: List[str]
    values: List[float]
    title: str = "时间线图表"
    y_label: str = "数值"

class ComparisonRequest(BaseModel):
    """对比图表请求"""
    categories: List[str]
    values_a: List[float]
    values_b: List[float]
    label_a: str = "版本A"
    label_b: str = "版本B"
    title: str = "对比图表"
    chart_type: str = "bar"  # bar or line

class TextDiffRequest(BaseModel):
    """文本差异对比请求"""
    text_a: str
    text_b: str
    title: str = "文本差异对比"

@router.post("/radar")
async def generate_radar_chart(
    request: RadarChartRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    生成雷达图
    """
    try:
        chart_data = visualization_service.generate_radar_chart(
            request.categories,
            request.values,
            request.title
        )
        
        return {
            "success": True,
            "chart_data": chart_data,
            "format": "base64_png"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"生成雷达图失败: {str(e)}"
        )

@router.post("/heatmap")
async def generate_heatmap(
    request: HeatmapRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    生成热力图
    """
    try:
        chart_data = visualization_service.generate_heatmap(
            request.data_matrix,
            request.x_labels,
            request.y_labels,
            request.title
        )
        
        return {
            "success": True,
            "chart_data": chart_data,
            "format": "base64_png"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"生成热力图失败: {str(e)}"
        )

@router.post("/timeline")
async def generate_timeline_chart(
    request: TimelineRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    生成时间线图表
    """
    try:
        chart_data = visualization_service.generate_timeline_chart(
            request.time_points,
            request.values,
            request.title,
            request.y_label
        )
        
        return {
            "success": True,
            "chart_data": chart_data,
            "format": "base64_png"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"生成时间线图表失败: {str(e)}"
        )

@router.post("/comparison")
async def generate_comparison_chart(
    request: ComparisonRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    生成对比图表
    """
    try:
        chart_data = visualization_service.generate_comparison_chart(
            request.categories,
            request.values_a,
            request.values_b,
            request.label_a,
            request.label_b,
            request.title,
            request.chart_type
        )
        
        return {
            "success": True,
            "chart_data": chart_data,
            "format": "base64_png"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"生成对比图表失败: {str(e)}"
        )

@router.post("/text-diff")
async def generate_text_diff(
    request: TextDiffRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    生成文本差异可视化
    """
    try:
        diff_result = visualization_service.generate_text_diff_visualization(
            request.text_a,
            request.text_b,
            request.title
        )
        
        return {
            "success": True,
            "diff": diff_result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"生成文本差异可视化失败: {str(e)}"
        )

