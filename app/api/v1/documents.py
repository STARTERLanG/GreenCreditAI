from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlmodel import Session

from app.core.config import settings
from app.core.db import engine
from app.models.file import FileParsingCache
from app.services.document_service import UPLOAD_CACHE, document_service

router = APIRouter()


class UploadResponse(BaseModel):
    filename: str
    status: str
    message: str
    file_hash: str


from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile

@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: Annotated[UploadFile, File(...)], background_tasks: BackgroundTasks):
    """
    上传文件并异步索引
    """
    try:
        content, file_hash, file_path = await document_service.process_file(file)

        # 异步建立索引
        background_tasks.add_task(document_service.index_document_task, file_hash)

        return UploadResponse(
            filename=file.filename,
            status="success",
            message=f"文件上传成功，正在后台建立索引。",
            file_hash=file_hash,
        )
    except Exception as e:
        logger.exception(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/list")
async def list_documents():
    """获取知识库文件列表"""
    return document_service.list_documents()


@router.post("/sync")
async def sync_kb(background_tasks: BackgroundTasks):
    """同步知识库目录 (knowledge_base/)"""
    try:
        results = await document_service.sync_knowledge_base(background_tasks)
        return {"status": "success", "results": results}
    except Exception as e:
        logger.exception(f"Sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/index/{file_hash}")
async def index_document(file_hash: str, background_tasks: BackgroundTasks):
    """手动触发后台索引"""
    background_tasks.add_task(document_service.index_document_task, file_hash)
    return {"status": "success", "message": "Indexing task started in background."}


@router.delete("/{file_hash}")
async def delete_document(file_hash: str):
    """从知识库中删除文件"""
    if document_service.delete_document(file_hash):
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="File not found")


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
