"""
Chroma向量数据库服务
用于知识库的向量检索
"""
import os
from typing import List, Dict, Optional, Any

class ChromaService:
    """Chroma向量数据库服务"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.chroma_available = False
        self.client = None
        self.collection = None
        self.persist_directory = persist_directory
        self._init_chroma()
    
    def _init_chroma(self):
        """初始化Chroma"""
        try:
            import chromadb
            from chromadb.config import Settings
            
            # 创建持久化目录
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # 创建客户端（使用新API）
            self.client = chromadb.PersistentClient(
                path=self.persist_directory
            )
            
            # 获取或创建集合
            self.collection = self.client.get_or_create_collection(
                name="knowledge_base",
                metadata={"description": "影视制作教育知识库"}
            )
            
            self.chroma_available = True
            print("✅ Chroma向量数据库已初始化")
        except ImportError:
            print("警告: Chroma未安装，向量检索功能受限")
            print("安装方法: pip install chromadb")
            self.chroma_available = False
        except Exception as e:
            print(f"警告: Chroma初始化失败: {e}")
            self.chroma_available = False
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict]] = None,
        ids: Optional[List[str]] = None
    ) -> bool:
        """添加文档到向量数据库"""
        if not self.chroma_available or not self.collection:
            return False
        
        try:
            if ids is None:
                import uuid
                ids = [str(uuid.uuid4()) for _ in documents]
            
            if metadatas is None:
                metadatas = [{}] * len(documents)
            
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            return True
        except Exception as e:
            print(f"添加文档失败: {e}")
            return False
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        where: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """搜索相似文档"""
        if not self.chroma_available or not self.collection:
            return []
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where
            )
            
            # 格式化结果
            formatted_results = []
            if results["documents"] and len(results["documents"][0]) > 0:
                for i in range(len(results["documents"][0])):
                    full_text = results["documents"][0][i]
                    metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                    distance = results["distances"][0][i] if results["distances"] else None
                    filename = metadata.get("filename", "") if metadata else ""
                    
                    # 过滤掉包含PDF元数据的结果
                    if '%PDF' in full_text or 'obj' in full_text[:100] or 'Linearized' in full_text[:100]:
                        continue
                    
                    # 过滤掉测试文本
                    if '这是一个关于影视制作的测试文本' in full_text:
                        continue
                    
                    # 过滤掉过短或主要是乱码的内容
                    if len(full_text.strip()) < 20:
                        continue
                    
                    # 计算文件名匹配度（如果查询词在文件名中，降低distance以提高优先级）
                    filename_match_bonus = 0
                    if filename and query:
                        query_lower = query.lower()
                        filename_lower = filename.lower()
                        # 如果查询词完全匹配文件名，大幅降低distance
                        if query_lower in filename_lower:
                            filename_match_bonus = -0.5  # 降低distance，提高优先级
                    
                    adjusted_distance = (distance if distance is not None else 999) + filename_match_bonus
                    
                    formatted_results.append({
                        "id": results["ids"][0][i],
                        "document": full_text,  # 完整内容
                        "metadata": metadata,
                        "distance": adjusted_distance,
                        "original_distance": distance
                    })
                
                # 按调整后的距离排序（距离越小越相关），只返回最相关的3个结果
                formatted_results.sort(key=lambda x: x.get("distance", 999) if x.get("distance") is not None else 999)
                formatted_results = formatted_results[:3]
            
            return formatted_results
        except Exception as e:
            print(f"搜索失败: {e}")
            return []
    
    def delete(self, ids: Optional[List[str]] = None, where: Optional[Dict] = None):
        """删除文档"""
        if not self.chroma_available or not self.collection:
            return False
        
        try:
            self.collection.delete(ids=ids, where=where)
            return True
        except Exception as e:
            print(f"删除文档失败: {e}")
            return False
    
    def get_collection_info(self) -> Dict[str, Any]:
        """获取集合信息"""
        if not self.chroma_available or not self.collection:
            return {"error": "Chroma未初始化"}
        
        try:
            count = self.collection.count()
            return {
                "name": self.collection.name,
                "count": count,
                "metadata": self.collection.metadata
            }
        except Exception as e:
            return {"error": str(e)}

# 全局实例
chroma_service = ChromaService()

