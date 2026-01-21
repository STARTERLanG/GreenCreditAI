import sqlite3
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# 检查 SQLite 版本
if sqlite3.sqlite_version < "3.35.0":
    print(
        f"Warning: SQLite version {sqlite3.sqlite_version} is too old for ChromaDB (>=3.35.0). This might cause hangs."
    )

from app.core.utils import configure_network_settings

# 立即执行清理
configure_network_settings()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App Config
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Aliyun Bailian / DashScope
    DASHSCOPE_API_KEY: str

    # Models
    MODEL_ROUTER_NAME: str = "qwen-turbo"
    MODEL_EXPERT_NAME: str = "qwen-max"
    EMBEDDING_MODEL_NAME: str = "text-embedding-v3"

    # Storage
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    VECTOR_DB_PERSIST_DIR: Path = BASE_DIR / "data" / "qdrant_db"
    UPLOAD_DIR: Path = BASE_DIR / "data" / "uploads"
    KNOWLEDGE_BASE_DIR: Path = BASE_DIR / "knowledge_base"
    SQLITE_DB_PATH: str = "sqlite:///data/greencredit.db"


settings = Settings()
