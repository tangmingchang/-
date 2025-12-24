"""
Auto-Editor自动视频剪辑服务
通过命令行调用auto-editor工具
"""
import subprocess
import os
from typing import Dict, Optional, Any, List

class AutoEditorService:
    """Auto-Editor自动剪辑服务"""
    
    def __init__(self):
        self.auto_editor_available = False
        self.auto_editor_path = None
        self._init_auto_editor()
    
    def _init_auto_editor(self):
        """初始化Auto-Editor"""
        # 检查是否安装了auto-editor命令行工具
        try:
            result = subprocess.run(
                ["auto-editor", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                self.auto_editor_available = True
                self.auto_editor_path = "auto-editor"
                print("✅ Auto-Editor命令行工具已安装")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("警告: Auto-Editor未安装，自动剪辑功能受限")
            print("安装方法: pip install auto-editor")
    
    def auto_edit(
        self,
        input_path: str,
        output_path: str,
        method: str = "audio",
        threshold: float = 0.04,
        margin: float = 0.2
    ) -> Dict[str, Any]:
        """自动剪辑视频"""
        if not self.auto_editor_available:
            return {"error": "Auto-Editor未安装"}
        
        try:
            # 构建命令
            cmd = [
                self.auto_editor_path,
                input_path,
                "--output", output_path,
                "--edit", f"{method}:threshold={threshold}",
                "--margin", f"{margin}sec"
            ]
            
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "output_path": output_path,
                    "message": "自动剪辑完成"
                }
            else:
                return {
                    "error": result.stderr,
                    "message": "自动剪辑失败"
                }
        except subprocess.TimeoutExpired:
            return {"error": "剪辑超时"}
        except Exception as e:
            return {"error": str(e)}

# 全局实例
auto_editor_service = AutoEditorService()

