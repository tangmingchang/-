"""
知识库服务 - 文档管理和向量检索
集成Chroma向量数据库
"""
import os
import aiofiles
from pathlib import Path
from typing import List, Optional
from app.core.config import settings

# 尝试导入Chroma服务
try:
    from app.services.chroma_service import chroma_service
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    chroma_service = None

class KnowledgeService:
    """知识库服务"""
    
    def __init__(self):
        self.knowledge_base_path = Path(settings.KNOWLEDGE_BASE_PATH)
        self.vector_db_path = Path(settings.VECTOR_DB_PATH)
        
        # 使用Chroma服务（如果可用）
        self.chroma_service = chroma_service if CHROMA_AVAILABLE else None
    
    async def save_document(
        self,
        filename: str,
        content: bytes,
        metadata: Optional[dict] = None
    ) -> dict:
        """保存文档"""
        file_path = self.knowledge_base_path / filename
        
        # 保存文件
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # 提取文本内容（根据文件类型使用不同的解析方法）
        text_content = ""
        file_ext = Path(filename).suffix.lower()
        
        if file_ext == '.pdf':
            # PDF文件：使用PDF解析库提取文本
            try:
                try:
                    from pypdf import PdfReader
                    import io
                    pdf_reader = PdfReader(io.BytesIO(content))
                    text_parts = []
                    # 只提取前10页，避免太长
                    for page_num, page in enumerate(pdf_reader.pages[:10]):
                        try:
                            page_text = page.extract_text()
                            if page_text and page_text.strip():
                                text_parts.append(page_text.strip())
                        except:
                            continue
                    text_content = "\n\n".join(text_parts)
                except ImportError:
                    try:
                        import PyPDF2
                        import io
                        pdf_file = io.BytesIO(content)
                        pdf_reader = PyPDF2.PdfReader(pdf_file)
                        text_parts = []
                        for page_num in range(min(10, len(pdf_reader.pages))):
                            try:
                                page = pdf_reader.pages[page_num]
                                page_text = page.extract_text()
                                if page_text and page_text.strip():
                                    text_parts.append(page_text.strip())
                            except:
                                continue
                        text_content = "\n\n".join(text_parts)
                    except ImportError:
                        print("警告: PDF解析库未安装，无法提取PDF文本")
                        text_content = ""
            except Exception as e:
                print(f"PDF文本提取失败: {e}")
                text_content = ""
        elif file_ext in ['.txt', '.md']:
            # 文本文件：直接解码
            text_content = content.decode('utf-8', errors='ignore')
        elif file_ext in ['.docx', '.doc']:
            # Word文档：需要python-docx库
            try:
                from docx import Document
                import io
                doc = Document(io.BytesIO(content))
                text_parts = [para.text for para in doc.paragraphs if para.text.strip()]
                text_content = "\n".join(text_parts)
            except ImportError:
                print("警告: python-docx未安装，无法提取Word文档文本")
                text_content = content.decode('utf-8', errors='ignore')
            except Exception as e:
                print(f"Word文档文本提取失败: {e}")
                text_content = content.decode('utf-8', errors='ignore')
        else:
            # 其他文件：尝试直接解码
            text_content = content.decode('utf-8', errors='ignore')
        
        # 清理文本：移除乱码和特殊字符
        if text_content:
            import re
            # 移除PDF元数据（如%PDF-1.6、obj、Linearized等）
            text_content = re.sub(r'%PDF[^\n]*', '', text_content)
            text_content = re.sub(r'obj\s+\d+\s+\d+', '', text_content)
            text_content = re.sub(r'Linearized\s+\d+', '', text_content)
            text_content = re.sub(r'Filter/FlateDecode', '', text_content)
            text_content = re.sub(r'Length\s+\d+', '', text_content)
            text_content = re.sub(r'endstream\s+endobj', '', text_content)
            # 移除PDF常见的乱码模式（如二进制数据、特殊符号等）
            text_content = re.sub(r'[^\w\s\u4e00-\u9fff\u3000-\u303f\uff00-\uffef，。！？；：、""''（）【】《》\n\r\t]', '', text_content)
            # 移除测试文本
            if '这是一个关于影视制作的测试文本' in text_content:
                # 移除测试文本段落
                text_content = re.sub(r'这是一个关于影视制作的测试文本[^。]*。', '', text_content)
            # 移除过多的空白字符
            text_content = re.sub(r'\s{3,}', '\n\n', text_content)
            # 移除过短的行（可能是乱码）
            lines = text_content.split('\n')
            cleaned_lines = [line for line in lines if len(line.strip()) > 3 or not re.search(r'[^\u4e00-\u9fff\w\s]', line)]
            text_content = '\n'.join(cleaned_lines)
            # 限制长度（保留前15000字符，足够向量化）
            text_content = text_content[:15000].strip()
        
        # 添加到向量数据库（如果可用）
        doc_id = f"doc_{int(__import__('time').time())}"
        if self.chroma_service and self.chroma_service.chroma_available:
            try:
                import uuid
                doc_id = str(uuid.uuid4())
                self.chroma_service.add_documents(
                    documents=[text_content],
                    metadatas=[{
                        "filename": filename,
                        "file_path": str(file_path),
                        **(metadata or {})
                    }],
                    ids=[doc_id]
                )
            except Exception as e:
                print(f"添加到向量数据库失败: {e}")
        
        return {
            "id": doc_id,
            "filename": filename,
            "file_path": str(file_path),
            "size": len(content),
            "metadata": metadata
        }
    
    async def search_documents(
        self,
        query: str,
        n_results: int = 5
    ) -> List[dict]:
        """搜索文档"""
        print(f"[知识库搜索] 搜索查询: {query}, n_results={n_results}")
        
        if not self.chroma_service or not self.chroma_service.chroma_available:
            print("[知识库搜索] Chroma服务不可用")
            return []
        
        try:
            # 检查集合中是否有文档
            collection_info = self.chroma_service.get_collection_info()
            print(f"[知识库搜索] 集合信息: {collection_info}")
            
            if collection_info.get("count", 0) == 0:
                print("[知识库搜索] 集合中没有文档")
                return []
            
            results = self.chroma_service.search(query, n_results=n_results)
            print(f"[知识库搜索] 搜索结果数量: {len(results)}")
            return results
        except Exception as e:
            import traceback
            print(f"[知识库搜索] 搜索错误: {e}")
            print(f"[知识库搜索] 错误堆栈: {traceback.format_exc()}")
            return []
    
    async def get_all_documents(self) -> List[dict]:
        """获取所有文档"""
        if not self.chroma_service or not self.chroma_service.chroma_available:
            return []
        
        try:
            # Chroma没有直接获取所有文档的方法，需要通过搜索实现
            # 这里返回集合信息
            info = self.chroma_service.get_collection_info()
            return [info] if "error" not in info else []
        except Exception as e:
            print(f"获取文档错误: {e}")
            return []
    
    async def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        if not self.chroma_service or not self.chroma_service.chroma_available:
            return False
        
        try:
            return self.chroma_service.delete(ids=[doc_id])
        except Exception as e:
            print(f"删除文档错误: {e}")
            return False

knowledge_service = KnowledgeService()

