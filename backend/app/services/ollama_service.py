"""
Ollama本地LLM服务
通过HTTP API调用本地运行的Ollama服务
"""
import httpx
import requests
from typing import List, Dict, Optional, AsyncGenerator
from app.core.config import settings

class OllamaService:
    """Ollama本地LLM服务"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.default_model = "qwen:7b"  # 默认模型，可以根据需要修改
        self.available = False
        self._check_availability()
    
    def _check_availability(self):
        """检查Ollama服务是否可用"""
        try:
            import httpx
            import requests
            
            # 使用同步请求检查（更简单可靠）
            try:
                response = requests.get(f"{self.base_url}/api/tags", timeout=2.0)
                self.available = response.status_code == 200
                if self.available:
                    print("✅ Ollama服务已连接")
                else:
                    print(f"警告: Ollama服务响应异常，状态码: {response.status_code}")
            except requests.exceptions.RequestException:
                self.available = False
                print("警告: Ollama服务未运行，请先安装并启动Ollama")
                print("安装方法: 下载 https://ollama.com/download/OllamaSetup.exe")
                print("启动方法: ollama serve 或直接运行Ollama应用")
        except ImportError:
            print("警告: httpx或requests未安装，Ollama服务不可用")
            self.available = False
        except Exception as e:
            print(f"警告: Ollama服务检查失败: {e}")
            self.available = False
    
    async def list_models(self) -> List[str]:
        """列出可用的模型"""
        if not self.available:
            return []
        
        try:
            # 使用同步requests（更可靠）
            response = requests.get(f"{self.base_url}/api/tags", timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                models = [model["name"] for model in data.get("models", [])]
                return models
            else:
                print(f"获取模型列表失败，状态码: {response.status_code}")
        except Exception as e:
            print(f"获取Ollama模型列表失败: {e}")
        
        return []
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        stream: bool = False,
        temperature: float = 0.7
    ) -> Dict:
        """聊天完成"""
        if not self.available:
            return {
                "error": "Ollama服务不可用",
                "message": "请确保Ollama服务正在运行（ollama serve）"
            }
        
        model = model or self.default_model
        
        try:
            if stream:
                # 流式响应 - 使用httpx异步
                async with httpx.AsyncClient(timeout=300.0) as client:
                    async with client.stream(
                        "POST",
                        f"{self.base_url}/api/chat",
                        json={
                            "model": model,
                            "messages": messages,
                            "stream": True,
                            "options": {
                                "temperature": temperature
                            }
                        }
                    ) as response:
                        if response.status_code == 200:
                            full_text = ""
                            async for line in response.aiter_lines():
                                if line:
                                    import json
                                    chunk = json.loads(line)
                                    if "message" in chunk and "content" in chunk["message"]:
                                        full_text += chunk["message"]["content"]
                                    if chunk.get("done", False):
                                        break
                            return {"message": {"content": full_text, "role": "assistant"}}
                        else:
                            return {
                                "error": f"HTTP {response.status_code}",
                                "message": "流式请求失败"
                            }
            else:
                # 非流式响应 - 使用同步requests（更可靠）
                response = requests.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": model,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "temperature": temperature
                        }
                    },
                    timeout=300.0
                )
                if response.status_code == 200:
                    data = response.json()
                    message_content = data.get("message", {}).get("content", "")
                    return {
                        "message": {
                            "content": message_content,
                            "role": "assistant"
                        }
                    }
                else:
                    return {
                        "error": f"HTTP {response.status_code}",
                        "message": response.text[:200] if hasattr(response, 'text') else str(response)
                    }
        except httpx.ConnectError:
            return {
                "error": "连接失败", "message": "无法连接到Ollama服务，请确保服务正在运行"}
        except Exception as e:
            return {"error": str(e), "message": f"Ollama调用失败: {str(e)}"}
    
    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """流式聊天"""
        if not self.available:
            yield "错误: Ollama服务不可用"
            return
        
        model = model or self.default_model
        
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json={
                        "model": model,
                        "messages": messages,
                        "stream": True,
                        "options": {
                            "temperature": temperature
                        }
                    }
                ) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if line:
                                import json
                                chunk = json.loads(line)
                                if "message" in chunk and "content" in chunk["message"]:
                                    yield chunk["message"]["content"]
                                if chunk.get("done", False):
                                    break
        except Exception as e:
            yield f"错误: {str(e)}"
    
    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        """将消息列表格式化为Ollama的prompt格式（已废弃，现在使用chat API）"""
        # 这个方法现在不再使用，因为chat API直接接受消息列表
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        return "\n\n".join(prompt_parts)

# 全局实例
ollama_service = OllamaService()

