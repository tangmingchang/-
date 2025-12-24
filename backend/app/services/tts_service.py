"""
Coqui TTS文本转语音服务
提供高质量的TTS功能
"""
import os
from typing import Dict, Optional, Any

class TTSService:
    """Coqui TTS服务"""
    
    def __init__(self):
        self.tts_available = False
        self.tts = None
        self._tts_model_name = None
        self._init_error = None
        self._init_tts()
    
    def _init_tts(self):
        """初始化TTS"""
        # TTS应该通过pip安装: pip install TTS
        try:
            # 先检查torchaudio是否可用（延迟检查，避免启动时错误）
            # torchaudio可能在运行时才加载，所以先不检查
            
            from TTS.api import TTS
            
            # 初始化TTS（使用多语言模型，延迟加载以避免启动时下载）
            # 注意：首次使用会下载模型，可能需要时间
            self.tts_available = True
            self._tts_model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
            print("✅ Coqui TTS已加载（模型将在首次使用时下载）")
        except ImportError as ie:
            print("警告: Coqui TTS未安装，TTS功能受限")
            print("安装方法: pip install TTS 或运行 python install_local_models.py")
            print(f"导入错误: {ie}")
            self.tts_available = False
        except Exception as e:
            # 捕获所有其他异常，但不阻止服务启动
            error_msg = str(e)
            if "torchaudio" in error_msg.lower() or "libtorchaudio" in error_msg.lower():
                print(f"警告: TTS初始化失败（torchaudio问题）: {error_msg[:100]}")
                print("提示: torchaudio将在首次使用时尝试加载，如果失败请重新安装: pip install torchaudio --upgrade")
            else:
                print(f"警告: TTS初始化失败: {error_msg[:100]}")
            # 仍然标记为可用，让它在实际使用时再处理错误
            self.tts_available = True  # 允许延迟加载
            self._init_error = error_msg
    
    def synthesize(
        self,
        text: str,
        output_path: str,
        language: str = "zh",
        speaker_wav: Optional[str] = None
    ) -> Dict[str, Any]:
        """合成语音"""
        if not self.tts_available:
            return {"error": "TTS未安装"}
        
        try:
            # 延迟加载TTS模型（首次使用时）
            if self.tts is None:
                # 检查是否有初始化错误
                if self._init_error:
                    return {"error": f"TTS初始化失败: {self._init_error}"}
                
                from TTS.api import TTS
                try:
                    self.tts = TTS(self._tts_model_name, gpu=False)
                except Exception as e:
                    # 如果torchaudio问题，尝试提示
                    if "torchaudio" in str(e).lower() or "libtorchaudio" in str(e).lower():
                        return {"error": f"torchaudio加载失败，请重新安装: pip install torchaudio --upgrade. 错误: {str(e)[:200]}"}
                    raise
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
            
            # 合成语音
            if speaker_wav:
                # 使用语音克隆
                self.tts.tts_to_file(
                    text=text,
                    file_path=output_path,
                    speaker_wav=speaker_wav,
                    language=language
                )
            else:
                # 使用默认声音
                self.tts.tts_to_file(
                    text=text,
                    file_path=output_path,
                    language=language
                )
            
            return {
                "success": True,
                "output_path": output_path
            }
        except Exception as e:
            return {"error": str(e)}

# 全局实例
tts_service = TTSService()

