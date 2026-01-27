import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.core.db import get_db
from app.main import app

# 使用内存数据库进行测试，使用 StaticPool 保持线程间连接
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)


@pytest.fixture(name="session")
def session_fixture():
    # 创建表结构
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    # 测试结束后清理
    SQLModel.metadata.drop_all(engine)


from app.api.deps import get_current_user, get_db
from app.models.user import User


@pytest.fixture(name="client")
def client_fixture(session: Session):
    # 覆盖 get_db 依赖，注入测试用的 session
    def get_session_override():
        return session

    # 模拟登录用户，避开 JWT 校验
    def get_current_user_override():
        return User(id="test-user-id", username="testuser", email="test@example.com")

    app.dependency_overrides[get_db] = get_session_override
    app.dependency_overrides[get_current_user] = get_current_user_override

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
