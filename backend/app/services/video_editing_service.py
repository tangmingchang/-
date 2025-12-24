"""
视频编辑服务 - 使用MoviePy
"""
import os
import sys
from typing import Dict, List, Optional, Any
from pathlib import Path

class VideoEditingService:
    """视频编辑服务"""
    
    def __init__(self):
        self.moviepy_available = False
        self._init_moviepy()
    
    def _init_moviepy(self):
        """初始化MoviePy"""
        # MoviePy应该通过pip安装: pip install moviepy
        try:
            from moviepy import VideoFileClip, concatenate_videoclips, CompositeVideoClip, TextClip
            self.VideoFileClip = VideoFileClip
            self.concatenate_videoclips = concatenate_videoclips
            self.CompositeVideoClip = CompositeVideoClip
            self.TextClip = TextClip
            self.moviepy_available = True
            print("✅ MoviePy已加载")
        except ImportError:
            print("警告: MoviePy未安装，视频编辑功能受限")
            print("安装方法: pip install moviepy 或运行 python install_local_models.py")
            self.moviepy_available = False
    
    def cut_video(
        self,
        video_path: str,
        start_time: float,
        end_time: float,
        output_path: str
    ) -> Dict[str, Any]:
        """裁剪视频"""
        if not self.moviepy_available:
            return {"error": "MoviePy未安装"}
        
        try:
            clip = self.VideoFileClip(video_path)
            cut_clip = clip.subclipped(start_time, end_time)
            cut_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
            clip.close()
            cut_clip.close()
            
            return {
                "success": True,
                "output_path": output_path,
                "duration": end_time - start_time
            }
        except Exception as e:
            return {"error": str(e)}
    
    def concatenate_videos(
        self,
        video_paths: List[str],
        output_path: str
    ) -> Dict[str, Any]:
        """拼接多个视频"""
        if not self.moviepy_available:
            return {"error": "MoviePy未安装"}
        
        try:
            clips = [self.VideoFileClip(path) for path in video_paths]
            final_clip = self.concatenate_videoclips(clips)
            final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
            
            for clip in clips:
                clip.close()
            final_clip.close()
            
            return {
                "success": True,
                "output_path": output_path,
                "clip_count": len(video_paths)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def add_text_overlay(
        self,
        video_path: str,
        text: str,
        output_path: str,
        position: str = "center",
        font_size: int = 50,
        color: str = "white",
        duration: Optional[float] = None
    ) -> Dict[str, Any]:
        """添加文字叠加"""
        if not self.moviepy_available:
            return {"error": "MoviePy未安装"}
        
        try:
            video_clip = self.VideoFileClip(video_path)
            
            # 创建文字clip
            txt_clip = self.TextClip(
                text=text,
                fontsize=font_size,
                color=color
            ).with_duration(duration or video_clip.duration).with_position(position)
            
            # 合成视频
            final_video = self.CompositeVideoClip([video_clip, txt_clip])
            final_video.write_videofile(output_path, codec='libx264', audio_codec='aac')
            
            video_clip.close()
            txt_clip.close()
            final_video.close()
            
            return {
                "success": True,
                "output_path": output_path
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """获取视频信息"""
        if not self.moviepy_available:
            return {"error": "MoviePy未安装"}
        
        try:
            clip = self.VideoFileClip(video_path)
            info = {
                "duration": clip.duration,
                "fps": clip.fps,
                "size": clip.size,
                "has_audio": clip.audio is not None
            }
            clip.close()
            return info
        except Exception as e:
            return {"error": str(e)}

# 全局实例
video_editing_service = VideoEditingService()

