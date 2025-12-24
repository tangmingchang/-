"""
情绪分析与可视化反馈服务
结合文本和语音情绪分析，生成可视化图表
"""
import json
from typing import Dict, List, Optional, Any
import numpy as np

class EmotionAnalysisService:
    """情绪分析服务"""
    
    def __init__(self):
        self.text_emotion_model = None
        self.speech_emotion_model = None
        self._init_models()
    
    def _init_models(self):
        """初始化情绪分析模型"""
        # 文本情绪分析模型（基于BERT/RoBERTa）
        try:
            # from transformers import pipeline
            # self.text_emotion_model = pipeline(
            #     "text-classification",
            #     model="bert-base-chinese",
            #     task="sentiment-analysis"
            # )
            pass
        except ImportError:
            print("警告: transformers未安装，文本情绪分析功能受限")
        
        # 语音情绪分析模型（SpeechBrain）
        try:
            # from speechbrain.inference.classifiers import EncoderClassifier
            # self.speech_emotion_model = EncoderClassifier.from_hparams(
            #     source="speechbrain/emotion-recognition-wav2vec2-IEMOCAP"
            # )
            pass
        except ImportError:
            print("警告: SpeechBrain未安装，语音情绪分析功能受限")
    
    def analyze_text_emotion(self, text: str) -> Dict[str, Any]:
        """
        分析文本情绪
        对剧本或对白逐句分类情感类型
        """
        # 简化的情绪分析（实际应使用预训练模型）
        emotions = {
            "喜悦": 0,
            "愤怒": 0,
            "忧伤": 0,
            "恐惧": 0,
            "惊讶": 0,
            "中性": 0
        }
        
        # 关键词匹配（简化版）
        positive_words = ["高兴", "快乐", "开心", "兴奋", "满意"]
        negative_words = ["悲伤", "痛苦", "难过", "失望", "沮丧"]
        anger_words = ["愤怒", "生气", "恼火", "不满"]
        fear_words = ["害怕", "恐惧", "担心", "紧张"]
        
        text_lower = text.lower()
        
        for word in positive_words:
            if word in text_lower:
                emotions["喜悦"] += 1
        
        for word in negative_words:
            if word in text_lower:
                emotions["忧伤"] += 1
        
        for word in anger_words:
            if word in text_lower:
                emotions["愤怒"] += 1
        
        for word in fear_words:
            if word in text_lower:
                emotions["恐惧"] += 1
        
        # 如果没有匹配到，设为中性
        if sum(emotions.values()) == 0:
            emotions["中性"] = 1
        
        # 归一化
        total = sum(emotions.values())
        if total > 0:
            emotions = {k: v / total for k, v in emotions.items()}
        
        # 确定主要情绪
        dominant_emotion = max(emotions.items(), key=lambda x: x[1])
        
        return {
            "emotions": emotions,
            "dominant_emotion": dominant_emotion[0],
            "confidence": dominant_emotion[1],
            "valence": "正面" if dominant_emotion[0] in ["喜悦", "惊讶"] else "负面" if dominant_emotion[0] != "中性" else "中性"
        }
    
    def analyze_speech_emotion(self, audio_path: str) -> Dict[str, Any]:
        """
        分析语音情绪
        使用语音情感识别模型
        """
        if not self.speech_emotion_model:
            # 返回模拟数据
            return {
                "emotion": "中性",
                "confidence": 0.75,
                "arousal": 0.5,  # 激活度
                "valence": 0.5   # 效价
            }
        
        try:
            # 实际调用SpeechBrain模型
            # out_prob, score, index, text_lab = self.speech_emotion_model.classify_file(audio_path)
            # return {
            #     "emotion": text_lab[0],
            #     "confidence": float(out_prob[0]),
            #     "arousal": 0.5,
            #     "valence": 0.5
            # }
            pass
        except Exception as e:
            print(f"语音情绪分析错误: {e}")
            return {}
    
    def analyze_script_emotions(self, script_content: str, scenes: List[Dict]) -> List[Dict[str, Any]]:
        """
        分析剧本各场景的情绪走势
        """
        emotion_timeline = []
        
        for i, scene in enumerate(scenes):
            # 提取场景文本
            scene_text = ""
            if "dialogue" in scene:
                for dialogue in scene.get("dialogue", []):
                    scene_text += " ".join(dialogue.get("lines", []))
            if "action" in scene:
                scene_text += " ".join(scene.get("action", []))
            
            # 分析情绪
            emotion_result = self.analyze_text_emotion(scene_text)
            
            emotion_timeline.append({
                "scene_id": i + 1,
                "scene_title": scene.get("title", f"场景{i+1}"),
                "emotion": emotion_result.get("dominant_emotion", "中性"),
                "confidence": emotion_result.get("confidence", 0.5),
                "valence": emotion_result.get("valence", "中性"),
                "emotion_distribution": emotion_result.get("emotions", {})
            })
        
        return emotion_timeline
    
    def generate_emotion_visualization_data(
        self, 
        emotion_timeline: List[Dict],
        emotion_distribution: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        生成情绪可视化数据
        用于绘制雷达图、热力图等
        """
        # 雷达图数据（整体情绪分布）
        radar_data = {
            "categories": list(emotion_distribution.keys()),
            "values": list(emotion_distribution.values()),
            "max_value": 1.0
        }
        
        # 热力图数据（时间序列情绪）
        heatmap_data = {
            "time_points": [f"场景{i+1}" for i in range(len(emotion_timeline))],
            "emotions": ["喜悦", "愤怒", "忧伤", "恐惧", "惊讶", "中性"],
            "intensity_matrix": []
        }
        
        # 构建强度矩阵
        for scene in emotion_timeline:
            row = []
            dist = scene.get("emotion_distribution", {})
            for emotion in heatmap_data["emotions"]:
                row.append(dist.get(emotion, 0))
            heatmap_data["intensity_matrix"].append(row)
        
        # 时间线数据（情绪曲线）
        timeline_data = {
            "scenes": [s.get("scene_id") for s in emotion_timeline],
            "emotions": [s.get("emotion") for s in emotion_timeline],
            "valence_scores": [
                1 if s.get("valence") == "正面" else -1 if s.get("valence") == "负面" else 0
                for s in emotion_timeline
            ],
            "confidence_scores": [s.get("confidence", 0.5) for s in emotion_timeline]
        }
        
        return {
            "radar_chart": radar_data,
            "heatmap": heatmap_data,
            "timeline": timeline_data
        }
    
    def analyze_emotions(
        self, 
        script_content: Optional[str] = None,
        scenes: Optional[List[Dict]] = None,
        audio_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        完整的情绪分析流程
        结合文本和语音分析
        """
        results = {}
        
        # 文本情绪分析
        if script_content:
            text_emotion = self.analyze_text_emotion(script_content)
            results["text_emotion"] = text_emotion
        
        # 场景情绪走势
        if scenes:
            scene_emotions = self.analyze_script_emotions(script_content or "", scenes)
            results["scene_emotions"] = scene_emotions
            
            # 计算整体情绪分布
            emotion_distribution = {}
            for scene in scene_emotions:
                dist = scene.get("emotion_distribution", {})
                for emotion, value in dist.items():
                    emotion_distribution[emotion] = emotion_distribution.get(emotion, 0) + value
            
            # 归一化
            total = sum(emotion_distribution.values())
            if total > 0:
                emotion_distribution = {k: v / total for k, v in emotion_distribution.items()}
            
            results["overall_distribution"] = emotion_distribution
            
            # 生成可视化数据
            visualization_data = self.generate_emotion_visualization_data(
                scene_emotions,
                emotion_distribution
            )
            results["visualization"] = visualization_data
        
        # 语音情绪分析
        if audio_path:
            speech_emotion = self.analyze_speech_emotion(audio_path)
            results["speech_emotion"] = speech_emotion
        
        return results

# 单例模式
emotion_service = EmotionAnalysisService()

