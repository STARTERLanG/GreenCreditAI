from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings

# check_same_thread=False 是 SQLite 在 FastAPI 中使用的必要配置
engine = create_engine(settings.SQLITE_DB_PATH, connect_args={"check_same_thread": False, "timeout": 10})


from sqlalchemy import event


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


def init_db():
    """初始化数据库表结构"""
    SQLModel.metadata.create_all(engine)


def get_db():
    """FastAPI Dependency for DB Session"""
    with Session(engine) as session:
        yield session
