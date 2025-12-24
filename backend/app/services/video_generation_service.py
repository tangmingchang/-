"""
统一的视频生成服务
支持阿里云DashScope通义万相
支持3-20秒视频生成（通过拼接实现）
"""
import os
import uuid
import asyncio
import subprocess
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
from app.core.config import settings
from app.services.dashscope_service import dashscope_service


class VideoGenerationService:
    """统一的视频生成服务"""
    
    def __init__(self):
        self.video_storage_dir = os.path.join(settings.MEDIA_ROOT, "videos")
        os.makedirs(self.video_storage_dir, exist_ok=True)
        self.tmp_dir = os.path.join(settings.MEDIA_ROOT, "tmp")
        os.makedirs(self.tmp_dir, exist_ok=True)
    
    async def generate_video(
        self,
        engine: str,
        mode: str,
        prompt: str,
        image_url: Optional[str] = None,
        audio_url: Optional[str] = None,
        duration: int = 5,
        resolution: str = "720P",
        model: Optional[str] = None,
        audio: bool = True,
        prompt_extend: bool = True
    ) -> Dict[str, Any]:
        """
        生成视频（统一接口）
        
        Args:
            engine: 引擎类型（"aliyun"）
            mode: 生成模式（"t2v" | "i2v"）
            prompt: 文本提示（中文）
            image_url: 图片URL（图生视频时必填）
            audio_url: 音频URL（可选，音频驱动）
            duration: 视频时长（秒，3-20）
            resolution: 分辨率（"480P" | "720P" | "1080P"）
            model: 模型名称（可选，使用默认模型）
            audio: 是否自动配音（仅aliyun引擎的wan2.5支持）
            prompt_extend: 是否自动润色Prompt
        
        Returns:
            包含job_id或video_url的字典
        """
        # 验证参数
        if engine != "aliyun":
            return {
                "error": f"不支持的引擎: {engine}",
                "message": "支持的引擎: aliyun（DashScope通义万相）"
            }
        
        if mode not in ["t2v", "i2v"]:
            return {
                "error": f"不支持的模式: {mode}",
                "message": "支持的模式: t2v, i2v"
            }
        
        if mode == "i2v" and not image_url:
            return {
                "error": "图生视频模式需要提供image_url"
            }
        
        if duration < 3 or duration > 20:
            return {
                "error": f"不支持的时长: {duration}",
                "message": "支持的时长范围: 3-20秒"
            }
        
        # 使用阿里云DashScope生成视频
        return await self._generate_with_aliyun(
            mode=mode,
            prompt=prompt,
            image_url=image_url,
            audio_url=audio_url,
            duration=duration,
            resolution=resolution,
            model=model,
            audio=audio,
            prompt_extend=prompt_extend
        )
    
    async def _generate_with_aliyun(
        self,
        mode: str,
        prompt: str,
        image_url: Optional[str],
        audio_url: Optional[str],
        duration: int,
        resolution: str,
        model: Optional[str],
        audio: bool,
        prompt_extend: bool
    ) -> Dict[str, Any]:
        """使用阿里云DashScope生成视频"""
        # 确定单次生成的最大时长
        max_single_duration = 10  # wan2.5支持10秒
        
        if duration <= max_single_duration:
            # 单次生成即可
            if mode == "t2v":
                result = await dashscope_service.generate_text_to_video(
                    prompt=prompt,
                    resolution=resolution,
                    duration=duration,
                    model=model,
                    audio=audio,
                    prompt_extend=prompt_extend
                )
            else:  # i2v
                result = await dashscope_service.generate_image_to_video(
                    image_url=image_url,
                    prompt=prompt,
                    resolution=resolution,
                    duration=duration,
                    model=model,
                    audio=audio,
                    prompt_extend=prompt_extend
                )
            
            return result
        else:
            # 需要分段生成并拼接
            return await self._generate_long_video_aliyun(
                mode=mode,
                prompt=prompt,
                image_url=image_url,
                audio_url=audio_url,
                duration=duration,
                resolution=resolution,
                model=model,
                audio=audio,
                prompt_extend=prompt_extend
            )
    
    async def _generate_long_video_aliyun(
        self,
        mode: str,
        prompt: str,
        image_url: Optional[str],
        audio_url: Optional[str],
        duration: int,
        resolution: str,
        model: Optional[str],
        audio: bool,
        prompt_extend: bool
    ) -> Dict[str, Any]:
        """
        生成长视频（15-20秒）：分段生成后拼接
        """
        # 将时长拆分为多个10秒或5秒的片段
        segment_durations = []
        remaining = duration
        
        while remaining > 0:
            if remaining >= 10:
                segment_durations.append(10)
                remaining -= 10
            elif remaining >= 5:
                segment_durations.append(5)
                remaining -= 5
            else:
                # 剩余不足5秒，合并到最后一个片段
                if segment_durations:
                    segment_durations[-1] += remaining
                else:
                    segment_durations.append(remaining)
                remaining = 0
        
        # 生成多个任务
        task_ids = []
        for i, seg_duration in enumerate(segment_durations):
            # 为每个片段生成任务
            if mode == "t2v":
                result = await dashscope_service.generate_text_to_video(
                    prompt=f"{prompt}（第{i+1}段）",
                    resolution=resolution,
                    duration=seg_duration,
                    model=model,
                    audio=audio,
                    prompt_extend=prompt_extend
                )
            else:  # i2v
                result = await dashscope_service.generate_image_to_video(
                    image_url=image_url,
                    prompt=f"{prompt}（第{i+1}段）" if prompt else None,
                    resolution=resolution,
                    duration=seg_duration,
                    model=model,
                    audio=audio,
                    prompt_extend=prompt_extend
                )
            
            if "error" in result:
                return result
            
            task_ids.append(result["task_id"])
        
        # 返回任务列表，由调用方等待所有任务完成后再拼接
        return {
            "success": True,
            "task_ids": task_ids,
            "segment_durations": segment_durations,
            "status": "PENDING",
            "message": f"已创建{len(task_ids)}个分段任务，需要等待所有任务完成后拼接"
        }
    
    
    async def concatenate_videos(
        self,
        video_paths: List[str],
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        使用ffmpeg拼接多个视频
        
        Args:
            video_paths: 视频文件路径列表
            output_path: 输出路径（可选，默认自动生成）
        
        Returns:
            拼接结果
        """
        if not video_paths:
            return {
                "error": "视频列表为空"
            }
        
        # 检查所有视频文件是否存在
        for path in video_paths:
            if not os.path.exists(path):
                return {
                    "error": f"视频文件不存在: {path}"
                }
        
        # 生成输出路径
        if not output_path:
            output_filename = f"concatenated_{uuid.uuid4().hex[:8]}.mp4"
            output_path = os.path.join(self.video_storage_dir, output_filename)
        
        # 创建ffmpeg concat列表文件
        concat_list_path = os.path.join(self.tmp_dir, f"concat_list_{uuid.uuid4().hex[:8]}.txt")
        with open(concat_list_path, "w", encoding="utf-8") as f:
            for video_path in video_paths:
                # 使用绝对路径，避免相对路径问题
                abs_path = os.path.abspath(video_path)
                # 转义单引号和反斜杠
                abs_path = abs_path.replace("'", "'\\''")
                f.write(f"file '{abs_path}'\n")
        
        try:
            # 使用ffmpeg拼接（无重编码，快速）
            cmd = [
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_list_path,
                "-c", "copy",  # 无重编码，直接复制流
                "-y",  # 覆盖输出文件
                output_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # 清理临时文件
            if os.path.exists(concat_list_path):
                os.remove(concat_list_path)
            
            if result.returncode == 0 and os.path.exists(output_path):
                return {
                    "success": True,
                    "output_path": output_path,
                    "message": f"成功拼接{len(video_paths)}个视频"
                }
            else:
                return {
                    "error": "视频拼接失败",
                    "message": result.stderr or "ffmpeg执行失败",
                    "stdout": result.stdout
                }
        
        except subprocess.TimeoutExpired:
            return {
                "error": "视频拼接超时",
                "message": "ffmpeg执行超过5分钟"
            }
        except FileNotFoundError:
            return {
                "error": "ffmpeg未安装",
                "message": "请安装ffmpeg: https://ffmpeg.org/download.html"
            }
        except Exception as e:
            return {
                "error": str(e),
                "message": f"视频拼接异常: {type(e).__name__}"
            }
    
    async def wait_and_concatenate_aliyun_tasks(
        self,
        task_ids: List[str],
        segment_durations: List[int],
        max_wait_time: int = 600,
        poll_interval: int = 10
    ) -> Dict[str, Any]:
        """
        等待所有阿里云任务完成并拼接视频
        
        Args:
            task_ids: 任务ID列表
            segment_durations: 每个片段的时长列表
            max_wait_time: 最大等待时间（秒）
            poll_interval: 轮询间隔（秒）
        
        Returns:
            拼接后的视频路径
        """
        start_time = time.time()
        video_paths = []
        
        # 等待所有任务完成
        for i, task_id in enumerate(task_ids):
            while True:
                # 检查超时
                elapsed = time.time() - start_time
                if elapsed > max_wait_time:
                    return {
                        "error": "任务超时",
                        "message": f"等待任务{task_id}完成超过{max_wait_time}秒",
                        "completed_segments": len(video_paths)
                    }
                
                # 查询任务状态
                status_result = await dashscope_service.get_task_status(task_id)
                
                if "error" in status_result and status_result.get("status") != "PENDING":
                    return {
                        "error": f"任务{task_id}失败",
                        "message": status_result.get("error", "未知错误"),
                        "completed_segments": len(video_paths)
                    }
                
                if status_result.get("status") == "SUCCEEDED":
                    local_path = status_result.get("local_path")
                    if local_path:
                        video_paths.append(local_path)
                        break
                    else:
                        return {
                            "error": f"任务{task_id}完成但未获取到视频路径",
                            "completed_segments": len(video_paths)
                        }
                elif status_result.get("status") == "FAILED":
                    return {
                        "error": f"任务{task_id}失败",
                        "message": status_result.get("error", "任务执行失败"),
                        "completed_segments": len(video_paths)
                    }
                
                # 等待后继续轮询
                await asyncio.sleep(poll_interval)
        
        # 所有任务完成，拼接视频
        if len(video_paths) == len(task_ids):
            return await self.concatenate_videos(video_paths)
        else:
            return {
                "error": "部分任务未完成",
                "message": f"期望{len(task_ids)}个视频，实际完成{len(video_paths)}个",
                "completed_segments": video_paths
            }


# 全局实例
video_generation_service = VideoGenerationService()

