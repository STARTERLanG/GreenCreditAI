from datetime import datetime
from enum import Enum

from sqlmodel import Field, SQLModel


class FileStatus(str, Enum):
    PENDING = "PENDING"  # 等待处理
    PARSING = "PARSING"  # 正在解析
    INDEXING = "INDEXING"  # 正在向量化
    COMPLETED = "COMPLETED"  # 处理完成
    FAILED = "FAILED"  # 处理失败


class FileParsingCache(SQLModel, table=True):
    __tablename__ = "file_parsing_cache"  # type: ignore

    file_hash: str = Field(primary_key=True, max_length=64, description="SHA-256 hash of file content")
    filename: str = Field(index=True)
    content: str = Field(description="Parsed text content")
    file_type: str = Field(max_length=10)
    file_size: int = Field(default=0)
    user_id: str | None = Field(default=None, index=True, description="Owner of the file")

    # 状态管理
    status: FileStatus = Field(default=FileStatus.PENDING, index=True)
    indexed: bool = Field(default=False, description="Deprecated: use status instead")
    error_message: str | None = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.now)
