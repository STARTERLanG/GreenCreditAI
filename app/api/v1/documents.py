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


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: Annotated[UploadFile, File(...)]):
    """
    上传文件并解析内容 (带数据库缓存去重)
    """
    try:
        # process_file 现在返回 (content, hash, file_path)
        content, file_hash, file_path = await document_service.process_file(file)

        # 缓存内容和路径
        UPLOAD_CACHE[file_hash] = {
            "content": content,
            "filename": file.filename,
            "path": file_path,
        }

        return UploadResponse(
            filename=file.filename,
            status="success",
            message=f"文件处理完成，共 {len(content)} 字符。",
            file_hash=file_hash,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


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
