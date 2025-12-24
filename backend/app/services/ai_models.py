"""
AI模型服务接口层
"""
import httpx
import json
import asyncio
import os
import shutil
from uuid import uuid4
from typing import Optional, Dict, Any
from app.core.config import settings
import openai
from openai import OpenAI
# gradio_client 已不再使用（Wan-2.1服务已废弃）
# from gradio_client import Client, handle_file

class StableDiffusionService:
    """Stable Diffusion文生图服务"""
    
    def __init__(self):
        self.api_url = settings.STABLE_DIFFUSION_API_URL
        self.api_key = settings.STABLE_DIFFUSION_API_KEY
    
    async def generate_image(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: int = 512,
        height: int = 512,
        steps: int = 20,
        cfg_scale: float = 7.0
    ) -> Dict[str, Any]:
        """生成图像"""
        if not self.api_url:
            raise ValueError("Stable Diffusion API URL未配置")
        
        payload = {
            "prompt": prompt,
            "width": width,
            "height": height,
            "steps": steps,
            "cfg_scale": cfg_scale
        }
        
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/generate",
                json=payload,
                headers=headers,
                timeout=300.0
            )
            response.raise_for_status()
            return response.json()

class KlingVideoService:
    """视频生成服务（已废弃，请使用 /api/video/generate 接口）"""
    
    def __init__(self):
        # 此服务已废弃，所有视频生成功能已迁移到DashScope通义万相
        # 保留此类仅用于向后兼容，避免导入错误
        self.api_key = None
        self.use_modelscope = False
        self.gradio_client_url = ""
        self.tmp_path = "tmp"
        import os
        os.makedirs(self.tmp_path, exist_ok=True)
        # 不打印警告，避免启动时输出过多信息
    
    async def _check_process(self, client, method: str, seg_id: str) -> Optional[str]:
        """轮询检查视频生成进度（已废弃）"""
        # 此方法已废弃，永远不会被调用
        return None
        import shutil
        from uuid import uuid4
        
        max_retries = 120  # 最多等待60分钟（120次 * 30秒）
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                process = client.predict(api_name="/get_process_bar")
                process_value = process.get("value", 0)
                process_label = process.get("label", "")
                
                print(f"[seg{seg_id}]-{method}-进度: {process_value}% - {process_label}")
                
                if process_value == 100:
                    # 生成完成，获取视频路径
                    video_retry_count = 0
                    while video_retry_count < 10:  # 最多等待10分钟获取视频
                        video_path = client.predict(api_name="/process_change")
                        value = video_path.get("value", {})
                        if video_path and value:
                            src_path = value.get("video")
                            if src_path and os.path.exists(src_path):
                                # 移动视频到临时目录
                                dst_path = os.path.join(self.tmp_path, f"{str(uuid4())}.mp4")
                                shutil.move(src_path, dst_path)
                                print(f"[seg{seg_id}]-{method}-[成功]-输出: {dst_path}")
                                return dst_path
                        await asyncio.sleep(60)  # 等待60秒后重试
                        video_retry_count += 1
                    
                    # 如果10分钟内还没获取到视频，返回None
                    return None
                    
                await asyncio.sleep(30)  # 每30秒检查一次进度
                retry_count += 1
            except Exception as e:
                error_str = str(e)
                if "Queue is full" in error_str:
                    print(f"[seg{seg_id}]-{method}-队列已满，等待60秒后重试...")
                    await asyncio.sleep(60)  # 队列满，等待更长时间
                    retry_count += 1
                else:
                    print(f"[seg{seg_id}]-{method}-检查进度时出错: {error_str}")
                    raise e
        
        # 超时
        return None
    
    async def generate_video(
        self,
        prompt: str,
        duration: int = 5
    ) -> Dict[str, Any]:
        """从文本生成视频（已废弃，请使用 /api/video/generate）"""
        return {
            "error": "此服务已废弃",
            "message": "请使用 /api/video/generate 接口（DashScope通义万相）",
            "new_endpoint": "/api/video/generate",
            "help": {
                "新接口": "/api/video/generate",
                "文档": "参考通义万相视频生成使用指南.md"
            }
        }
        
        # 以下代码已废弃，永远不会执行
        pass
    
    async def generate_video_from_image(
        self,
        image_url: str,
        prompt: Optional[str] = None,
        duration: int = 5
    ) -> Dict[str, Any]:
        """从图像生成视频（已废弃，请使用 /api/video/generate）"""
        return {
            "error": "此服务已废弃",
            "message": "请使用 /api/video/generate 接口（DashScope通义万相）",
            "new_endpoint": "/api/video/generate",
            "help": {
                "新接口": "/api/video/generate",
                "文档": "参考通义万相视频生成使用指南.md"
            }
        }
        
        # 以下代码已废弃，永远不会执行
        if False:  # 永远不会执行
            if self.use_modelscope:
                return await self.modelscope_service.generate_video_from_image(
                    image_url=image_url,
                    prompt=prompt,
                    duration=duration
                )
            
            if not self.api_key:
                return {
                    "error": "WAN21 API Key未配置",
                    "message": "请在环境变量中设置WAN21_API_KEY"
                }
        
            # 以下代码已废弃，永远不会执行
            pass

class GPT4Service:
    """GPT-4大语言模型服务"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
    
    async def analyze_script(
        self,
        script_content: str
    ) -> Dict[str, Any]:
        """分析剧本"""
        if not self.client:
            raise ValueError("OpenAI API Key未配置")
        
        prompt = f"""请分析以下影视剧本，提供详细的结构分析、人物分析、对白质量评估和改进建议。

剧本内容：
{script_content}

请以JSON格式返回分析结果，包含以下字段：
- structure_analysis: 结构分析（三幕结构、冲突点等）
- character_analysis: 人物分析（角色性格、动机等）
- dialogue_quality: 对白质量评估
- narrative_flow: 叙事流畅度
- strengths: 优点
- weaknesses: 不足
- suggestions: 改进建议
"""
        
        response = self.client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "你是一位专业的影视剧本分析专家。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        result_text = response.choices[0].message.content
        
        # 尝试解析JSON
        try:
            return json.loads(result_text)
        except:
            return {"analysis": result_text}

class WhisperService:
    """Whisper语音识别服务"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
    
    async def transcribe_audio(
        self,
        audio_file_path: str,
        language: Optional[str] = "zh"
    ) -> Dict[str, Any]:
        """转录音频"""
        if not self.client:
            raise ValueError("OpenAI API Key未配置")
        
        with open(audio_file_path, "rb") as audio_file:
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language
            )
        
        return {
            "text": transcript.text,
            "language": language
        }

# 全局服务实例
stable_diffusion_service = StableDiffusionService()
kling_video_service = KlingVideoService()  # 使用fal.ai的Kling Video
gpt4_service = GPT4Service()
whisper_service = WhisperService()

# 为了向后兼容，保留pika_service别名
pika_service = kling_video_service


