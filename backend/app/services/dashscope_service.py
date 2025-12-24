"""
阿里云百炼（DashScope）通义万相服务
支持文生视频（T2V）和图生视频（I2V）
使用DashScope SDK和HTTP API两种方式
"""
import os
import uuid
import asyncio
import httpx
import base64
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from app.core.config import settings

# 尝试导入dashscope SDK（如果已安装）
try:
    import dashscope
    DASHSCOPE_SDK_AVAILABLE = True
except ImportError:
    DASHSCOPE_SDK_AVAILABLE = False
    dashscope = None

class DashScopeService:
    """阿里云百炼DashScope通义万相服务"""
    
    def __init__(self):
        self.api_key = settings.DASHSCOPE_API_KEY
        self.base_url = settings.DASHSCOPE_BASE_URL
        self.video_storage_dir = os.path.join(settings.MEDIA_ROOT, "videos")
        os.makedirs(self.video_storage_dir, exist_ok=True)
        
        # 检查API Key配置
        if not self.api_key:
            print("⚠️  警告: DASHSCOPE_API_KEY未配置，视频生成功能将无法使用")
            print("   请在.env文件中设置DASHSCOPE_API_KEY，或从环境变量中读取")
            print("   获取API Key: https://dashscope.console.aliyun.com/apiKey")
        else:
            print(f"[DashScope] API Key已配置（长度: {len(self.api_key)}字符，前10位: {self.api_key[:10]}...）")
            print(f"[DashScope] Base URL: {self.base_url}")
        
        # 如果SDK可用，设置API key
        if DASHSCOPE_SDK_AVAILABLE and self.api_key:
            dashscope.api_key = self.api_key
            # 设置API基础URL（如果需要）
            if hasattr(dashscope, 'base_http_api_url'):
                dashscope.base_http_api_url = self.base_url
        
        # 默认模型配置
        self.default_t2v_model = settings.WANX_T2V_MODEL
        self.default_i2v_model = settings.WANX_I2V_MODEL
        
        # 支持的模型列表
        self.t2v_models = {
            "wan2.5-t2v-preview": {
                "resolutions": ["480P", "720P", "1080P"],
                "durations": [5, 10],
                "supports_audio": True,
                "fps": 24
            },
            "wan2.2-t2v-plus": {
                "resolutions": ["480P", "1080P"],
                "durations": [5],
                "supports_audio": False,
                "fps": 30
            }
        }
        
        self.i2v_models = {
            "wan2.5-i2v-preview": {
                "resolutions": ["480P", "720P", "1080P"],
                "durations": [5, 10],
                "supports_audio": True,
                "fps": 24
            },
            "wan2.2-i2v-flash": {
                "resolutions": ["480P", "720P", "1080P"],
                "durations": [5],
                "supports_audio": False,
                "fps": 30
            },
            "wan2.2-i2v-plus": {
                "resolutions": ["480P", "1080P"],
                "durations": [5],
                "supports_audio": False,
                "fps": 30
            },
            "wanx2.1-i2v-turbo": {
                "resolutions": ["480P", "720P"],
                "durations": [3, 4, 5],
                "supports_audio": False,
                "fps": 24
            }
        }
    
    def _check_api_key(self) -> Optional[Dict[str, Any]]:
        """检查API Key是否配置"""
        if not self.api_key:
            return {
                "error": "DASHSCOPE_API_KEY未配置",
                "message": "请在.env文件中设置DASHSCOPE_API_KEY",
                "help": {
                    "获取方式": "访问 https://dashscope.console.aliyun.com/apiKey 创建API Key",
                    "配置方法": "在.env文件中添加: DASHSCOPE_API_KEY=你的API密钥"
                }
            }
        return None
    
    def _get_resolution_size(self, resolution: str) -> str:
        """将分辨率字符串转换为API需要的格式"""
        resolution_map = {
            "480P": "832*480",
            "720P": "1280*720",
            "1080P": "1920*1080"
        }
        return resolution_map.get(resolution, "832*480")
    
    async def generate_text_to_video(
        self,
        prompt: str,
        resolution: str = "720P",
        duration: int = 5,
        model: Optional[str] = None,
        audio: bool = True,
        prompt_extend: bool = True
    ) -> Dict[str, Any]:
        """
        文生视频（Text-to-Video）
        
        Args:
            prompt: 视频描述文本（中文）
            resolution: 分辨率（480P/720P/1080P）
            duration: 时长（秒，根据模型支持：3/4/5/10）
            model: 模型名称（默认使用配置的模型）
            audio: 是否自动配音（仅wan2.5支持）
            prompt_extend: 是否自动润色Prompt
        
        Returns:
            包含task_id或video_url的字典
        """
        # 检查API Key
        api_key_error = self._check_api_key()
        if api_key_error:
            return api_key_error
        
        # 使用默认模型或指定模型
        model_name = model or self.default_t2v_model
        
        # 验证模型和参数
        if model_name not in self.t2v_models:
            return {
                "error": f"不支持的模型: {model_name}",
                "message": f"支持的T2V模型: {', '.join(self.t2v_models.keys())}"
            }
        
        model_info = self.t2v_models[model_name]
        if duration not in model_info["durations"]:
            return {
                "error": f"模型{model_name}不支持{duration}秒时长",
                "message": f"支持的时长: {model_info['durations']}"
            }
        
        if resolution not in model_info["resolutions"]:
            return {
                "error": f"模型{model_name}不支持{resolution}分辨率",
                "message": f"支持的分辨率: {model_info['resolutions']}"
            }
        
        # 如果模型不支持audio但请求了audio，自动关闭
        if not model_info["supports_audio"] and audio:
            audio = False
        
        # 准备请求
        url = f"{self.base_url}/services/aigc/video-generation/video-synthesis"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-DashScope-Async": "enable",
            "Content-Type": "application/json"
        }
        
        # 构建请求体
        size = self._get_resolution_size(resolution)
        request_body = {
            "model": model_name,
            "input": {
                "prompt": prompt
            },
            "parameters": {
                "size": size,
                "duration": duration,
                "prompt_extend": prompt_extend
            }
        }
        
        # 添加audio参数（如果支持）
        if model_info["supports_audio"]:
            request_body["parameters"]["audio"] = audio
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 第一步：创建任务
                response = await client.post(url, json=request_body, headers=headers)
                
                if response.status_code != 200:
                    error_data = response.json() if response.content else {}
                    return {
                        "error": f"API调用失败: {response.status_code}",
                        "message": error_data.get("message", response.text),
                        "code": error_data.get("code", "UNKNOWN_ERROR")
                    }
                
                result = response.json()
                
                # 获取task_id
                task_id = result.get("output", {}).get("task_id")
                if not task_id:
                    return {
                        "error": "未获取到task_id",
                        "message": "API响应格式异常",
                        "response": result
                    }
                
                # 返回task_id，由调用方轮询
                return {
                    "success": True,
                    "task_id": task_id,
                    "status": "PENDING",
                    "message": "视频生成任务已创建，请使用task_id轮询状态"
                }
        
        except httpx.TimeoutException:
            return {
                "error": "请求超时",
                "message": "连接DashScope API超时，请检查网络"
            }
        except Exception as e:
            return {
                "error": str(e),
                "message": f"调用DashScope API失败: {type(e).__name__}"
            }
    
    async def generate_image_to_video(
        self,
        image_url: str,
        prompt: Optional[str] = None,
        resolution: str = "720P",
        duration: int = 5,
        model: Optional[str] = None,
        audio: bool = True,
        prompt_extend: bool = True
    ) -> Dict[str, Any]:
        """
        图生视频（Image-to-Video）
        
        Args:
            image_url: 图片URL（公网可访问）或本地文件路径
            prompt: 镜头说明文本（可选）
            resolution: 分辨率（480P/720P/1080P）
            duration: 时长（秒，根据模型支持：3/4/5/10）
            model: 模型名称（默认使用配置的模型）
            audio: 是否自动配音（仅wan2.5支持）
            prompt_extend: 是否自动润色Prompt
        
        Returns:
            包含task_id或video_url的字典
        """
        # 检查API Key
        api_key_error = self._check_api_key()
        if api_key_error:
            return api_key_error
        
        # 使用默认模型或指定模型
        model_name = model or self.default_i2v_model
        
        # 验证模型和参数
        if model_name not in self.i2v_models:
            return {
                "error": f"不支持的模型: {model_name}",
                "message": f"支持的I2V模型: {', '.join(self.i2v_models.keys())}"
            }
        
        model_info = self.i2v_models[model_name]
        if duration not in model_info["durations"]:
            return {
                "error": f"模型{model_name}不支持{duration}秒时长",
                "message": f"支持的时长: {model_info['durations']}"
            }
        
        if resolution not in model_info["resolutions"]:
            return {
                "error": f"模型{model_name}不支持{resolution}分辨率",
                "message": f"支持的分辨率: {model_info['resolutions']}"
            }
        
        # 如果模型不支持audio但请求了audio，自动关闭
        if not model_info["supports_audio"] and audio:
            audio = False
        
        # 处理图片：支持URL或base64编码
        # 如果是本地文件路径，尝试读取并转换为base64
        image_data = None
        if image_url and not image_url.startswith("http"):
            # 可能是本地文件路径，尝试读取
            if os.path.exists(image_url):
                try:
                    with open(image_url, "rb") as f:
                        image_data = base64.b64encode(f.read()).decode('utf-8')
                    # 不打印，避免日志过多
                    pass
                except Exception as e:
                    return {
                        "error": f"读取本地图片失败: {str(e)}",
                        "message": "请使用公网可访问的图片URL或配置OSS上传图片"
                    }
        
        # 准备请求
        # 图生视频使用与文生视频相同的端点，但请求体包含img_url
        # 如果 image2video 端点不存在，会回退到 video-synthesis
        url = f"{self.base_url}/services/aigc/video-generation/video-synthesis"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-DashScope-Async": "enable",
            "Content-Type": "application/json"
        }
        
        # 构建请求体
        # 图生视频API也需要使用size参数（格式：1280*720），而不是resolution
        size = self._get_resolution_size(resolution)
        request_body = {
            "model": model_name,
            "input": {},
            "parameters": {
                "size": size,  # 使用size而不是resolution
                "duration": duration,
                "prompt_extend": prompt_extend
            }
        }
        
        # 添加图片（优先使用base64，否则使用URL）
        # 根据DashScope API文档，可以使用data URI格式的img_url
        # 如果image_url是localhost，尝试读取文件并转换为base64
        if image_url and (image_url.startswith("http://localhost") or image_url.startswith("http://127.0.0.1")):
            # 本地URL，尝试读取文件并转换为base64
            try:
                # 从URL提取文件路径
                if "/media/images/" in image_url:
                    filename = image_url.split("/media/images/")[-1]
                    media_dir = os.path.join(os.path.dirname(__file__), "..", "..", "media", "images")
                    local_path = os.path.join(media_dir, filename)
                    if os.path.exists(local_path):
                        with open(local_path, "rb") as f:
                            image_data = base64.b64encode(f.read()).decode('utf-8')
                        file_ext = os.path.splitext(filename)[1].lower() or ".jpg"
                        mime_type_map = {
                            ".jpg": "image/jpeg",
                            ".jpeg": "image/jpeg",
                            ".png": "image/png",
                            ".gif": "image/gif",
                            ".webp": "image/webp"
                        }
                        mime_type = mime_type_map.get(file_ext, "image/jpeg")
                        request_body["input"]["img_url"] = f"data:{mime_type};base64,{image_data}"
                        print(f"[DashScope] 使用base64编码的本地图片（{len(image_data)}字符）")
                    else:
                        print(f"[DashScope] 警告: 本地图片文件不存在: {local_path}，使用原始URL")
                        request_body["input"]["img_url"] = image_url
                else:
                    # 尝试从其他路径读取
                    print(f"[DashScope] 警告: 无法从URL提取文件路径，使用原始URL")
                    request_body["input"]["img_url"] = image_url
            except Exception as e:
                import traceback
                print(f"[DashScope] 读取本地图片失败: {e}")
                print(f"[DashScope] 错误堆栈: {traceback.format_exc()}")
                request_body["input"]["img_url"] = image_url
        elif image_data:
            # 检测图片格式
            file_ext = os.path.splitext(image_url)[1].lower() if image_url else ".jpg"
            mime_type_map = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".webp": "image/webp"
            }
            mime_type = mime_type_map.get(file_ext, "image/jpeg")
            # 使用data URI格式作为img_url
            request_body["input"]["img_url"] = f"data:{mime_type};base64,{image_data}"
        else:
            request_body["input"]["img_url"] = image_url
        
        # 添加prompt（如果提供）
        if prompt:
            request_body["input"]["prompt"] = prompt
        
        # 添加audio参数（如果支持）
        if model_info["supports_audio"]:
            request_body["parameters"]["audio"] = audio
        
        # 检查请求体大小（base64编码的图片可能很大）
        import json
        request_body_str = json.dumps(request_body)
        request_size = len(request_body_str.encode('utf-8'))
        print(f"[DashScope I2V] 请求体大小: {request_size / 1024:.2f} KB")
        
        if request_size > 10 * 1024 * 1024:  # 10MB
            print(f"[DashScope I2V] 警告: 请求体较大（{request_size / 1024 / 1024:.2f} MB），可能导致超时")
        
        # 增加超时时间，特别是对于大图片
        # 图生视频需要上传图片和处理，通常需要更长时间
        if request_size > 5 * 1024 * 1024:  # 大于5MB
            timeout_duration = 120.0  # 2分钟
        elif request_size > 500 * 1024:  # 大于500KB（包含base64图片）
            timeout_duration = 90.0  # 1.5分钟
        else:
            timeout_duration = 60.0  # 1分钟
        print(f"[DashScope I2V] 使用超时时间: {timeout_duration}秒（请求体大小: {request_size / 1024:.2f} KB）")
        
        # 如果使用base64格式，尝试先测试服务器是否支持
        # 如果img_url是base64格式，可能需要使用公网URL
        img_url_value = request_body.get("input", {}).get("img_url", "")
        if img_url_value and img_url_value.startswith("data:"):
            print(f"[DashScope I2V] ⚠️  警告: 使用base64格式的图片")
            print(f"[DashScope I2V] 如果服务器不支持base64，可能会断开连接")
            print(f"[DashScope I2V] 建议: 配置OSS使用公网URL")
        
        try:
            
            # 打印请求信息用于调试
            print(f"[DashScope I2V] ========== API 调用详情 ==========")
            print(f"[DashScope I2V] 完整请求URL: {url}")
            print(f"[DashScope I2V] Base URL: {self.base_url}")
            print(f"[DashScope I2V] API Key已配置: {'是' if self.api_key else '否'}")
            if self.api_key:
                print(f"[DashScope I2V] API Key前10位: {self.api_key[:10]}...")
            print(f"[DashScope I2V] 请求方法: POST")
            print(f"[DashScope I2V] Headers:")
            print(f"  - Authorization: Bearer ***")
            print(f"  - X-DashScope-Async: enable")
            print(f"  - Content-Type: application/json")
            print(f"[DashScope I2V] 请求体结构:")
            print(f"  - model: {request_body.get('model')}")
            print(f"  - input keys: {list(request_body.get('input', {}).keys())}")
            print(f"  - parameters keys: {list(request_body.get('parameters', {}).keys())}")
            if 'img_url' in request_body.get('input', {}):
                img_url_preview = request_body['input']['img_url']
                if img_url_preview.startswith('data:'):
                    print(f"  - img_url: data URI (base64, 长度: {len(img_url_preview)}字符)")
                else:
                    print(f"  - img_url: {img_url_preview[:100]}...")
            print(f"[DashScope I2V] =====================================")
            
            # 添加重试机制（最多重试3次）
            max_retries = 3
            retry_delay = 2  # 重试延迟（秒）
            
            for attempt in range(max_retries):
                try:
                    async with httpx.AsyncClient(timeout=timeout_duration) as client:
                        # 第一步：创建任务
                        if attempt > 0:
                            print(f"[DashScope I2V] 第 {attempt + 1} 次重试...")
                            await asyncio.sleep(retry_delay * attempt)  # 递增延迟
                        else:
                            print(f"[DashScope I2V] 发送请求到DashScope API...")
                            print(f"[DashScope I2V] 目标服务器: dashscope.aliyuncs.com")
                        
                        response = await client.post(url, json=request_body, headers=headers)
                        
                        print(f"[DashScope I2V] ========== API 响应 ==========")
                        print(f"[DashScope I2V] 响应状态码: {response.status_code}")
                        print(f"[DashScope I2V] 响应Headers: {dict(response.headers)}")
                        
                        # 如果是错误响应，打印响应内容
                        if response.status_code != 200:
                            try:
                                error_content = response.json()
                                print(f"[DashScope I2V] 错误响应内容: {error_content}")
                            except:
                                error_text = response.text[:500]  # 限制长度
                                print(f"[DashScope I2V] 错误响应文本: {error_text}")
                        print(f"[DashScope I2V] ===============================")
                        
                        # 处理 502 Bad Gateway 错误（服务器暂时不可用）
                        if response.status_code == 502:
                            error_msg = "DashScope API服务器暂时不可用（502 Bad Gateway）"
                            print(f"[DashScope I2V] {error_msg}")
                            if attempt < max_retries - 1:
                                print(f"[DashScope I2V] 将在 {retry_delay * (attempt + 1)} 秒后重试...")
                                continue
                            else:
                                return {
                                    "error": "API调用失败: 502",
                                    "message": f"{error_msg}，已重试 {max_retries} 次。请稍后再试或检查 DashScope 服务状态。",
                                    "code": "BAD_GATEWAY"
                                }
                        
                        if response.status_code != 200:
                            error_data = response.json() if response.content else {}
                            error_msg = error_data.get("message", response.text)
                            print(f"[DashScope I2V] API调用失败: status_code={response.status_code}, message={error_msg}")
                            
                            # 对于某些错误，不重试
                            if response.status_code in [400, 401, 403, 404]:
                                return {
                                    "error": f"API调用失败: {response.status_code}",
                                    "message": error_msg,
                                    "code": error_data.get("code", "UNKNOWN_ERROR")
                                }
                            
                            # 对于其他错误，尝试重试
                            if attempt < max_retries - 1:
                                print(f"[DashScope I2V] 将在 {retry_delay * (attempt + 1)} 秒后重试...")
                                continue
                            else:
                                return {
                                    "error": f"API调用失败: {response.status_code}",
                                    "message": error_msg,
                                    "code": error_data.get("code", "UNKNOWN_ERROR")
                                }
                        
                        # 成功，跳出重试循环
                        break
                        
                except (httpx.ConnectError, httpx.RemoteProtocolError) as e:
                    print(f"[DashScope I2V] 连接错误（尝试 {attempt + 1}/{max_retries}）: {e}")
                    if attempt < max_retries - 1:
                        print(f"[DashScope I2V] 将在 {retry_delay * (attempt + 1)} 秒后重试...")
                        await asyncio.sleep(retry_delay * (attempt + 1))
                        continue
                    else:
                        # 最后一次重试失败，抛出异常让外层处理
                        raise
            
            # 如果成功，继续处理响应
            result = response.json()
            print(f"[DashScope I2V] API响应成功，获取task_id...")
            
            # 获取task_id
            task_id = result.get("output", {}).get("task_id")
            if not task_id:
                print(f"[DashScope I2V] 警告: 未获取到task_id，响应内容: {result}")
                return {
                    "error": "未获取到task_id",
                    "message": "API响应格式异常",
                    "response": result
                }
            
            print(f"[DashScope I2V] 成功创建视频生成任务: task_id={task_id}")
            
            # 返回task_id，由调用方轮询
            return {
                "success": True,
                "task_id": task_id,
                "status": "PENDING",
                "message": "视频生成任务已创建，请使用task_id轮询状态"
            }
        
        except httpx.TimeoutException as e:
            print(f"[DashScope I2V] 请求超时: {e}")
            print(f"[DashScope I2V] 请求体大小: {request_size / 1024:.2f} KB")
            print(f"[DashScope I2V] 超时时间: {timeout_duration}秒")
            print(f"[DashScope I2V] 可能的原因:")
            print(f"  1. 图片太大，base64编码后请求体较大（{request_size / 1024:.2f} KB）")
            print(f"  2. DashScope服务器处理时间较长")
            print(f"  3. 网络连接较慢")
            print(f"[DashScope I2V] 建议:")
            print(f"  - 压缩图片后再上传（减小文件大小）")
            print(f"  - 使用OSS上传图片，使用公网URL而不是base64")
            print(f"  - 检查网络连接速度")
            return {
                "error": "请求超时",
                "message": f"连接DashScope API超时（已等待{timeout_duration}秒）。请求体较大（{request_size / 1024:.2f} KB），建议：1) 压缩图片 2) 使用OSS上传图片 3) 检查网络连接"
            }
        except httpx.RemoteProtocolError as e:
            print(f"[DashScope I2V] 远程协议错误: {e}")
            print(f"[DashScope I2V] 服务器在发送响应前断开了连接")
            print(f"[DashScope I2V] ⚠️  关键诊断:")
            print(f"  1. 服务器可能不支持base64格式的图片（需要公网URL）")
            print(f"  2. 请求体格式可能不符合API要求")
            print(f"  3. API端点或参数格式可能不正确")
            print(f"[DashScope I2V] 建议:")
            print(f"  - 🔴 最重要：配置OSS上传图片，使用公网URL而不是base64")
            print(f"  - 检查API文档确认图片格式要求")
            print(f"  - 确认API端点和参数格式是否正确")
            return {
                "error": "Server disconnected without sending a response.",
                "message": "DashScope API连接中断。服务器可能不支持base64格式的图片，强烈建议配置OSS使用公网URL。如果问题持续，请检查API文档或联系技术支持。",
                "suggestion": "配置OSS上传图片，获取公网URL后重试",
                "diagnosis": "服务器在接收请求时断开连接，可能是图片格式不支持"
            }
        except httpx.ConnectError as e:
            print(f"[DashScope I2V] 连接错误: {e}")
            print(f"[DashScope I2V] 无法连接到DashScope API: {url}")
            print(f"[DashScope I2V] 可能的原因:")
            print(f"  1. DashScope服务器暂时不可用（502 Bad Gateway）")
            print(f"  2. 网络连接问题（无法访问 dashscope.aliyuncs.com）")
            print(f"  3. 需要配置代理（如果在中国大陆，可能需要代理）")
            print(f"  4. 防火墙阻止了连接")
            print(f"[DashScope I2V] 建议：")
            print(f"  - 等待几分钟后重试（服务器可能正在维护）")
            print(f"  - 检查 https://dashscope.aliyuncs.com 是否可以访问")
            print(f"  - 查看阿里云服务状态页面")
            return {
                "error": "ConnectError",
                "message": "无法连接到DashScope API服务器。这可能是服务器暂时不可用（502错误）。建议：1) 等待几分钟后重试 2) 检查网络连接 3) 查看阿里云服务状态"
            }
        except httpx.RequestError as e:
            print(f"[DashScope I2V] 请求错误: {e}")
            print(f"[DashScope I2V] 错误类型: {type(e).__name__}")
            return {
                "error": str(e),
                "message": f"调用DashScope API失败: {type(e).__name__}"
            }
        except Exception as e:
            import traceback
            print(f"[DashScope I2V] 未知异常: {e}")
            print(f"[DashScope I2V] 异常堆栈: {traceback.format_exc()}")
            return {
                "error": str(e),
                "message": f"调用DashScope API失败: {type(e).__name__}"
            }
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        查询任务状态
        
        Args:
            task_id: 任务ID
        
        Returns:
            任务状态信息，包含video_url（如果完成）
        """
        # 检查API Key
        api_key_error = self._check_api_key()
        if api_key_error:
            return api_key_error
        
        url = f"{self.base_url}/tasks/{task_id}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code != 200:
                    error_data = response.json() if response.content else {}
                    return {
                        "error": f"查询任务失败: {response.status_code}",
                        "message": error_data.get("message", response.text)
                    }
                
                result = response.json()
                output = result.get("output", {})
                task_status = output.get("task_status", "UNKNOWN")
                
                response_data = {
                    "task_id": task_id,
                    "status": task_status,
                    "message": self._get_status_message(task_status)
                }
                
                # 如果任务成功，获取视频URL并下载到本地
                if task_status == "SUCCEEDED":
                    video_url = output.get("video_url")
                    if video_url:
                        # 下载视频到本地
                        local_path = await self._download_video(video_url, task_id)
                        if local_path:
                            response_data.update({
                                "video_url": video_url,
                                "local_path": local_path,
                                "usage": output.get("usage", {})
                            })
                        else:
                            response_data["error"] = "视频下载失败"
                    else:
                        response_data["error"] = "未找到视频URL"
                elif task_status == "FAILED":
                    # 获取详细的错误信息
                    error_message = output.get("message", "任务执行失败")
                    error_code = output.get("code")
                    error_details = output.get("details", {})
                    
                    response_data["error"] = error_message
                    response_data["error_code"] = error_code
                    response_data["error_details"] = error_details
                    response_data["full_output"] = output  # 保存完整输出用于调试
                
                return response_data
        
        except httpx.TimeoutException:
            return {
                "error": "请求超时",
                "message": "查询任务状态超时"
            }
        except Exception as e:
            return {
                "error": str(e),
                "message": f"查询任务状态失败: {type(e).__name__}"
            }
    
    async def _download_video(self, video_url: str, task_id: str) -> Optional[str]:
        """
        下载视频到本地存储
        
        Args:
            video_url: 视频URL
            task_id: 任务ID（用于生成文件名）
        
        Returns:
            本地文件路径，失败返回None
        """
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.get(video_url)
                if response.status_code == 200:
                    # 生成文件名
                    filename = f"{task_id}.mp4"
                    local_path = os.path.join(self.video_storage_dir, filename)
                    
                    # 保存文件
                    with open(local_path, "wb") as f:
                        f.write(response.content)
                    
                    return local_path
                else:
                    return None
        except Exception as e:
            print(f"下载视频失败: {e}")
            return None
    
    def _get_status_message(self, status: str) -> str:
        """获取状态消息"""
        status_messages = {
            "PENDING": "任务等待中",
            "RUNNING": "视频生成中",
            "SUCCEEDED": "视频生成成功",
            "FAILED": "视频生成失败"
        }
        return status_messages.get(status, f"未知状态: {status}")
    
    async def wait_for_task_completion(
        self,
        task_id: str,
        max_wait_time: int = 300,
        poll_interval: int = 10
    ) -> Dict[str, Any]:
        """
        等待任务完成（轮询）
        
        Args:
            task_id: 任务ID
            max_wait_time: 最大等待时间（秒）
            poll_interval: 轮询间隔（秒）
        
        Returns:
            任务结果
        """
        start_time = asyncio.get_event_loop().time()
        
        while True:
            # 检查是否超时
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > max_wait_time:
                return {
                    "error": "任务超时",
                    "message": f"等待任务完成超过{max_wait_time}秒",
                    "task_id": task_id
                }
            
            # 查询任务状态
            status_result = await self.get_task_status(task_id)
            
            if "error" in status_result and status_result["status"] != "PENDING":
                return status_result
            
            if status_result.get("status") == "SUCCEEDED":
                return status_result
            elif status_result.get("status") == "FAILED":
                return status_result
            
            # 等待后继续轮询
            await asyncio.sleep(poll_interval)
    
    async def analyze_script_with_qwen(self, script_content: str) -> Dict[str, Any]:
        """
        使用通义千问分析剧本
        返回结构分析、人物分析、改进建议等内容
        """
        if not self.api_key:
            return {
                "error": "DASHSCOPE_API_KEY未配置",
                "message": "请配置DashScope API Key以使用通义千问分析功能"
            }
        
        # 构建分析提示词
        analysis_prompt = f"""请作为专业的影视剧本分析专家，对以下剧本进行深入分析。

