from contextlib import contextmanager
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from fast_zero.app import app
from fast_zero.database import get_session
from fast_zero.models import User, table_registry
from fast_zero.security import get_password_hash


# 装饰器，作用是每个测试得到全新的数据库环境
@pytest.fixture
def session():
    """提供 SQLite 内存数据库的测试会话，测试结束自动清理。

    StaticPool 确保所有连接复用同一个 :memory: 数据库，
    check_same_thread=False 允许跨线程访问（TestClient 需要）。
    """
    engine = create_engine(
        'sqlite:///:memory:',
        # 不同线程之间可以实现共享
        connect_args={'check_same_thread': False},
        # 所有请求使用同一连接
        poolclass=StaticPool,
    )
    table_registry.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    table_registry.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def client(session):
    def get_session_override():
        return session

    # `dependency_overrides` 是 FastAPI 合法属性，IDE 误报可忽略
    app.dependency_overrides[get_session] = get_session_override  # type: ignore[attr-defined]

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()  # type: ignore[attr-defined]


@pytest.fixture
def user(session):
    password = "test123"
    user = User(
        username="Teste",
        email="teste@example.com",
        # 需要进行加密
        password=get_password_hash("test123"))
    session.add(user)
    session.commit()
    session.refresh(user)

    user.clean_password = password

    return user


@contextmanager
def _mock_db_time(*, model, time=datetime(2024, 1, 1)):

    def fake_time_hook(mapper, connection, target):
        if hasattr(target, "created_at"):
            target.created_at = time

    event.listen(model, "before_insert", fake_time_hook)

    yield time

    event.remove(model, "before_insert", fake_time_hook)


@pytest.fixture
def mock_db_time():

    return _mock_db_time
