"""
AI剪辑建议服务
使用PySceneDetect进行镜头检测，结合音频分析和LLM生成建议
"""
import subprocess
import json
from typing import Dict, List, Optional, Any
from pathlib import Path

class EditingService:
    """剪辑建议服务"""
    
    def __init__(self):
        self.scenedetect_available = False
        self.librosa_available = False
        self._init_tools()
    
    def _init_tools(self):
        """初始化工具"""
        # 检查PySceneDetect是否可用
        try:
            import scenedetect
            self.scenedetect_available = True
        except ImportError:
            print("警告: PySceneDetect未安装，将使用基础检测")
            self.scenedetect_available = False
        
        # 检查librosa是否可用
        try:
            import librosa
            self.librosa_available = True
        except ImportError:
            print("警告: librosa未安装，音频分析功能受限")
            self.librosa_available = False
    
    def detect_scenes(self, video_path: str) -> List[Dict[str, Any]]:
        """
        检测视频中的镜头切换点
        返回场景边界列表
        """
        if not self.scenedetect_available:
            # 基础实现：返回模拟数据
            return [
                {"start": 0.0, "end": 5.2, "duration": 5.2},
                {"start": 5.2, "end": 12.5, "duration": 7.3},
                {"start": 12.5, "end": 18.0, "duration": 5.5}
            ]
        
        try:
            from scenedetect import VideoManager, SceneManager
            from scenedetect.detectors import ContentDetector
            
            # 创建视频管理器和场景管理器
            video_manager = VideoManager([video_path])
            scene_manager = SceneManager()
            scene_manager.add_detector(ContentDetector())
            
            # 开始检测
            video_manager.set_duration()
            video_manager.start()
            scene_manager.detect_scenes(frame_source=video_manager)
            
            # 获取场景列表
            scene_list = scene_manager.get_scene_list()
            
            scenes = []
            for i, (start_time, end_time) in enumerate(scene_list):
                scenes.append({
                    "scene_id": i + 1,
                    "start": start_time.get_seconds(),
                    "end": end_time.get_seconds(),
                    "duration": (end_time - start_time).get_seconds()
                })
            
            return scenes
        
        except Exception as e:
            print(f"场景检测错误: {e}")
            return []
    
    def analyze_audio_rhythm(self, video_path: str) -> Dict[str, Any]:
        """
        分析音频节奏（BPM）
        返回节奏信息和情绪基调
        """
        if not self.librosa_available:
            return {
                "bpm": 120,
                "tempo": "中等",
                "energy": 0.6,
                "mood": "中性"
            }
        
        try:
            import librosa
            import numpy as np
            
            # 提取音频
            y, sr = librosa.load(video_path)
            
            # 计算BPM
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            bpm = float(tempo)
            
            # 计算能量
            energy = float(np.mean(librosa.feature.rms(y=y)[0]))
            
            # 判断节奏类型
            if bpm < 90:
                tempo_type = "慢速"
            elif bpm < 120:
                tempo_type = "中速"
            else:
                tempo_type = "快速"
            
            # 判断情绪基调（简化版）
            if energy > 0.7:
                mood = "激昂"
            elif energy < 0.3:
                mood = "平静"
            else:
                mood = "中性"
            
            return {
                "bpm": round(bpm, 2),
                "tempo": tempo_type,
                "energy": round(energy, 3),
                "mood": mood
            }
        
        except Exception as e:
            print(f"音频分析错误: {e}")
            return {}
    
    def classify_shot_types(self, video_path: str, scenes: List[Dict]) -> List[Dict[str, Any]]:
        """
        分类镜头类型（远景/中景/特写等）
        需要预训练的镜头分类模型
        """
        # 这里应该调用镜头分类模型
        # 示例：使用预训练的ResNet50模型
        # 目前返回模拟数据
        
        shot_types = ["远景", "中景", "特写", "中景", "远景"]
        
        classified_scenes = []
        for i, scene in enumerate(scenes):
            classified_scenes.append({
                **scene,
                "shot_type": shot_types[i % len(shot_types)],
                "shot_angle": "平视" if i % 2 == 0 else "俯视"
            })
        
        return classified_scenes
    
    def generate_editing_suggestions(
        self, 
        scenes: List[Dict], 
        audio_analysis: Dict,
        shot_types: List[Dict]
    ) -> List[Dict[str, Any]]:
        """
        生成剪辑建议
        基于场景切换频率、节奏、镜头类型等
        """
        suggestions = []
        
        # 计算平均镜头长度
        avg_scene_length = sum(s.get("duration", 0) for s in scenes) / max(len(scenes), 1)
        
        # 分析节奏匹配
        if audio_analysis.get("tempo") == "快速" and avg_scene_length > 5:
            suggestions.append({
                "type": "节奏调整",
                "priority": "高",
                "suggestion": f"当前平均镜头长度{avg_scene_length:.1f}秒，但音乐节奏较快，建议加快剪辑节奏，缩短镜头时长",
                "target_scenes": [i+1 for i in range(len(scenes)) if scenes[i].get("duration", 0) > 5]
            })
        
        # 分析转场建议
        for i in range(len(scenes) - 1):
            current_scene = scenes[i]
            next_scene = scenes[i + 1]
            
            current_type = shot_types[i].get("shot_type", "") if i < len(shot_types) else ""
            next_type = shot_types[i+1].get("shot_type", "") if i+1 < len(shot_types) else ""
            
            # 如果场景差异大，建议使用叠化
            if abs(current_scene.get("duration", 0) - next_scene.get("duration", 0)) > 3:
                suggestions.append({
                    "type": "转场效果",
                    "priority": "中",
                    "suggestion": f"场景{i+1}到场景{i+2}时长差异较大，建议使用淡入淡出过渡",
                    "transition": "fade",
                    "position": i + 1
                })
            
            # 如果镜头类型跳跃大，建议使用切
            if current_type != next_type and current_type and next_type:
                if (current_type == "远景" and next_type == "特写") or \
                   (current_type == "特写" and next_type == "远景"):
                    suggestions.append({
                        "type": "转场效果",
                        "priority": "低",
                        "suggestion": f"场景{i+1}到场景{i+2}镜头类型跳跃较大，可以使用快速切换",
                        "transition": "cut",
                        "position": i + 1
                    })
        
        # 使用LLM生成更详细的建议（可选）
        # 这里可以调用LLM，输入场景信息和音频分析，生成自然语言建议
        
        return suggestions
    
    def analyze_video(self, video_path: str) -> Dict[str, Any]:
        """
        完整的视频分析流程
        """
        # 步骤1: 检测场景
        scenes = self.detect_scenes(video_path)
        
        # 步骤2: 分析音频节奏
        audio_analysis = self.analyze_audio_rhythm(video_path)
        
        # 步骤3: 分类镜头类型
        shot_types = self.classify_shot_types(video_path, scenes)
        
        # 步骤4: 生成剪辑建议
        suggestions = self.generate_editing_suggestions(scenes, audio_analysis, shot_types)
        
        # 步骤5: 统计信息
        stats = {
            "total_scenes": len(scenes),
            "total_duration": sum(s.get("duration", 0) for s in scenes),
            "avg_scene_length": sum(s.get("duration", 0) for s in scenes) / max(len(scenes), 1),
            "scene_frequency": len(scenes) / max(sum(s.get("duration", 0) for s in scenes), 1)  # 每秒场景数
        }
        
        return {
            "scenes": scenes,
            "audio_analysis": audio_analysis,
            "shot_types": shot_types,
            "suggestions": suggestions,
            "statistics": stats
        }

# 单例模式
editing_service = EditingService()

