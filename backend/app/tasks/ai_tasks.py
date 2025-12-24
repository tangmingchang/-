"""
AI任务异步处理
"""
from app.celery_app import celery_app, CELERY_AVAILABLE
from app.services.ai_models import (
    stable_diffusion_service,
    pika_service,
    gpt4_service,
    whisper_service
)
import os

if CELERY_AVAILABLE:
    @celery_app.task(name="generate_image")
    def generate_image_task(prompt: str, **kwargs):
        """异步生成图像任务"""
        import asyncio
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(
            stable_diffusion_service.generate_image(prompt, **kwargs)
        )
    
    @celery_app.task(name="generate_video_from_text")
    def generate_video_from_text_task(prompt: str, **kwargs):
        """异步生成视频任务（文生视频）"""
        import asyncio
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(
            pika_service.generate_video(prompt, **kwargs)
        )
    
    @celery_app.task(name="generate_video_from_image")
    def generate_video_from_image_task(image_url: str, **kwargs):
        """异步生成视频任务（图生视频）"""
        import asyncio
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(
            pika_service.generate_video_from_image(image_url, **kwargs)
        )
    
    @celery_app.task(name="analyze_script")
    def analyze_script_task(script_content: str):
        """异步分析剧本任务"""
        import asyncio
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(
            gpt4_service.analyze_script(script_content)
        )
    
    @celery_app.task(name="transcribe_audio")
    def transcribe_audio_task(audio_file_path: str, language: str = "zh"):
        """异步转录音频任务"""
        import asyncio
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_file_path}")
        
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(
            whisper_service.transcribe_audio(audio_file_path, language)
        )
else:
    # Celery未安装，创建模拟任务对象
    class MockTask:
        def __init__(self, task_id="mock_task"):
            self.id = task_id
        
        def delay(self, *args, **kwargs):
            return self
    
    def generate_image_task(*args, **kwargs):
        return MockTask()
    
    def generate_video_from_text_task(*args, **kwargs):
        return MockTask()
    
    def generate_video_from_image_task(*args, **kwargs):
        return MockTask()
    
    def analyze_script_task(*args, **kwargs):
        return MockTask()
    
    def transcribe_audio_task(*args, **kwargs):
        return MockTask()

