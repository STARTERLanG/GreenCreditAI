import shutil
import hashlib
from pathlib import Path
from fastapi import UploadFile
from sqlmodel import Session
from app.core.config import settings
from app.core.logging import logger
from app.core.db import engine
from app.models.file import FileParsingCache
from app.parsers import parse_file

# 简单的内存缓存
# Key: file_hash, Value: {"content": str, "filename": str}
UPLOAD_CACHE = {}

class DocumentService:
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def _calculate_hash(self, file_path: Path) -> str:
        """计算文件的 SHA-256 哈希值"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            # 分块读取，避免大文件占用内存
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    async def process_file(self, file: UploadFile) -> str:
        """
        处理上传文件：保存 -> 计算Hash -> 查库 -> (命中返回) / (未命中解析入库)
        返回: 文件内容文本
        """
        # 1. 临时保存文件以计算 Hash (FastAPI 的 UploadFile 可能是内存对象)
        temp_path = self.upload_dir / f"temp_{file.filename}"
        try:
            with temp_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # 2. 计算 Hash
            file_hash = self._calculate_hash(temp_path)
            logger.info(f"File hash: {file_hash}")

            # 3. 查询数据库缓存
            with Session(engine) as session:
                cached_file = session.get(FileParsingCache, file_hash)
                if cached_file:
                    logger.info("Cache HIT! Returning content from DB.")
                    # 如果需要，可以将临时文件重命名为正式文件 (可选)
                    # 清理临时文件
                    temp_path.unlink()
                    return cached_file.content, file_hash

                # 4. Cache Miss: 解析内容
                logger.info("Cache MISS. Parsing file...")
                content = parse_file(temp_path)
                
                # 5. 存入数据库
                new_cache = FileParsingCache(
                    file_hash=file_hash,
                    filename=file.filename,
                    content=content,
                    file_type=Path(file.filename).suffix,
                    file_size=temp_path.stat().st_size
                )
                session.add(new_cache)
                session.commit()
                logger.info("Content parsed and saved to DB.")

                # 6. (可选) 保留文件副本，按 Hash 命名
                final_path = self.upload_dir / f"{file_hash}{Path(file.filename).suffix}"
                if not final_path.exists():
                    shutil.move(temp_path, final_path)
                else:
                    temp_path.unlink()
                
                return content, file_hash

        finally:
            file.file.close()
            # 确保临时文件被清理
            if temp_path.exists():
                temp_path.unlink()

document_service = DocumentService()