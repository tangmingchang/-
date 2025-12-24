"""
WhisperX增强语音识别服务
提供更准确的语音识别和说话人分离
"""
import os
from typing import Dict, List, Optional, Any

class WhisperXService:
    """WhisperX语音识别服务"""
    
    def __init__(self):
        self.whisperx_available = False
        self.model = None
        self.model_size = "base"
        self._init_whisperx()
    
    def _init_whisperx(self):
        """初始化WhisperX"""
        # WhisperX应该通过pip安装: pip install whisperx
        try:
            import whisperx
            self.whisperx = whisperx
            self.whisperx_available = True
            print(f"✅ WhisperX已安装，模型大小: {self.model_size}")
        except ImportError:
            print("警告: WhisperX未安装，增强语音识别功能受限")
            print("安装方法: pip install whisperx 或运行 python install_local_models.py")
            self.whisperx_available = False
    
    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        batch_size: int = 16,
        align: bool = True,
        diarize: bool = False
    ) -> Dict[str, Any]:
        """转写音频（带时间戳和说话人分离）"""
        if not self.whisperx_available:
            return {
                "error": "WhisperX未安装",
                "text": "",
                "segments": []
            }
        
        try:
            # 加载模型
            model = self.whisperx.load_model(self.model_size, "cpu", compute_type="int8")
            
            # 转写
            audio = self.whisperx.load_audio(audio_path)
            result = model.transcribe(audio, batch_size=batch_size, language=language)
            
            # 对齐（获取词级时间戳）
            if align:
                model_a, metadata = self.whisperx.load_align_model(language_code=language or result["language"], device="cpu")
                result = self.whisperx.align(result["segments"], model_a, metadata, audio, "cpu", return_char_alignments=False)
            
            # 说话人分离
            if diarize:
                diarize_model = self.whisperx.DiarizationPipeline(use_auth_token=None, device="cpu")
                diarize_segments = diarize_model(audio)
                result = self.whisperx.assign_word_speakers(diarize_segments, result)
            
            return {
                "success": True,
                "text": " ".join([seg["text"] for seg in result["segments"]]),
                "segments": result["segments"],
                "language": result.get("language", language or "unknown")
            }
        except Exception as e:
            return {
                "error": str(e),
                "text": "",
                "segments": []
            }

# 全局实例
whisperx_service = WhisperXService()

