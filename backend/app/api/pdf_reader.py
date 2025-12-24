"""
PDF阅读器API
用于提取PDF章节信息和页面内容
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.core.security import get_current_active_user
from app.models.user import User
import os
from pathlib import Path

router = APIRouter()

class PDFChapterInfo(BaseModel):
    """PDF章节信息"""
    title: str
    page_number: int
    start_page: int
    end_page: Optional[int] = None

class PDFInfoResponse(BaseModel):
    """PDF信息响应"""
    total_pages: int
    chapters: List[PDFChapterInfo]
    file_path: str

@router.get("/pdf/info/{filename:path}", response_model=PDFInfoResponse)
async def get_pdf_info(
    filename: str,
    current_user: User = Depends(get_current_active_user)
):
    """获取PDF文件信息和章节"""
    try:
        # 构建文件路径
        # 假设PDF文件在frontend/public/books目录下
        project_root = Path(__file__).parent.parent.parent.parent
        pdf_path = project_root / "frontend" / "public" / "books" / filename
        
        if not pdf_path.exists():
            raise HTTPException(status_code=404, detail="PDF文件不存在")
        
        # 尝试导入PDF处理库
        try:
            import PyPDF2
        except ImportError:
            # 如果没有PyPDF2，尝试使用pypdf
            try:
                from pypdf import PdfReader as PyPDF2_PdfReader
                PyPDF2 = None
            except ImportError:
                raise HTTPException(
                    status_code=500,
                    detail="PDF处理库未安装，请运行: pip install PyPDF2 或 pip install pypdf"
                )
        
        # 读取PDF
        if PyPDF2:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                
                # 提取章节信息（通过目录或标题页）
                chapters = extract_chapters_from_pdf(pdf_reader, total_pages)
        else:
            # 使用pypdf
            pdf_reader = PyPDF2_PdfReader(str(pdf_path))
            total_pages = len(pdf_reader.pages)
            chapters = extract_chapters_from_pypdf(pdf_reader, total_pages)
        
        return {
            "total_pages": total_pages,
            "chapters": chapters,
            "file_path": f"/books/{filename}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取PDF失败: {str(e)}")

def extract_chapters_from_pdf(pdf_reader, total_pages: int) -> List[Dict[str, Any]]:
    """从PDF中提取章节信息（PyPDF2版本）"""
    chapters = []
    
    try:
        # 尝试从目录提取章节
        if pdf_reader.outline:
            for item in pdf_reader.outline:
                if isinstance(item, list):
                    # 递归处理嵌套的目录项
                    for sub_item in item:
                        if hasattr(sub_item, 'title') and hasattr(sub_item, 'page'):
                            page_num = pdf_reader.get_destination_page_number(sub_item)
                            chapters.append({
                                "title": sub_item.title,
                                "page_number": page_num + 1,  # 转换为1-based
                                "start_page": page_num + 1
                            })
                elif hasattr(item, 'title') and hasattr(item, 'page'):
                    page_num = pdf_reader.get_destination_page_number(item)
                    chapters.append({
                        "title": item.title,
                        "page_number": page_num + 1,
                        "start_page": page_num + 1
                    })
    except:
        pass
    
    # 如果没有找到章节，尝试从页面文本中提取
    if not chapters:
        chapters = extract_chapters_from_text(pdf_reader, total_pages)
    
    # 如果没有章节，创建默认章节
    if not chapters:
        chapters = [{
            "title": "全文",
            "page_number": 1,
            "start_page": 1,
            "end_page": total_pages
        }]
    else:
        # 设置每个章节的结束页
        for i in range(len(chapters)):
            if i < len(chapters) - 1:
                chapters[i]["end_page"] = chapters[i + 1]["start_page"] - 1
            else:
                chapters[i]["end_page"] = total_pages
    
    return chapters

def extract_chapters_from_pypdf(pdf_reader, total_pages: int) -> List[Dict[str, Any]]:
    """从PDF中提取章节信息（pypdf版本）"""
    chapters = []
    
    try:
        # 尝试从目录提取章节
        if hasattr(pdf_reader, 'outline') and pdf_reader.outline:
            for item in pdf_reader.outline:
                if isinstance(item, list):
                    for sub_item in item:
                        if hasattr(sub_item, 'title'):
                            page_num = pdf_reader.get_destination_page_number(sub_item) if hasattr(pdf_reader, 'get_destination_page_number') else 0
                            chapters.append({
                                "title": sub_item.title,
                                "page_number": page_num + 1,
                                "start_page": page_num + 1
                            })
                elif hasattr(item, 'title'):
                    page_num = pdf_reader.get_destination_page_number(item) if hasattr(pdf_reader, 'get_destination_page_number') else 0
                    chapters.append({
                        "title": item.title,
                        "page_number": page_num + 1,
                        "start_page": page_num + 1
                    })
    except:
        pass
    
    if not chapters:
        chapters = extract_chapters_from_text_pypdf(pdf_reader, total_pages)
    
    if not chapters:
        chapters = [{
            "title": "全文",
            "page_number": 1,
            "start_page": 1,
            "end_page": total_pages
        }]
    else:
        for i in range(len(chapters)):
            if i < len(chapters) - 1:
                chapters[i]["end_page"] = chapters[i + 1]["start_page"] - 1
            else:
                chapters[i]["end_page"] = total_pages
    
    return chapters

def extract_chapters_from_text(pdf_reader, total_pages: int, max_pages: int = 50) -> List[Dict[str, Any]]:
    """从PDF前几页的文本中提取章节标题"""
    chapters = []
    chapter_patterns = [
        r'第[一二三四五六七八九十\d]+章',
        r'Chapter\s+\d+',
        r'第[一二三四五六七八九十\d]+节',
        r'^\d+\.\s+[^\n]+',  # 数字开头的标题
    ]
    
    import re
    pages_to_check = min(max_pages, total_pages)
    
    for page_num in range(pages_to_check):
        try:
            page = pdf_reader.pages[page_num]
            text = page.extract_text()
            
            if text:
                lines = text.split('\n')
                for line in lines[:20]:  # 只检查前20行
                    line = line.strip()
                    if len(line) > 3 and len(line) < 100:
                        for pattern in chapter_patterns:
                            if re.search(pattern, line):
                                chapters.append({
                                    "title": line,
                                    "page_number": page_num + 1,
                                    "start_page": page_num + 1
                                })
                                break
        except:
            continue
    
    return chapters

def extract_chapters_from_text_pypdf(pdf_reader, total_pages: int, max_pages: int = 50) -> List[Dict[str, Any]]:
    """从PDF前几页的文本中提取章节标题（pypdf版本）"""
    chapters = []
    chapter_patterns = [
        r'第[一二三四五六七八九十\d]+章',
        r'Chapter\s+\d+',
        r'第[一二三四五六七八九十\d]+节',
        r'^\d+\.\s+[^\n]+',
    ]
    
    import re
    pages_to_check = min(max_pages, total_pages)
    
    for page_num in range(pages_to_check):
        try:
            page = pdf_reader.pages[page_num]
            text = page.extract_text()
            
            if text:
                lines = text.split('\n')
                for line in lines[:20]:
                    line = line.strip()
                    if len(line) > 3 and len(line) < 100:
                        for pattern in chapter_patterns:
                            if re.search(pattern, line):
                                chapters.append({
                                    "title": line,
                                    "page_number": page_num + 1,
                                    "start_page": page_num + 1
                                })
                                break
        except:
            continue
    
    return chapters

@router.get("/pdf/chapter-content/{filename:path}")
async def get_chapter_content(
    filename: str,
    chapter_title: str,
    start_page: Optional[int] = None,
    end_page: Optional[int] = None,
    current_user: User = Depends(get_current_active_user)
):
    """从PDF中提取指定章节的内容"""
    try:
        project_root = Path(__file__).parent.parent.parent.parent
        pdf_path = project_root / "frontend" / "public" / "books" / filename
        
        if not pdf_path.exists():
            raise HTTPException(status_code=404, detail="PDF文件不存在")
        
        # 尝试导入PDF处理库
        try:
            from pypdf import PdfReader
            pdf_reader = PdfReader(str(pdf_path))
            use_pypdf = True
        except ImportError:
            try:
                import PyPDF2
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                use_pypdf = False
            except ImportError:
                raise HTTPException(
                    status_code=500,
                    detail="PDF处理库未安装，请运行: pip install pypdf 或 pip install PyPDF2"
                )
        
        # 如果没有指定页码，尝试根据章节标题查找
        if start_page is None:
            start_page = find_chapter_page(pdf_reader, chapter_title, use_pypdf)
            if start_page is None:
                start_page = 1
        
        if end_page is None:
            total_pages = len(pdf_reader.pages) if use_pypdf else len(pdf_reader.pages)
            end_page = total_pages
        
        # 提取页面内容
        content_pages = []
        total_pages = len(pdf_reader.pages) if use_pypdf else len(pdf_reader.pages)
        for page_num in range(start_page - 1, min(end_page, total_pages)):
            try:
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                if text.strip():
                    content_pages.append({
                        "page": page_num + 1,
                        "content": text.strip()
                    })
            except Exception as e:
                continue
        
        # 合并所有页面内容
        if not content_pages:
            full_content = "无法从PDF中提取内容，请检查PDF文件是否可读。"
        else:
            full_content = f"--- 第 {content_pages[0]['page']} 页 ---\n\n{content_pages[0]['content']}"
            if len(content_pages) > 1:
                for page_info in content_pages[1:]:
                    full_content += f"\n\n--- 第 {page_info['page']} 页 ---\n\n{page_info['content']}"
        
        return {
            "chapter_title": chapter_title,
            "start_page": start_page,
            "end_page": end_page,
            "content": full_content,
            "total_pages": total_pages
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提取章节内容失败: {str(e)}")

def find_chapter_page(pdf_reader, chapter_title: str, use_pypdf: bool = True) -> Optional[int]:
    """根据章节标题查找页码"""
    import re
    
    try:
        # 尝试从目录中查找
        if hasattr(pdf_reader, 'outline') and pdf_reader.outline:
            for item in pdf_reader.outline:
                if isinstance(item, list):
                    for sub_item in item:
                        if hasattr(sub_item, 'title'):
                            title = sub_item.title if use_pypdf else getattr(sub_item, 'title', '')
                            if chapter_title.lower() in title.lower():
                                if hasattr(pdf_reader, 'get_destination_page_number'):
                                    try:
                                        page_num = pdf_reader.get_destination_page_number(sub_item)
                                        return page_num + 1
                                    except:
                                        pass
                elif hasattr(item, 'title'):
                    title = item.title if use_pypdf else getattr(item, 'title', '')
                    if chapter_title.lower() in title.lower():
                        if hasattr(pdf_reader, 'get_destination_page_number'):
                            try:
                                page_num = pdf_reader.get_destination_page_number(item)
                                return page_num + 1
                            except:
                                pass
    except:
        pass
    
    # 如果目录中找不到，尝试从前几页的文本中搜索
    search_keywords = re.findall(r'[\u4e00-\u9fa5]+|\w+', chapter_title)
    if not search_keywords:
        return None
    
    total_pages = len(pdf_reader.pages)
    pages_to_search = min(50, total_pages)
    for page_num in range(pages_to_search):
        try:
            page = pdf_reader.pages[page_num]
            text = page.extract_text()
            if text:
                # 检查是否包含章节标题的关键词
                text_lower = text.lower()
                if any(keyword.lower() in text_lower for keyword in search_keywords):
                    return page_num + 1
        except:
            continue
    
    return None

