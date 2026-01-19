from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.document_service import document_service, UPLOAD_CACHE
from pydantic import BaseModel

router = APIRouter()

class UploadResponse(BaseModel):
    filename: str
    status: str
    message: str

@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    上传文件并解析内容 (带数据库缓存去重)
    """
    try:
        # 处理文件 (包含 Hash 计算、查库缓存、解析逻辑)
        content = await document_service.process_file(file)
        
        # 3. 缓存内容 (覆盖式，简单模拟 "当前上下文")
        # 注意：这里依然使用简单的内存字典作为会话上下文，
        # 下一步可以将 content 存入 chat_sessions 表
        UPLOAD_CACHE["latest"] = {
            "filename": file.filename,
            "content": content
        }
        
        return UploadResponse(
            filename=file.filename if file.filename else "unknown",
            status="success",
            message=f"文件处理完成（已缓存），共 {len(content)} 字符，可进行分析。"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
