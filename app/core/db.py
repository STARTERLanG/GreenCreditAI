from sqlmodel import SQLModel, create_engine, Session
from app.core.config import settings


# check_same_thread=False 是 SQLite 在 FastAPI 中使用的必要配置
engine = create_engine(settings.SQLITE_DB_PATH, connect_args={"check_same_thread": False})

def init_db():
    """初始化数据库表结构"""
    SQLModel.metadata.create_all(engine)

def get_db():
    """FastAPI Dependency for DB Session"""
    with Session(engine) as session:
        yield session
