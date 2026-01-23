import hashlib
import shutil
from pathlib import Path

from fastapi import UploadFile
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlmodel import Session, select

from app.core.config import settings
from app.core.db import engine
from app.core.logging import logger
from app.models.file import FileParsingCache
from app.parsers import parse_file
from app.rag.vector_store import vector_store

from app.models.file import FileParsingCache, FileStatus
from app.rag.vector_store import vector_store
from app.rag.strategies.general import GeneralRecursiveStrategy

# 简单的内存缓存
UPLOAD_CACHE = {}

class DocumentService:
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        # 默认使用通用递归策略
        self.default_strategy = GeneralRecursiveStrategy()

    def _calculate_hash(self, file_path: Path) -> str:
        """计算文件的 SHA-256 哈希值"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    async def index_document_task(self, file_hash: str):
        """
        [异步背景任务] 执行向量索引
        """
        with Session(engine) as session:
            file_record = session.get(FileParsingCache, file_hash)
            if not file_record:
                return

            try:
                # 更新状态：正在索引
                file_record.status = FileStatus.INDEXING
                session.add(file_record)
                session.commit()

                logger.info(f"Indexing file {file_record.filename}...")
                
                # 策略选择 (未来可根据文件类型选择不同策略)
                strategy = self.default_strategy
                
                # 执行切分
                documents = strategy.split(
                    file_record.content, 
                    metadata={"file_hash": file_hash, "filename": file_record.filename}
                )

                # 存入向量库
                vector_store.add_documents(documents)

                # 更新状态：完成
                file_record.status = FileStatus.COMPLETED
                file_record.indexed = True  # 保持兼容性
                file_record.error_message = None
                session.add(file_record)
                session.commit()
                logger.info(f"File {file_hash} indexed successfully.")
                
            except Exception as e:
                logger.exception(f"Index failed for {file_hash}")
                file_record.status = FileStatus.FAILED
                file_record.error_message = str(e)
                session.add(file_record)
                session.commit()

    async def process_file(self, file: UploadFile) -> tuple[str, str, Path]:
        """
        处理上传文件 (同步解析 + 设置异步索引任务)
        """
        temp_path = self.upload_dir / f"temp_{file.filename}"
        try:
            with temp_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            file_hash = self._calculate_hash(temp_path)
            final_path = self.upload_dir / f"{file_hash}{Path(file.filename).suffix}"

            with Session(engine) as session:
                cached_file = session.get(FileParsingCache, file_hash)
                
                if cached_file:
                    temp_path.unlink()
                    content = cached_file.content
                else:
                    logger.info("Cache MISS. Parsing file...")
                    content = parse_file(temp_path)
                    
                    new_cache = FileParsingCache(
                        file_hash=file_hash,
                        filename=file.filename,
                        content=content,
                        file_type=Path(file.filename).suffix,
                        file_size=temp_path.stat().st_size,
                        status=FileStatus.PENDING,
                        indexed=False
                    )
                    session.add(new_cache)
                    session.commit()

                    if not final_path.exists():
                        shutil.move(temp_path, final_path)
                    else:
                        temp_path.unlink()

                UPLOAD_CACHE[file_hash] = {
                    "content": content,
                    "filename": file.filename,
                    "path": final_path,
                }
                return content, file_hash, final_path

        finally:
            file.file.close()
            if temp_path.exists():
                temp_path.unlink()

    def list_documents(self) -> list[FileParsingCache]:
        with Session(engine) as session:
            return session.exec(select(FileParsingCache).order_by(FileParsingCache.created_at.desc())).all()

    def delete_document(self, file_hash: str):
        with Session(engine) as session:
            file_record = session.get(FileParsingCache, file_hash)
            if file_record:
                if file_record.indexed or file_record.status == FileStatus.COMPLETED:
                    vector_store.delete_by_metadata("file_hash", file_hash)
                
                final_path = self.upload_dir / f"{file_hash}{file_record.file_type}"
                if final_path.exists():
                    final_path.unlink()
                
                session.delete(file_record)
                session.commit()
                return True
        return False

    async def sync_knowledge_base(self, background_tasks):
        """扫描并异步索引"""
        kb_dir = Path("knowledge_base")
        if not kb_dir.exists(): kb_dir.mkdir(parents=True)
        
        supported_extensions = {".pdf", ".docx", ".txt", ".md", ".xlsx", ".pptx"}
        files = [f for f in kb_dir.glob("**/*") if f.is_file() and f.suffix.lower() in supported_extensions]
        
        results = []
        for file_path in files:
            file_hash = self._calculate_hash(file_path)
            with Session(engine) as session:
                cached_file = session.get(FileParsingCache, file_hash)
                if not cached_file:
                    content = parse_file(file_path)
                    cached_file = FileParsingCache(
                        file_hash=file_hash,
                        filename=file_path.name,
                        content=content,
                        file_type=file_path.suffix,
                        file_size=file_path.stat().st_size,
                        status=FileStatus.PENDING
                    )
                    session.add(cached_file)
                    session.commit()
                
                if cached_file.status in [FileStatus.PENDING, FileStatus.FAILED]:
                    background_tasks.add_task(self.index_document_task, file_hash)
                    results.append(f"Queued: {file_path.name}")
                else:
                    results.append(f"Skipped: {file_path.name}")
        return results


document_service = DocumentService()