剧本内容：
{script_content}

请提供以下分析（请用自然的中文文本描述，不要使用JSON格式）：

1. **结构分析**：分析剧本的整体结构，包括场景数量、场景类型分布（内景/外景）、剧情节奏、是否有明确的三幕结构等。

2. **人物分析**：分析剧本中的主要角色，包括角色数量、角色关系、角色性格特点、角色动机等。

3. **对白质量**：评估对白的自然度、角色一致性、对话推进剧情的作用等。

4. **优点**：指出剧本的优点和亮点（至少3条）。

5. **不足**：指出剧本的不足之处（至少3条）。

6. **改进建议**：提供具体的、有针对性的改进建议（至少5条），建议要切合剧本实际内容，不要使用固定模板。

请按照以上格式，用清晰的中文文本输出分析结果，每个部分都要详细具体，切合剧本实际内容。"""
        
        try:
            # 使用DashScope SDK调用通义千问
            if DASHSCOPE_SDK_AVAILABLE:
                from dashscope import Generation
                
                # 使用新版 messages 格式
                response = Generation.call(
                    model='qwen-turbo',  # 或 'qwen-plus', 'qwen-max'
                    messages=[
                        {
                            "role": "user",
                            "content": analysis_prompt
                        }
                    ],
                    temperature=0.7,
                    max_tokens=3000
                )
                
                if response.status_code == 200:
                    # 新版API格式：output.choices[0].message.content
                    if hasattr(response, 'output') and hasattr(response.output, 'choices'):
                        if len(response.output.choices) > 0:
                            result_text = response.output.choices[0].message.content
                        else:
                            result_text = ""
                    elif hasattr(response.output, 'text'):
                        result_text = response.output.text
                    else:
                        result_text = str(response.output)
                    print(f"[DashScope] 通义千问返回的原始文本长度: {len(result_text) if result_text else 0}")
                    print(f"[DashScope] 通义千问返回的原始文本前500字符: {result_text[:500] if result_text else 'None'}")
                    # 解析结果文本
                    parsed_result = self._parse_analysis_result(result_text)
                    print(f"[DashScope] 解析后的结果: {parsed_result}")
                    return parsed_result
                else:
                    error_msg = response.message if hasattr(response, 'message') else str(response)
                    print(f"[DashScope] API调用失败: status_code={response.status_code}, message={error_msg}")
                    return {
                        "error": f"API调用失败: {response.status_code}",
                        "message": error_msg
                    }
            else:
                # 使用HTTP API
                return await self._call_qwen_api(analysis_prompt)
        
        except Exception as e:
            return {
                "error": str(e),
                "message": f"调用通义千问API失败: {type(e).__name__}"
            }
    
    async def _call_qwen_api(self, prompt: str) -> Dict[str, Any]:
        """使用HTTP API调用通义千问"""
        url = f"{self.base_url}/services/aigc/text-generation/generation"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 使用新版 messages 格式
        request_body = {
            "model": "qwen-turbo",
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            },
            "parameters": {
                "temperature": 0.7,
                "max_tokens": 3000
            }
        }
        
        try:
            # 禁用代理，避免代理连接问题
            async with httpx.AsyncClient(
                timeout=60.0,
                proxies=None  # 禁用代理
            ) as client:
                response = await client.post(url, json=request_body, headers=headers)
                
                if response.status_code != 200:
                    error_data = response.json() if response.content else {}
                    return {
                        "error": f"API调用失败: {response.status_code}",
                        "message": error_data.get("message", response.text)
                    }
                
                result = response.json()
                output = result.get("output", {})
                
                # 新版API格式：output.choices[0].message.content
                # 旧版API格式：output.text
                if "choices" in output and len(output["choices"]) > 0:
                    text = output["choices"][0].get("message", {}).get("content", "")
                else:
                    text = output.get("text", "")
                
                if text:
                    return self._parse_analysis_result(text)
                else:
                    return {
                        "error": "未获取到分析结果",
                        "message": "API响应格式异常",
                        "response": result
                    }
        
        except httpx.TimeoutException:
            return {
                "error": "请求超时",
                "message": "连接通义千问API超时，请检查网络"
            }
        except Exception as e:
            return {
                "error": str(e),
                "message": f"调用通义千问API失败: {type(e).__name__}"
            }
    
    def _parse_analysis_result(self, result_text: str) -> Dict[str, Any]:
        """解析通义千问返回的分析结果文本"""
        import re
        
        if not result_text or not result_text.strip():
            print("[DashScope] 警告: 通义千问返回的文本为空")
            return {
                "structure_analysis": "未提供结构分析",
                "character_analysis": "未提供人物分析",
                "dialogue_quality": "未提供对白质量分析",
                "strengths": [],
                "weaknesses": [],
                "suggestions": [],
                "raw_analysis": result_text
            }
        
        # 更灵活的正则表达式，支持多种格式：
        # 1. "结构分析："或"1. **结构分析**："或"结构分析"等
        # 2. 支持中英文冒号、空格等变化
        patterns = {
            "structure": [
                r'(?:^|\n)\s*(?:\d+\.\s*)?\*?\*?结构分析\*?\*?[：:]\s*(.*?)(?=\n\s*(?:\d+\.\s*)?\*?\*?(?:人物分析|对白质量|优点|不足|改进建议)|$)',
                r'结构分析[：:]\s*(.*?)(?=\n\s*(?:人物分析|对白质量|优点|不足|改进建议)|$)',
                r'(?:^|\n).*?结构分析.*?[：:]\s*(.*?)(?=\n.*?(?:人物|对白|优点|不足|改进)|$)',
            ],
            "character": [
                r'(?:^|\n)\s*(?:\d+\.\s*)?\*?\*?人物分析\*?\*?[：:]\s*(.*?)(?=\n\s*(?:\d+\.\s*)?\*?\*?(?:对白质量|优点|不足|改进建议)|$)',
                r'人物分析[：:]\s*(.*?)(?=\n\s*(?:对白质量|优点|不足|改进建议)|$)',
                r'(?:^|\n).*?人物分析.*?[：:]\s*(.*?)(?=\n.*?(?:对白|优点|不足|改进)|$)',
            ],
            "dialogue": [
                r'(?:^|\n)\s*(?:\d+\.\s*)?\*?\*?对白质量\*?\*?[：:]\s*(.*?)(?=\n\s*(?:\d+\.\s*)?\*?\*?(?:优点|不足|改进建议)|$)',
                r'对白质量[：:]\s*(.*?)(?=\n\s*(?:优点|不足|改进建议)|$)',
                r'(?:^|\n).*?对白质量.*?[：:]\s*(.*?)(?=\n.*?(?:优点|不足|改进)|$)',
            ],
            "strengths": [
                r'(?:^|\n)\s*(?:\d+\.\s*)?\*?\*?优点\*?\*?[：:]\s*(.*?)(?=\n\s*(?:\d+\.\s*)?\*?\*?(?:不足|改进建议)|$)',
                r'优点[：:]\s*(.*?)(?=\n\s*(?:不足|改进建议)|$)',
                r'(?:^|\n).*?优点.*?[：:]\s*(.*?)(?=\n.*?(?:不足|改进)|$)',
            ],
            "weaknesses": [
                r'(?:^|\n)\s*(?:\d+\.\s*)?\*?\*?不足\*?\*?[：:]\s*(.*?)(?=\n\s*(?:\d+\.\s*)?\*?\*?改进建议|$)',
                r'不足[：:]\s*(.*?)(?=\n\s*改进建议|$)',
                r'(?:^|\n).*?不足.*?[：:]\s*(.*?)(?=\n.*?改进|$)',
            ],
            "suggestions": [
                r'(?:^|\n)\s*(?:\d+\.\s*)?\*?\*?改进建议\*?\*?[：:]\s*(.*?)$',
                r'改进建议[：:]\s*(.*?)$',
                r'(?:^|\n).*?改进建议.*?[：:]\s*(.*?)$',
            ]
        }
        
        def extract_section(key: str) -> str:
            """尝试多种模式提取内容"""
            for pattern in patterns[key]:
                match = re.search(pattern, result_text, re.DOTALL | re.MULTILINE | re.IGNORECASE)
                if match:
                    text = match.group(1).strip()
                    if text and len(text) > 5:  # 确保不是空内容
                        return text
            return ""
        
        # 提取列表项
        def extract_list_items(text: str) -> List[str]:
            if not text:
                return []
            # 匹配数字编号、项目符号等
            items = re.findall(r'[•\-\d+\.、]\s*(.+?)(?=\n[•\-\d+\.、]|$)', text, re.MULTILINE)
            if not items:
                # 如果没有找到列表格式，按段落分割
                items = [line.strip() for line in text.split('\n') if line.strip() and len(line.strip()) > 10]
            return items[:10]  # 最多返回10条
        
        structure_text = extract_section("structure")
        character_text = extract_section("character")
        dialogue_text = extract_section("dialogue")
        strengths_text = extract_section("strengths")
        weaknesses_text = extract_section("weaknesses")
        suggestions_text = extract_section("suggestions")
        
        # 如果所有字段都为空，可能是格式不匹配，尝试按段落分割
        if not structure_text and not character_text and not dialogue_text:
            print(f"[DashScope] 警告: 无法解析通义千问返回的格式，原始文本:\n{result_text[:500]}")
            # 尝试简单分割：按数字编号分割
            sections = re.split(r'\n\s*\d+\.\s*\*?\*?', result_text)
            if len(sections) > 1:
                structure_text = sections[1] if len(sections) > 1 else ""
                character_text = sections[2] if len(sections) > 2 else ""
                dialogue_text = sections[3] if len(sections) > 3 else ""
        
        return {
            "structure_analysis": structure_text or "未提供结构分析",
            "character_analysis": character_text or "未提供人物分析",
            "dialogue_quality": dialogue_text or "未提供对白质量分析",
            "strengths": extract_list_items(strengths_text),
            "weaknesses": extract_list_items(weaknesses_text),
            "suggestions": extract_list_items(suggestions_text),
            "raw_analysis": result_text  # 保留原始文本
        }
    
    async def generate_text_to_image(
        self,
        prompt: str,
        model: str = "wan2.6-t2i",  # 通义万相文生图模型
        # 可选模型：
        # - wan2.6-t2i (通义万相2.6-文生图，最新版本，推荐)
        # - wan2.5-t2i-preview (通义万相2.5-文生图-Preview)
        # - wan2.2-t2i-plus (通义万相2.2-文生图-Plus，更丰富的画面细节)
        # - wan2.2-t2i-flash (通义万相2.2-文生图-Flash，更快的生成速度)
        # - wan2.1-t2i-plus (通义万相2.1-文生图-Plus)
        # - wan2.1-t2i-turbo (通义万相2.1-文生图-Turbo)
        negative_prompt: Optional[str] = None,
        size: str = "1024*1024",
        n: int = 1,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        文生图（Text-to-Image）
        
        Args:
            prompt: 文本提示词
            model: 模型名称，默认 "wan2.6-t2i"（通义万相2.6-文生图，最新版本）
            negative_prompt: 负面提示词（可选）
            size: 图片尺寸，格式 "宽*高"，如 "1024*1024", "720*1280"
            n: 生成图片数量（1-4）
            seed: 随机种子（可选，用于复现结果）
        
        Returns:
            包含图片URL或base64数据的字典
        """
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY未配置，请先配置API Key")
        
        # 优先使用DashScope SDK（如果可用）
        if DASHSCOPE_SDK_AVAILABLE:
            try:
                from dashscope import ImageSynthesis
                import asyncio
                
                # 使用SDK调用（同步调用，需要在线程池中执行）
                def _call_sdk():
                    # 解析尺寸
                    width, height = map(int, size.split('*'))
                    
                    # 构建参数
                    # 注意：SDK的size参数可能需要*格式，保持原样
                    call_params = {
                        "model": model,
                        "prompt": prompt,
                        "n": min(n, 4),
                        "size": f"{width}*{height}"  # SDK使用*格式
                    }
                    
                    # 添加可选参数
                    if negative_prompt:
                        call_params["negative_prompt"] = negative_prompt
                    if seed is not None:
                        call_params["seed"] = seed
                    
                    print(f"[DashScope 文生图] SDK调用参数: {call_params}")
                    call_result = ImageSynthesis.call(**call_params)
                    return call_result
                
                # 在线程池中执行同步调用
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, _call_sdk)
                
                print(f"[DashScope 文生图] SDK响应状态: {result.status_code}")
                print(f"[DashScope 文生图] SDK响应内容: {result}")
                
                if result.status_code == 200:
                    images = []
                    if result.output and result.output.get("results"):
                        for item in result.output["results"]:
                            if hasattr(item, "url") and item.url:
                                images.append(item.url)
                            elif hasattr(item, "b64_image") and item.b64_image:
                                images.append(f"data:image/png;base64,{item.b64_image}")
                    
                    if images:
                        return {
                            "success": True,
                            "images": images
                        }
                    else:
                        return {
                            "success": False,
                            "error": "未返回图片数据"
                        }
                else:
                    error_msg = result.message if hasattr(result, "message") else (result.get("message") if isinstance(result, dict) else "未知错误")
                    print(f"[DashScope 文生图] SDK调用失败，状态码: {result.status_code}, 错误: {error_msg}")
                    return {
                        "success": False,
                        "error": f"SDK调用失败 (状态码: {result.status_code}): {error_msg}"
                    }
            except Exception as e:
                error_msg = str(e)
                # 如果是URL错误，可能是SDK配置问题，直接使用HTTP API
                if "url error" in error_msg.lower() or "InvalidParameter" in error_msg or "InvalidTask" in error_msg:
                    print(f"[DashScope 文生图] SDK调用失败（可能是配置问题）: {e}，使用HTTP API")
                else:
                    print(f"[DashScope 文生图] SDK调用异常: {e}，尝试使用HTTP API")
                    import traceback
                    traceback.print_exc()
        
        # 如果SDK不可用，使用HTTP API
        # 构建请求URL - 使用正确的端点（通义万相文生图）
        # 注意：根据阿里云文档，文生图API端点可能不同，优先使用SDK
        api_url = f"{self.base_url}/services/aigc/image-generation/generation"
        
        # 解析尺寸（支持*和x两种格式）
        if '*' in size:
            width, height = map(int, size.split('*'))
        elif 'x' in size:
            width, height = map(int, size.split('x'))
        else:
            # 默认1024*1024
            width, height = 1024, 1024
        
        # 构建请求体
        # 注意：wan2.6-t2i等新版本模型需要messages格式，且content应该是列表
        # 格式：content可以是字符串列表，或者包含type和text的对象列表
        request_body = {
            "model": model,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            },
            "parameters": {
                "size": f"{width}*{height}",  # HTTP API使用*格式
                "n": min(n, 4)  # 最多4张
            }
        }
        
        if negative_prompt:
            request_body["parameters"]["negative_prompt"] = negative_prompt
        
        if seed is not None:
            request_body["parameters"]["seed"] = seed
        
        # 构建请求头 - 必须启用异步模式
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable"  # 必须启用异步模式
        }
        
        print(f"[DashScope 文生图] 请求URL: {api_url}")
        print(f"[DashScope 文生图] 模型: {model}")
        print(f"[DashScope 文生图] Prompt: {prompt[:100]}...")
        print(f"[DashScope 文生图] 尺寸: {width}*{height}")
        print(f"[DashScope 文生图] 请求体: {request_body}")
        print(f"[DashScope 文生图] 使用异步模式 (X-DashScope-Async: enable)")
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                # 提交任务（异步模式）
                response = await client.post(api_url, json=request_body, headers=headers)
                print(f"[DashScope 文生图] HTTP响应状态: {response.status_code}")
                print(f"[DashScope 文生图] HTTP响应内容: {response.text}")
                
                if response.status_code != 200:
                    # 如果返回错误，尝试解析错误信息
                    try:
                        error_json = response.json()
                        error_msg = error_json.get("message", response.text)
                        error_code = error_json.get("code", "")
                        
                        # 如果错误提示需要prompt而不是messages，尝试使用prompt格式（旧版本模型）
                        if "prompt" in error_msg.lower() and "messages" not in error_msg.lower():
                            print(f"[DashScope 文生图] 检测到需要prompt格式，重试使用prompt格式")
                            request_body_prompt = {
                                "model": model,
                                "input": {
                                    "prompt": prompt
                                },
                                "parameters": {
                                    "size": f"{width}*{height}",
                                    "n": min(n, 4)
                                }
                            }
                            if negative_prompt:
                                request_body_prompt["parameters"]["negative_prompt"] = negative_prompt
                            if seed is not None:
                                request_body_prompt["parameters"]["seed"] = seed
                            
                            response2 = await client.post(api_url, json=request_body_prompt, headers=headers)
                            print(f"[DashScope 文生图] prompt格式重试响应: {response2.status_code} - {response2.text}")
                            
                            if response2.status_code == 200:
                                result = response2.json()
                                # 继续使用result处理（会进入下面的轮询逻辑）
                            else:
                                return {
                                    "success": False,
                                    "error": f"API错误 ({error_code}): {error_msg}",
                                    "error_code": error_code
                                }
                        else:
                            return {
                                "success": False,
                                "error": f"API错误 ({error_code}): {error_msg}",
                                "error_code": error_code
                            }
                    except Exception as parse_error:
                        print(f"[DashScope 文生图] 解析错误信息失败: {parse_error}")
                        return {
                            "success": False,
                            "error": f"HTTP错误 {response.status_code}: {response.text}"
                        }
                
                # 如果上面重试了，result已经在重试逻辑中设置，否则从原始响应获取
                if 'result' not in locals() or result is None:
                    if response.status_code == 200:
                        result = response.json()
                    else:
                        # 如果还是错误，直接返回
                        try:
                            error_json = response.json()
                            error_msg = error_json.get("message", response.text)
                            return {
                                "success": False,
                                "error": f"API调用失败: {error_msg}"
                            }
                        except:
                            return {
                                "success": False,
                                "error": f"API调用失败: HTTP {response.status_code}"
                            }
                
                # 异步模式会返回task_id，需要轮询
                if result.get("output") and result["output"].get("task_id"):
                    task_id = result["output"]["task_id"]
                    print(f"[DashScope 文生图] 任务ID: {task_id}，开始轮询任务状态...")
                    
                    # 轮询任务状态
                    max_attempts = 60  # 最多等待60次（约2分钟）
                    for attempt in range(max_attempts):
                        await asyncio.sleep(2)  # 每2秒查询一次
                        
                        query_url = f"{self.base_url}/tasks/{task_id}"
                        query_headers = {
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        }
                        
                        # 添加重试机制处理连接断开
                        query_response = None
                        retry_count = 3
                        for retry in range(retry_count):
                            try:
                                query_response = await client.get(
                                    query_url, 
                                    headers=query_headers,
                                    timeout=30.0  # 设置超时时间
                                )
                                break  # 成功则跳出重试循环
                            except (httpx.RemoteProtocolError, httpx.TimeoutException, httpx.ConnectError) as e:
                                if retry < retry_count - 1:
                                    print(f"[DashScope 文生图] 查询任务状态时连接错误 (重试 {retry + 1}/{retry_count}): {e}")
                                    await asyncio.sleep(1)  # 等待1秒后重试
                                else:
                                    # 最后一次重试失败，抛出异常
                                    print(f"[DashScope 文生图] 查询任务状态失败，已重试{retry_count}次: {e}")
                                    raise
                        
                        if query_response is None:
                            print(f"[DashScope 文生图] 无法获取任务状态响应")
                            continue
                        
                        if query_response.status_code != 200:
                            print(f"[DashScope 文生图] 查询任务状态失败: {query_response.status_code} - {query_response.text}")
                            continue
                        
                        task_result = query_response.json()
                        task_status = task_result.get("output", {}).get("task_status")
                        print(f"[DashScope 文生图] 任务状态 ({attempt + 1}/{max_attempts}): {task_status}")
                        
                        if task_status == "SUCCEEDED":
                            # 打印完整响应以便调试
                            print(f"[DashScope 文生图] 任务成功，完整响应: {json.dumps(task_result, ensure_ascii=False, indent=2)}")
                            
                            # 任务成功，返回图片URL
                            # DashScope API返回的数据结构：output.choices[].message.content[]
                            output = task_result.get("output", {})
                            
                            # 首先尝试从choices中提取（这是DashScope文生图的正确结构）
                            choices = output.get("choices", [])
                            results = []
                            
                            if choices:
                                # choices是一个数组，每个元素包含message.content
                                for choice in choices:
                                    if isinstance(choice, dict):
                                        message = choice.get("message", {})
                                        if message:
                                            content = message.get("content", [])
                                            if isinstance(content, list):
                                                # content是数组，包含type和image/text对象
                                                for item in content:
                                                    if isinstance(item, dict):
                                                        if item.get("type") == "image":
                                                            # 提取图片URL - 字段名是"image"而不是"url"
                                                            image_url = item.get("image") or item.get("url") or item.get("image_url")
                                                            if image_url:
                                                                results.append({"url": image_url})
                                                                print(f"[DashScope 文生图] 从choices中提取到图片URL: {image_url}")
                                                        elif item.get("type") == "text":
                                                            # 文本内容，忽略
                                                            pass
                                            elif isinstance(content, str):
                                                # content可能是直接的URL字符串
                                                results.append({"url": content})
                                        # 也检查choice中是否有直接的url字段
                                        if "url" in choice:
                                            results.append({"url": choice["url"]})
                                        elif "image_url" in choice:
                                            results.append({"url": choice["image_url"]})
                                        elif "image" in choice:
                                            results.append({"url": choice["image"]})
                            
                            # 如果没有从choices中提取到，尝试其他可能的字段
                            if not results:
                                results = output.get("results", [])
                            
                            if not results:
                                # 尝试直接获取urls字段
                                if "urls" in output:
                                    results = output["urls"] if isinstance(output["urls"], list) else [output["urls"]]
                                # 尝试获取images字段
                                elif "images" in output:
                                    results = output["images"] if isinstance(output["images"], list) else [output["images"]]
                            
                            print(f"[DashScope 文生图] 提取的results: {results}")
                            
                            if results:
                                images = []
                                for item in results:
                                    if isinstance(item, dict):
                                        # 尝试多种可能的字段名
                                        if "url" in item:
                                            images.append(item["url"])
                                        elif "image_url" in item:
                                            images.append(item["image_url"])
                                        elif "b64_image" in item:
                                            images.append(f"data:image/png;base64,{item['b64_image']}")
                                        elif isinstance(item, str):
                                            # 如果item本身就是URL字符串
                                            images.append(item)
                                    elif isinstance(item, str):
                                        # 如果results中的元素直接是URL字符串
                                        images.append(item)
                                    elif hasattr(item, "url"):
                                        images.append(item.url)
                                    elif hasattr(item, "b64_image"):
                                        images.append(f"data:image/png;base64,{item.b64_image}")
                                
                                if images:
                                    print(f"[DashScope 文生图] 生成成功，获得 {len(images)} 张图片")
                                    return {
                                        "success": True,
                                        "images": images,
                                        "task_id": task_id
                                    }
                            
                            # 如果还是没有找到，尝试直接从output中查找
                            # 有些API可能直接返回url字段
                            if "url" in output:
                                url = output["url"]
                                if isinstance(url, str):
                                    images = [url]
                                elif isinstance(url, list):
                                    images = url
                                else:
                                    images = []
                                
                                if images:
                                    print(f"[DashScope 文生图] 从output.url提取到 {len(images)} 张图片")
                                    return {
                                        "success": True,
                                        "images": images,
                                        "task_id": task_id
                                    }
                            
                            # 最后尝试：检查整个task_result的结构
                            print(f"[DashScope 文生图] 无法提取图片数据，完整响应结构: {list(task_result.keys())}")
                            if "output" in task_result:
                                print(f"[DashScope 文生图] output的键: {list(task_result['output'].keys())}")
                            
                            return {
                                "success": False,
                                "error": "任务成功但未返回图片数据",
                                "task_id": task_id,
                                "debug_info": f"output keys: {list(output.keys()) if output else 'None'}"
                            }
                        elif task_status == "FAILED":
                            error_msg = task_result.get("output", {}).get("message", "未知错误")
                            print(f"[DashScope 文生图] 任务失败: {error_msg}")
                            return {
                                "success": False,
                                "error": f"任务失败: {error_msg}",
                                "task_id": task_id
                            }
                        elif task_status in ["PENDING", "RUNNING"]:
                            # 任务进行中，继续等待
                            continue
                    
                    # 超时
                    return {
                        "success": False,
                        "error": f"任务超时（已等待 {max_attempts * 2} 秒），任务ID: {task_id}，请稍后查询",
                        "task_id": task_id
                    }
                elif result.get("output") and result["output"].get("results"):
                    # 同步返回（某些情况下可能直接返回结果）
                    images = []
                    for item in result["output"]["results"]:
                        if isinstance(item, dict):
                            if "url" in item:
                                images.append(item["url"])
                            elif "b64_image" in item:
                                images.append(f"data:image/png;base64,{item['b64_image']}")
                    
                    if images:
                        return {
                            "success": True,
                            "images": images
                        }
                    else:
                        return {
                            "success": False,
                            "error": "未返回图片数据"
                        }
                else:
                    return {
                        "success": False,
                        "error": result.get("message", f"未知响应格式: {result}")
                    }
        
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response else str(e)
            print(f"[DashScope 文生图] HTTP错误: {e.response.status_code} - {error_detail}")
            # 尝试解析错误信息
            try:
                if e.response:
                    error_json = e.response.json()
                    error_msg = error_json.get("message", error_detail)
                    error_code = error_json.get("code", "")
                    return {
                        "success": False,
                        "error": f"HTTP错误 {e.response.status_code} ({error_code}): {error_msg}",
                        "error_code": error_code,
                        "error_message": error_msg
                    }
            except:
                pass
            return {
                "success": False,
                "error": f"HTTP错误 {e.response.status_code}: {error_detail}"
            }
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"[DashScope 文生图] 异常: {str(e)}\n{error_detail}")
            return {
                "success": False,
                "error": f"异常: {str(e)}"
            }
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "qwen-turbo",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ):
        """
        使用通义千问进行聊天对话
        messages格式: [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
        """
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY未配置，请先配置API Key")
        
        # 优先使用DashScope SDK（如果可用）
        if DASHSCOPE_SDK_AVAILABLE:
            try:
                from dashscope import Generation
                import asyncio
                
                # 使用SDK调用（同步调用，需要在线程池中执行）
                def _call_sdk():
                    response = Generation.call(
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens or 2000,
                        result_format="message"
                    )
                    return response
                
                # 在线程池中执行同步调用
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(None, _call_sdk)
                
                if response.status_code == 200:
                    output = response.output
                    choices = output.get("choices", []) if isinstance(output, dict) else []
                    if choices:
                        content = choices[0].get("message", {}).get("content", "")
                        # 返回类似OpenAI格式的响应
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
                        
                        return MockResponse(content)
                    else:
                        raise Exception("API响应格式异常，未找到choices")
                else:
                    error_msg = response.message if hasattr(response, 'message') else str(response)
                    raise Exception(f"API调用失败: {response.status_code}, {error_msg}")
                    
            except ImportError:
                print("[DashScope] SDK不可用，使用HTTP API")
            except Exception as e:
                print(f"[DashScope] SDK调用失败: {e}，尝试使用HTTP API")
        
        # 使用HTTP API（fallback）
        url = f"{self.base_url}/services/aigc/text-generation/generation"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 构建请求体（使用messages格式）
        request_body = {
            "model": model,
            "input": {
                "messages": messages
            },
            "parameters": {
                "temperature": temperature,
                "max_tokens": max_tokens or 2000,
                "result_format": "message"  # 返回消息格式
            }
        }
        
        if stream:
            request_body["parameters"]["incremental_output"] = True
        
        try:
            # 增加超时时间到120秒，因为对话可能需要更长时间
            # 禁用代理，避免代理连接问题
            async with httpx.AsyncClient(
                timeout=120.0,
                proxies=None  # 禁用代理
            ) as client:
                response = await client.post(url, json=request_body, headers=headers)
                
                if response.status_code != 200:
                    error_data = response.json() if response.content else {}
                    error_msg = error_data.get('message', response.text)
                    print(f"[DashScope] API调用失败: status_code={response.status_code}, message={error_msg}")
                    raise Exception(f"API调用失败: {response.status_code}, {error_msg}")
                
                result = response.json()
                
                if stream:
                    # 流式响应需要特殊处理
                    # 这里先返回完整响应，实际流式处理在stream_chat_completion中实现
                    output = result.get("output", {})
                    choices = output.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", "")
                    return ""
                else:
                    output = result.get("output", {})
                    choices = output.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", "")
                        # 返回类似OpenAI格式的响应
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
                        
                        return MockResponse(content)
                    else:
                        print(f"[DashScope] API响应格式异常: {result}")
                        raise Exception("API响应格式异常，未找到choices")
        
        except httpx.TimeoutException:
            print("[DashScope] 连接超时")
            raise Exception("连接通义千问API超时，请检查网络或稍后重试")
        except (httpx.ConnectError, httpx.ProxyError, httpx.RemoteProtocolError) as e:
            print(f"[DashScope] 连接错误: {e}")
            raise Exception(f"无法连接到通义千问API: {str(e)}")
        except Exception as e:
            print(f"[DashScope] 调用失败: {type(e).__name__}: {str(e)}")
            raise Exception(f"调用通义千问API失败: {str(e)}")
    
    async def stream_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "qwen-turbo",
        temperature: float = 0.7
    ):
        """
        流式聊天完成（使用SSE或轮询方式）
        注意：DashScope的流式API可能需要使用SSE，这里先使用轮询方式模拟流式
        """
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY未配置")
        
        # 先获取完整响应，然后逐字符返回（模拟流式）
        # 实际生产环境可以使用SSE或WebSocket
        try:
            response = await self.chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                stream=False
            )
            
            content = response.choices[0].message.content
            
            # 逐字符或逐词返回（模拟流式效果）
            words = content.split()
            for i, word in enumerate(words):
                if i > 0:
                    yield " "
                for char in word:
                    yield char
                    await asyncio.sleep(0.01)  # 控制流式速度
        except Exception as e:
            yield f"错误: {str(e)}"

dashscope_service = DashScopeService()

