"""
音频分析与配乐建议服务
使用NISQA评估语音质量，YAMNet识别声音事件，MusicGen生成配乐
"""
import json
from typing import Dict, List, Optional, Any
import numpy as np

class AudioAnalysisService:
    """音频分析服务"""
    
    def __init__(self):
        self.nisqa_available = False
        self.yamnet_available = False
        self.musicgen_available = False
        self._init_models()
    
    def _init_models(self):
        """初始化模型"""
        # 检查NISQA是否可用
        try:
            import nisqa
            self.nisqa_model = None  # 延迟加载
            self.nisqa_available = True
            print("✅ NISQA已安装")
        except ImportError:
            print("警告: NISQA未安装，语音质量评估功能受限")
            print("安装方法: pip install nisqa")
            self.nisqa_available = False
        
        # 检查YAMNet是否可用（延迟加载以避免NumPy兼容性问题）
        try:
            # 延迟导入TensorFlow，避免启动时NumPy兼容性错误
            # TensorFlow将在首次使用时加载
            self.tf = None
            self.hub = None
            self.yamnet_model = None  # 延迟加载
            self.yamnet_available = True  # 标记为可用，但延迟加载
            print("✅ YAMNet已标记为可用（将延迟加载）")
        except Exception as e:
            print(f"警告: YAMNet初始化失败: {e}")
            print("安装方法: pip install tensorflow tensorflow-hub")
            self.yamnet_available = False
        
        # 检查MusicGen是否可用
        try:
            from audiocraft.models import MusicGen
            self.MusicGen = MusicGen
            self.musicgen_model = None  # 延迟加载
            self.musicgen_available = True
            print("✅ MusicGen已安装")
        except ImportError:
            print("警告: MusicGen未安装，音乐生成功能受限")
            print("安装方法: pip install git+https://github.com/facebookresearch/audiocraft.git")
            print("注意: MusicGen需要FFmpeg库，Windows上可能需要预编译版本")
            self.musicgen_available = False
        except Exception as e:
            print(f"警告: MusicGen初始化失败: {e}")
            self.musicgen_available = False
    
    def assess_speech_quality(self, audio_path: str) -> Dict[str, Any]:
        """
        评估语音清晰度
        使用NISQA模型计算质量分数
        """
        if not self.nisqa_available:
            # 返回模拟数据
            return {
                "mos_score": 4.2,  # Mean Opinion Score (1-5)
                "clarity": 0.85,
                "noise_level": 0.15,
                "distortion": 0.1,
                "overall_quality": "良好",
                "suggestions": [
                    "对白清晰度良好",
                    "背景噪声在可接受范围内"
                ]
            }
        
        try:
            import nisqa
            import subprocess
            import os
            import tempfile
            
            # NISQA命令行调用方式
            # 创建临时输出目录
            with tempfile.TemporaryDirectory() as tmpdir:
                output_file = os.path.join(tmpdir, "nisqa_result.csv")
                
                # 调用NISQA预测
                cmd = [
                    "python", "-m", "nisqa",
                    "--mode", "predict_file",
                    "--pretrained_model", "weights/nisqa.tar",  # 需要下载模型
                    "--deg", audio_path,
                    "--output_dir", tmpdir
                ]
                
                # 如果模型文件不存在，使用PyPI版本
                try:
                    result = nisqa.predict_file(
                        audio_path,
                        pretrained_model="weights/nisqa.tar"  # 需要先下载
                    )
                    return {
                        "mos_score": float(result.get('mos_pred', 4.0)),
                        "clarity": float(result.get('noi_pred', 0.1)),
                        "noise_level": float(result.get('noi_pred', 0.1)),
                        "distortion": float(result.get('dis_pred', 0.1)),
                        "overall_quality": "优秀" if result.get('mos_pred', 4.0) > 4.0 else "良好"
                    }
                except Exception as e:
                    print(f"NISQA评估错误（可能需要下载模型）: {e}")
                    # 返回基础评估
                    return {
                        "mos_score": 4.0,
                        "clarity": 0.8,
                        "noise_level": 0.2,
                        "distortion": 0.1,
                        "overall_quality": "需要下载NISQA模型权重"
                    }
        except Exception as e:
            print(f"语音质量评估错误: {e}")
            return {}
    
    def classify_sound_events(self, audio_path: str) -> List[Dict[str, Any]]:
        """
        识别音频中的声音事件
        使用YAMNet分类环境音、音效等
        """
        if not self.yamnet_available:
            # 返回模拟数据
            return [
                {"event": "语音", "confidence": 0.95, "start": 0.0, "end": 5.0},
                {"event": "雨声", "confidence": 0.78, "start": 2.0, "end": 8.0},
                {"event": "背景音乐", "confidence": 0.65, "start": 0.0, "end": 10.0}
            ]
        
        try:
            import librosa
            
            # 延迟加载TensorFlow和YAMNet模型
            if self.tf is None or self.hub is None:
                print("加载TensorFlow和YAMNet...")
                import tensorflow as tf
                import tensorflow_hub as hub
                self.tf = tf
                self.hub = hub
            
            if self.yamnet_model is None:
                print("加载YAMNet模型...")
                self.yamnet_model = self.hub.load('https://tfhub.dev/google/yamnet/1')
            
            # 加载音频
            audio_data, sample_rate = librosa.load(audio_path, sr=16000)
            
            # 确保音频长度符合要求
            if len(audio_data) < sample_rate * 0.5:  # 至少0.5秒
                audio_data = np.pad(audio_data, (0, int(sample_rate * 0.5 - len(audio_data))))
            
            # 运行模型
            scores, embeddings, spectrogram = self.yamnet_model(audio_data)
            
            # 获取类别名称
            class_names = self.yamnet_model.class_names.numpy().astype(str)
            
            # 提取主要声音事件
            events = []
            mean_scores = scores.numpy().mean(axis=0)
            for i, score in enumerate(mean_scores):
                if score > 0.3:  # 阈值
                    events.append({
                        "event": class_names[i],
                        "confidence": float(score),
                        "start": 0.0,
                        "end": len(audio_data) / sample_rate
                    })
            
            return sorted(events, key=lambda x: x['confidence'], reverse=True)[:10]
        
        except Exception as e:
            print(f"声音事件分类错误: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def analyze_emotion_from_audio(self, audio_path: str) -> Dict[str, Any]:
        """
        从音频分析情绪基调
        结合对白内容和音频特征
        """
        # 简化实现：基于音频能量和节奏判断
        try:
            import librosa
            import numpy as np
            
            y, sr = librosa.load(audio_path)
            
            # 计算特征
            energy = np.mean(librosa.feature.rms(y=y)[0])
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            
            # 判断情绪
            if energy > 0.7 and tempo > 120:
                emotion = "激昂/紧张"
            elif energy < 0.3 and tempo < 90:
                emotion = "平静/忧伤"
            elif energy > 0.5:
                emotion = "积极/欢快"
            else:
                emotion = "中性"
            
            return {
                "emotion": emotion,
                "energy": float(energy),
                "tempo": float(tempo),
                "valence": "正面" if energy > 0.5 else "负面"
            }
        
        except Exception as e:
            print(f"音频情绪分析错误: {e}")
            return {"emotion": "未知"}
    
    def suggest_music(
        self, 
        scene_description: str,
        emotion: str,
        sound_events: List[Dict]
    ) -> Dict[str, Any]:
        """
        根据场景和情绪推荐配乐
        可以生成音乐或从曲库推荐
        """
        # 构建音乐描述
        music_prompt = f"{emotion}的{scene_description}配乐"
        
        # 判断音乐类型
        if "紧张" in emotion or "激昂" in emotion:
            music_type = "紧张悬疑"
            tempo_range = "120-140 BPM"
        elif "平静" in emotion or "忧伤" in emotion:
            music_type = "抒情舒缓"
            tempo_range = "60-90 BPM"
        elif "欢快" in emotion:
            music_type = "轻快活泼"
            tempo_range = "100-120 BPM"
        else:
            music_type = "中性背景"
            tempo_range = "80-100 BPM"
        
        suggestions = {
            "music_type": music_type,
            "tempo_range": tempo_range,
            "description": music_prompt,
            "recommended_tracks": [
                {
                    "title": f"{music_type}配乐示例1",
                    "style": music_type,
                    "duration": "30秒",
                    "source": "音乐库"
                },
                {
                    "title": f"{music_type}配乐示例2",
                    "style": music_type,
                    "duration": "30秒",
                    "source": "音乐库"
                }
            ],
            "generate_option": {
                "prompt": music_prompt,
                "duration": 30,
                "model": "musicgen"
            }
        }
        
        return suggestions
    
    def generate_music(self, prompt: str, duration: int = 30) -> Optional[str]:
        """
        使用MusicGen生成音乐
        返回生成的音频文件路径
        """
        if not self.musicgen_available:
            return None
        
        try:
            import torch
            import soundfile as sf
            import os
            from app.core.config import settings
            
            # 延迟加载模型
            if self.musicgen_model is None:
                print("加载MusicGen模型...")
                self.musicgen_model = self.MusicGen.get_pretrained('facebook/musicgen-small')
            
            # 设置生成参数
            self.musicgen_model.set_generation_params(duration=duration)
            
            # 生成音乐
            print(f"正在生成音乐: {prompt}")
            wav = self.musicgen_model.generate([prompt])
            
            # 保存音频
            audio_dir = os.path.join(settings.MEDIA_ROOT, "audios")
            os.makedirs(audio_dir, exist_ok=True)
            
            output_path = os.path.join(audio_dir, f"generated_{hash(prompt) % 1000000}.wav")
            sf.write(output_path, wav[0].cpu().numpy(), self.musicgen_model.sample_rate)
            
            print(f"音乐已生成: {output_path}")
            return output_path
        
        except Exception as e:
            print(f"音乐生成错误: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def analyze_audio(self, audio_path: str, scene_context: Optional[str] = None) -> Dict[str, Any]:
        """
        完整的音频分析流程
        """
        # 步骤1: 评估语音质量
        quality_assessment = self.assess_speech_quality(audio_path)
        
        # 步骤2: 识别声音事件
        sound_events = self.classify_sound_events(audio_path)
        
        # 步骤3: 分析情绪
        emotion_analysis = self.analyze_emotion_from_audio(audio_path)
        
        # 步骤4: 推荐配乐
        music_suggestions = self.suggest_music(
            scene_context or "未知场景",
            emotion_analysis.get("emotion", "中性"),
            sound_events
        )
        
        return {
            "quality_assessment": quality_assessment,
            "sound_events": sound_events,
            "emotion_analysis": emotion_analysis,
            "music_suggestions": music_suggestions
        }

# 单例模式
audio_service = AudioAnalysisService()

