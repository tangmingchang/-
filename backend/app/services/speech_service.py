"""
语音识别服务
使用Whisper模型进行语音转文字
"""
import os
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

class SpeechToTextService:
    """语音转文字服务"""
    
    def __init__(self):
        self.whisper_available = False
        self.model = None
        self.model_size = "base"  # base, small, medium, large
        try:
            self._init_model()
        except Exception as e:
            # 捕获所有初始化错误，避免模块导入时崩溃
            print(f"警告: SpeechToTextService初始化失败: {e}")
            self.whisper_available = False
    
    def _init_model(self):
        """初始化Whisper模型"""
        try:
            import whisper
            self.whisper_available = True
            
            # 根据配置加载模型（延迟加载，避免启动时占用太多资源）
            # self.model = whisper.load_model(self.model_size)
            print(f"Whisper已就绪，模型大小: {self.model_size}")
        except ImportError:
            print("警告: Whisper未安装，语音识别功能不可用")
            print("安装方法: pip install openai-whisper")
            self.whisper_available = False
        except Exception as e:
            # 捕获其他可能的错误
            print(f"警告: Whisper初始化时出现错误: {e}")
            self.whisper_available = False
    
    def load_model(self):
        """延迟加载模型"""
        if self.model is None and self.whisper_available:
            try:
                import whisper
                self.model = whisper.load_model(self.model_size)
            except Exception as e:
                print(f"加载Whisper模型错误: {e}")
    
    def transcribe(
        self, 
        audio_path: str,
        language: Optional[str] = None,
        task: str = "transcribe"
    ) -> Dict[str, Any]:
        """
        转写音频文件
        返回带时间戳的文本结果
        """
        if not self.whisper_available:
            return {
                "text": "语音识别功能不可用，请安装Whisper",
                "segments": [],
                "language": language or "unknown"
            }
        
        self.load_model()
        
        if self.model is None:
            return {
                "text": "模型加载失败",
                "segments": [],
                "language": language or "unknown"
            }
        
        try:
            import whisper
            
            # 转写音频
            result = self.model.transcribe(
                audio_path,
                language=language,
                task=task,
                verbose=False
            )
            
            # 格式化结果
            segments = []
            for segment in result.get("segments", []):
                segments.append({
                    "id": segment.get("id", 0),
                    "start": round(segment.get("start", 0), 2),
                    "end": round(segment.get("end", 0), 2),
                    "text": segment.get("text", "").strip()
                })
            
            return {
                "text": result.get("text", "").strip(),
                "segments": segments,
                "language": result.get("language", language or "unknown")
            }
        
        except Exception as e:
            print(f"语音转写错误: {e}")
            return {
                "text": f"转写失败: {str(e)}",
                "segments": [],
                "language": language or "unknown"
            }
    
    def generate_subtitle_file(
        self, 
        segments: List[Dict],
        output_path: str,
        format: str = "srt"
    ) -> str:
        """
        生成字幕文件（SRT格式）
        """
        if format.lower() == "srt":
            srt_content = []
            for i, segment in enumerate(segments, 1):
                start_time = self._format_timestamp(segment.get("start", 0))
                end_time = self._format_timestamp(segment.get("end", 0))
                text = segment.get("text", "")
                
                srt_content.append(f"{i}")
                srt_content.append(f"{start_time} --> {end_time}")
                srt_content.append(text)
                srt_content.append("")
            
            # 写入文件
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(srt_content))
            
            return output_path
        else:
            raise ValueError(f"不支持的字幕格式: {format}")
    
    def _format_timestamp(self, seconds: float) -> str:
        """格式化时间戳为SRT格式 (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def transcribe_with_subtitle(
        self,
        audio_path: str,
        output_dir: str = "./media/audios",
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        转写音频并生成字幕文件
        """
        # 转写
        result = self.transcribe(audio_path, language=language)
        
        # 生成字幕文件
        if result.get("segments"):
            os.makedirs(output_dir, exist_ok=True)
            subtitle_path = os.path.join(
                output_dir,
                f"subtitle_{Path(audio_path).stem}.srt"
            )
            self.generate_subtitle_file(result["segments"], subtitle_path)
            result["subtitle_file"] = subtitle_path
        
        return result
    
    def batch_transcribe(
        self,
        audio_files: List[str],
        language: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        批量转写多个音频文件
        """
        results = []
        for audio_file in audio_files:
            result = self.transcribe(audio_file, language=language)
            result["file"] = audio_file
            results.append(result)
        return results

# 单例模式
speech_service = SpeechToTextService()

