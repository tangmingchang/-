"""
知识库API
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List
from sqlalchemy.orm import Session
from app.services.knowledge_service import knowledge_service
from app.models.knowledge import Document
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User

router = APIRouter()

@router.post("/knowledge/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """上传文档"""
    try:
        content = await file.read()
        
        # 保存文档
        doc_info = await knowledge_service.save_document(
            filename=file.filename,
            content=content,
            metadata={
                "content_type": file.content_type,
                "size": len(content)
            }
        )
        
        # 保存到数据库
        document = Document(
            filename=file.filename,
            file_path=doc_info["file_path"],
            file_type=file.content_type or "unknown",
            file_size=doc_info["size"],
            document_metadata=doc_info.get("metadata")
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        
        return {
            "id": document.id,
            "filename": document.filename,
            "file_type": document.file_type,
            "file_size": document.file_size,
            "created_at": document.created_at.isoformat() if document.created_at else None
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

@router.get("/knowledge/search")
async def search_knowledge(
    query: str,
    limit: int = 5,
    current_user: User = Depends(get_current_active_user)
):
    """搜索知识库"""
    try:
        results = await knowledge_service.search_documents(query, n_results=limit)
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@router.get("/knowledge/documents")
async def get_documents(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取所有文档"""
    documents = db.query(Document).order_by(
        Document.created_at.desc()
    ).all()
    
    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "file_type": doc.file_type,
            "file_size": doc.file_size,
            "file_path": doc.file_path,  # 添加文件路径
            "created_at": doc.created_at.isoformat() if doc.created_at else None
        }
        for doc in documents
    ]

@router.delete("/knowledge/documents/{document_id}")
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除文档"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 从向量数据库删除
    await knowledge_service.delete_document(f"doc_{document_id}")
    
    # 从数据库删除
    db.delete(document)
    db.commit()
    
    return {"message": "文档已删除"}

