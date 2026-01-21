from datetime import datetime

from sqlmodel import Field, SQLModel


class FileParsingCache(SQLModel, table=True):
    __tablename__ = "file_parsing_cache"  # type: ignore

    file_hash: str = Field(primary_key=True, max_length=64, description="SHA-256 hash of file content")
    filename: str = Field(index=True)
    content: str = Field(description="Parsed text content")
    file_type: str = Field(max_length=10)
    file_size: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.now)
