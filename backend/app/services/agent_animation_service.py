"""
智能体反馈动画服务
使用Wav2Lip等模型生成说话动画
"""
import os
from typing import Dict, List, Optional, Any
from pathlib import Path

class AgentAnimationService:
    """智能体动画服务"""
    
    def __init__(self):
        self.wav2lip_available = False
        self.sadtalker_available = False
        self.tts_available = False
        self._init_models()
        self.agent_avatar_path = "./media/images/agent_avatar.png"  # 默认助手头像
    
    def _init_models(self):
        """初始化模型"""
        # Wav2Lip模型
        try:
            # Wav2Lip需要从GitHub安装，检查是否可用
            import sys
            # 尝试多个可能的路径
            possible_paths = [
                os.path.join(os.path.dirname(__file__), "../../../Wav2Lip"),
                os.path.join(os.getcwd(), "Wav2Lip"),
                os.path.join(os.path.dirname(os.getcwd()), "Wav2Lip"),
            ]
            
            wav2lip_path = None
            for path in possible_paths:
                abs_path = os.path.abspath(path)
                if os.path.exists(abs_path) and os.path.exists(os.path.join(abs_path, "inference.py")):
                    wav2lip_path = abs_path
                    break
            
            if wav2lip_path:
                sys.path.insert(0, wav2lip_path)
                self.wav2lip_path = wav2lip_path
                
                # 检查模型文件
                checkpoint_path = os.path.join(wav2lip_path, "checkpoints", "wav2lip_gan.pth")
                face_detector_path = os.path.join(wav2lip_path, "face_detection", "detection", "sfd", "s3fd.pth")
                
                if os.path.exists(checkpoint_path):
                    self.wav2lip_available = True
                    print(f"✅ Wav2Lip已完全安装: {wav2lip_path}")
                    print(f"   - 模型文件: {checkpoint_path}")
                    if os.path.exists(face_detector_path):
                        print(f"   - 人脸检测模型: 已安装")
                    else:
                        print(f"   ⚠️  人脸检测模型缺失: {face_detector_path}")
                else:
                    self.wav2lip_available = False
                    print(f"⚠️  Wav2Lip模型文件不存在: {checkpoint_path}")
                    print("   请下载模型权重: https://drive.google.com/file/d/15G3U08c8xsCkOqQxE38Z2XXDnPcOptNk/view?usp=share_link")
            else:
                print("警告: Wav2Lip未安装，说话动画功能受限")
                print("安装方法: git clone https://github.com/Rudrabha/Wav2Lip.git")
                self.wav2lip_available = False
        except Exception as e:
            print(f"警告: Wav2Lip初始化失败: {e}")
            self.wav2lip_available = False
        
        # SadTalker模型
        try:
            # from sadtalker import SadTalker
            # self.sadtalker_model = SadTalker()
            # self.sadtalker_available = True
            pass
        except ImportError:
            print("警告: SadTalker未安装，动画功能受限")
        
        # TTS服务
        try:
            import edge_tts
            self.edge_tts = edge_tts
            self.tts_available = True
            print("✅ Edge TTS已安装")
        except ImportError:
            print("警告: Edge TTS未安装，语音合成功能受限")
            print("安装方法: pip install edge-tts")
            self.tts_available = False
    
    def text_to_speech(self, text: str, output_path: Optional[str] = None) -> str:
        """
        文本转语音
        返回音频文件路径
        """
        if not self.tts_available:
            # 返回占位路径
            return ""
        
        try:
            import asyncio
            import os
            from app.core.config import settings
            
            if output_path is None:
                audio_dir = os.path.join(settings.MEDIA_ROOT, "audios")
                os.makedirs(audio_dir, exist_ok=True)
                output_path = os.path.join(audio_dir, f"tts_{hash(text) % 1000000}.wav")
            
            async def generate():
                voice = "zh-CN-XiaoxiaoNeural"  # 中文语音
                tts = self.edge_tts.Communicate(text, voice)
                await tts.save(output_path)
            
            asyncio.run(generate())
            return output_path
        except Exception as e:
            print(f"TTS错误: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def generate_speaking_animation(
        self,
        text: str,
        avatar_image: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成说话动画
        使用Wav2Lip将语音与头像同步
        """
        if not self.wav2lip_available:
            return {
                "success": False,
                "message": "Wav2Lip未安装",
                "animation_type": "predefined",  # 使用预设动画
                "action": "speak"
            }
        
        try:
            import subprocess
            import os
            from app.core.config import settings
            
            # 步骤1: 生成语音
            audio_path = self.text_to_speech(text)
            if not audio_path:
                return {"success": False, "message": "语音生成失败"}
            
            # 步骤2: 使用Wav2Lip生成动画
            avatar = avatar_image or self.agent_avatar_path
            if not os.path.exists(avatar):
                return {"success": False, "message": f"头像文件不存在: {avatar}"}
            
            # 设置输出路径
            if output_path is None:
                video_dir = os.path.join(settings.MEDIA_ROOT, "videos")
                os.makedirs(video_dir, exist_ok=True)
                output_path = os.path.join(video_dir, f"wav2lip_{hash(text) % 1000000}.mp4")
            
            # 调用Wav2Lip推理脚本
            checkpoint_path = os.path.join(self.wav2lip_path, "checkpoints", "wav2lip_gan.pth")
            if not os.path.exists(checkpoint_path):
                return {"success": False, "message": "Wav2Lip模型文件不存在，请下载模型权重"}
            
            cmd = [
                "python",
                os.path.join(self.wav2lip_path, "inference.py"),
                "--checkpoint_path", checkpoint_path,
                "--face", avatar,
                "--audio", audio_path,
                "--outfile", output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(output_path):
                return {
                    "success": True,
                    "animation_path": output_path,
                    "audio_path": audio_path,
                    "duration": 5.0,  # 估算时长
                    "animation_type": "wav2lip"
                }
            else:
                return {
                    "success": False,
                    "message": f"Wav2Lip生成失败: {result.stderr}",
                    "stdout": result.stdout
                }
        
        except Exception as e:
            print(f"生成说话动画错误: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": str(e)}
    
    def generate_gesture_animation(
        self,
        action: str,
        avatar_image: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成手势动画（点头、摇头等）
        使用SadTalker或预设动画
        """
        # 预设动作映射
        predefined_actions = {
            "nod": {"type": "nod", "duration": 1.0, "description": "点头"},
            "shake": {"type": "shake", "duration": 1.0, "description": "摇头"},
            "smile": {"type": "smile", "duration": 0.5, "description": "微笑"},
            "think": {"type": "think", "duration": 2.0, "description": "思考"},
            "point": {"type": "point", "duration": 1.0, "description": "指向"}
        }
        
        if action in predefined_actions:
            return {
                "success": True,
                "action": predefined_actions[action],
                "animation_type": "predefined",
                "animation_data": f"/media/animations/{action}.gif"  # 预设动画路径
            }
        
        # 如果需要更复杂的动画，使用SadTalker
        if self.sadtalker_available:
            # 使用驱动视频生成动画
            # result = self.sadtalker_model.generate(...)
            pass
        
        return {"success": False, "message": f"未知动作: {action}"}
    
    def generate_feedback_animation(
        self,
        context: str,
        emotion: str = "neutral",
        avatar_image: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        根据上下文生成反馈动画
        根据情绪和上下文选择合适的动画
        """
        # 情绪到动作的映射
        emotion_to_action = {
            "positive": "smile",
            "negative": "shake",
            "thinking": "think",
            "confirming": "nod",
            "explaining": "point"
        }
        
        action = emotion_to_action.get(emotion, "nod")
        
        # 如果上下文包含文本，生成说话动画
        if len(context) > 10:
            return self.generate_speaking_animation(context, avatar_image)
        else:
            return self.generate_gesture_animation(action, avatar_image)
    
    def get_animation_trigger_rules(self) -> Dict[str, str]:
        """
        获取动画触发规则
        定义不同情境下应该触发的动画
        """
        return {
            "user_correct": "smile",
            "user_wrong": "shake",
            "assistant_thinking": "think",
            "assistant_explaining": "speak",
            "highlight_info": "point",
            "waiting_input": "nod"
        }

# 单例模式
agent_animation_service = AgentAnimationService()

