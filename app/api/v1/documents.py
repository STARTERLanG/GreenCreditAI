from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.document_service import document_service, UPLOAD_CACHE
from pydantic import BaseModel

router = APIRouter()

class UploadResponse(BaseModel):
    filename: str
    status: str
    message: str
    file_hash: str # 新增

@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    上传文件并解析内容 (带数据库缓存去重)
    """
    try:
        # 调整：process_file 现在应该返回 (content, hash)
        content, file_hash = await document_service.process_file(file)
        
        # 缓存内容
        UPLOAD_CACHE[file_hash] = {
            "content": content,
            "filename": file.filename
        }
        
        return UploadResponse(
            filename=file.filename,
            status="success",
            message=f"文件处理完成，共 {len(content)} 字符。",
            file_hash=file_hash
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
