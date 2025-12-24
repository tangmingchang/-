"""
AI服务 - 集成OpenAI和其他AI模型
优先使用阿里云百炼DashScope通义千问，支持OpenAI和Ollama作为备选
"""
from openai import OpenAI
from app.core.config import settings
from app.core.prompts import FILM_EDUCATION_SYSTEM_PROMPT
from typing import List, Dict, Optional
import json
import asyncio

class AIService:
    """AI服务类"""
    
    def __init__(self):
        self.client = None
        if settings.OPENAI_API_KEY:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        
        # 优先使用DashScope通义千问
        try:
            from app.services.dashscope_service import dashscope_service
            self.dashscope_service = dashscope_service
            self.use_dashscope = bool(settings.DASHSCOPE_API_KEY)
        except ImportError:
            self.dashscope_service = None
            self.use_dashscope = False
        
        # 尝试加载Ollama作为备选
        try:
            from app.services.ollama_service import ollama_service
            self.ollama_service = ollama_service
            self.use_ollama_fallback = True
        except ImportError:
            self.ollama_service = None
            self.use_ollama_fallback = False
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ):
        """聊天完成"""
        # 优先使用DashScope通义千问
        if self.use_dashscope and self.dashscope_service:
            try:
                response = await self.dashscope_service.chat_completion(
                    messages=messages,
                    model="qwen-turbo",  # 或 "qwen-plus", "qwen-max"
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=stream
                )
                return response
            except Exception as e:
                print(f"DashScope通义千问调用失败: {e}，尝试使用OpenAI")
        
        # 如果DashScope不可用，尝试使用OpenAI
        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stream=stream,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response
            except Exception as e:
                print(f"OpenAI调用失败: {e}，尝试使用Ollama")
        
        # 如果OpenAI不可用，尝试使用Ollama
        if self.use_ollama_fallback and self.ollama_service and self.ollama_service.available:
            try:
                result = await self.ollama_service.chat(
                    messages=messages,
                    stream=stream,
                    temperature=temperature
                )
                if "error" not in result:
                    # 转换为OpenAI格式
                    class MockResponse:
                        def __init__(self, content):
                            self.choices = [MockChoice(content)]
                    
                    class MockChoice:
                        def __init__(self, content):
                            self.message = MockMessage(content)
                    
                    class MockMessage:
                        def __init__(self, content):
                            self.content = content
                            self.role = "assistant"
                    
                    return MockResponse(result.get("message", {}).get("content", ""))
            except Exception as e:
                print(f"Ollama调用失败: {e}")
        
        # 如果都不可用，返回模拟响应
        return self._mock_response(messages[-1]["content"])
    
    async def stream_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7
    ):
        """流式聊天完成"""
        # 优先使用DashScope通义千问
        if self.use_dashscope and self.dashscope_service:
            try:
                async for chunk in self.dashscope_service.stream_chat_completion(
                    messages=messages,
                    model="qwen-turbo",
                    temperature=temperature
                ):
                    yield chunk
                return
            except Exception as e:
                print(f"DashScope流式调用失败: {e}，尝试使用OpenAI")
        
        # 如果DashScope不可用，尝试使用OpenAI
        if self.client:
            try:
                stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stream=True,
                    temperature=temperature
                )
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                return
            except Exception as e:
                print(f"OpenAI流式调用失败: {e}")
        
        # 如果都不可用，模拟流式响应
        mock_text = self._mock_response(messages[-1]["content"])
        for char in mock_text:
            yield char
            await asyncio.sleep(0.01)
    
    def _mock_response(self, user_message: str) -> str:
        """模拟响应（用于测试）"""
        responses = {
            "你好": "你好！我是影视制作教育智能体，可以帮助你学习影视制作相关知识。",
            "什么是影视制作": "影视制作是指通过技术手段将创意转化为视听作品的过程，包括前期策划、拍摄、后期制作等环节。",
        }
        
        for key, value in responses.items():
            if key in user_message:
                return value
        
        return f"关于'{user_message}'，这是一个很好的问题。作为影视制作教育智能体，我可以为你提供相关的知识和建议。请告诉我你想了解的具体方面。"
    
    def format_messages(
        self,
        conversation_history: List[Dict],
        system_prompt: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """格式化消息"""
        messages = []
        
        # 系统提示词
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        else:
            # 使用专业提示词
            messages.append({
                "role": "system",
                "content": FILM_EDUCATION_SYSTEM_PROMPT
            })
        
        # 添加对话历史
        for msg in conversation_history:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
        
        return messages

ai_service = AIService()

