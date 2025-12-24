"""
CLIP图像理解服务
用于图像-文本匹配、场景识别等
"""
import torch
from typing import List, Dict, Optional, Any
from PIL import Image
import numpy as np

class CLIPService:
    """CLIP图像理解服务"""
    
    def __init__(self):
        self.clip_available = False
        self.model = None
        self.preprocess = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._init_clip()
    
    def _init_clip(self):
        """初始化CLIP模型"""
        # CLIP应该通过pip安装: pip install git+https://github.com/openai/CLIP.git
        try:
            import clip
            
            # 加载模型
            self.model, self.preprocess = clip.load("ViT-B/32", device=self.device)
            self.model.eval()
            self.clip_available = True
            print(f"✅ CLIP已加载，设备: {self.device}")
        except ImportError:
            print("警告: CLIP未安装，图像理解功能受限")
            print("安装方法: pip install git+https://github.com/openai/CLIP.git 或运行 python install_local_models.py")
            self.clip_available = False
        except Exception as e:
            print(f"警告: CLIP初始化失败: {e}")
            self.clip_available = False
    
    def match_image_text(
        self,
        image_path: str,
        text_options: List[str]
    ) -> Dict[str, Any]:
        """匹配图像和文本"""
        if not self.clip_available:
            return {"error": "CLIP未安装"}
        
        try:
            import clip  # 确保导入clip模块
            
            # 加载和预处理图像
            image = Image.open(image_path)
            image_input = self.preprocess(image).unsqueeze(0).to(self.device)
            
            # 编码文本
            text_inputs = clip.tokenize(text_options).to(self.device)
            
            # 计算相似度
            with torch.no_grad():
                image_features = self.model.encode_image(image_input)
                text_features = self.model.encode_text(text_inputs)
                
                # 归一化
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
                
                # 计算相似度
                similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
                values, indices = similarity[0].topk(len(text_options))
            
            # 格式化结果
            results = []
            for value, idx in zip(values, indices):
                results.append({
                    "text": text_options[idx],
                    "score": float(value),
                    "rank": int(idx)
                })
            
            return {
                "success": True,
                "matches": sorted(results, key=lambda x: x["score"], reverse=True)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def find_similar_images(
        self,
        query_text: str,
        image_paths: List[str],
        top_k: int = 5
    ) -> Dict[str, Any]:
        """根据文本查找相似图像"""
        if not self.clip_available:
            return {"error": "CLIP未安装"}
        
        try:
            # 编码查询文本
            import clip
            text_input = clip.tokenize([query_text]).to(self.device)
            with torch.no_grad():
                text_features = self.model.encode_text(text_input)
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            
            # 编码所有图像
            similarities = []
            for img_path in image_paths:
                try:
                    image = Image.open(img_path)
                    image_input = self.preprocess(image).unsqueeze(0).to(self.device)
                    with torch.no_grad():
                        image_features = self.model.encode_image(image_input)
                        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                        similarity = float((image_features @ text_features.T)[0][0])
                        similarities.append({
                            "image_path": img_path,
                            "similarity": similarity
                        })
                except Exception as e:
                    print(f"处理图像 {img_path} 失败: {e}")
                    continue
            
            # 排序并返回top_k
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            
            return {
                "success": True,
                "results": similarities[:top_k]
            }
        except Exception as e:
            return {"error": str(e)}

# 全局实例
clip_service = CLIPService()

