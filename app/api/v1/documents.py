from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlmodel import Session

from app.api import deps
from app.core.config import settings
from app.core.db import engine
from app.models.file import FileParsingCache
from app.models.user import User
from app.services.document_service import UPLOAD_CACHE, document_service

router = APIRouter()


class UploadResponse(BaseModel):
    filename: str
    status: str
    message: str
    file_hash: str


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: Annotated[User, Depends(deps.get_current_user)] = None,
):
    """上传文件并进行解析"""
    if not file.filename.endswith((".pdf", ".docx", ".txt", ".md")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Only PDF, DOCX, TXT, and MD files are allowed.",
        )
    try:
        # 读取文件内容
        content = await file.read()

        result = await document_service.process_file(
            filename=file.filename, content=content, user_id=current_user.id if current_user else None
        )
        return result
    except Exception as e:
        # logger.exception(f"Upload failed: {e}") # Assuming logger is defined elsewhere
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/list")
async def list_documents(current_user: Annotated[User, Depends(deps.get_current_user)] = None):
    """获取知识库文件列表"""
    return document_service.list_documents(user_id=current_user.id if current_user else None)


@router.post("/sync")
async def sync_kb(background_tasks: BackgroundTasks):
    """同步知识库目录 (knowledge_base/)"""
    try:
        results = await document_service.sync_knowledge_base(background_tasks)
        return {"status": "success", "results": results}
    except Exception as e:
        # logger.exception(f"Sync failed: {e}") # Assuming logger is defined elsewhere
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/index/{file_hash}")
async def index_document(
    file_hash: str,
    current_user: Annotated[User, Depends(deps.get_current_user)] = None,
):
    """手动触发索引"""
    document_service.index_document_task(file_hash, user_id=current_user.id if current_user else None)
    return {"status": "indexing_started", "file_hash": file_hash}


@router.delete("/{file_hash}")
async def delete_document(
    file_hash: str,
    current_user: Annotated[User, Depends(deps.get_current_user)],
):
    """从知识库中删除文件"""
    if document_service.delete_document(file_hash, user_id=current_user.id):
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="File not found or permission denied")


@router.get("/file/{file_hash}")
async def get_document_file(file_hash: str):
    """获取原始文件流"""
    # 1. 查缓存
    if file_hash in UPLOAD_CACHE:
        path = UPLOAD_CACHE[file_hash]["path"]
        filename = UPLOAD_CACHE[file_hash]["filename"]
        return FileResponse(path, filename=filename)

    # 2. 查数据库 (我们需要确保数据库或文件系统里有持久化的文件)
    # 尝试在 upload_dir 中寻找以 hash 开头的文件
    upload_dir = settings.UPLOAD_DIR
    for file in upload_dir.iterdir():
        if file.name.startswith(file_hash):
            return FileResponse(file, filename=file.name)

    raise HTTPException(status_code=404, detail="File not found")


@router.get("/content/{file_hash}")
async def get_document_content(file_hash: str):
    """获取已解析的文件内容用于预览"""
    # 优先查缓存
    if file_hash in UPLOAD_CACHE:
        return {"content": UPLOAD_CACHE[file_hash]["content"]}

    # 缓存没有，查数据库
    with Session(engine) as session:
        file_record = session.get(FileParsingCache, file_hash)
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")
        return {"content": file_record.content}
