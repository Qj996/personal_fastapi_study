from contextlib import contextmanager
from datetime import datetime

import factory
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from fast_zero.app import app
from fast_zero.database import get_session
from fast_zero.models import User, table_registry
from fast_zero.security import get_password_hash


# 创建一个用户对象工厂，供给测试使用
class UserFactory(factory.Factory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'test{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@test.com')
    password = factory.LazyAttribute(lambda obj: f'{obj.usernam}@example.com')


# 装饰器，作用是每个测试得到全新的数据库环境
@pytest_asyncio.fixture
async def session():
    """提供 SQLite 内存数据库的测试会话，测试结束自动清理。

    StaticPool 确保所有连接复用同一个 :memory: 数据库，
    check_same_thread=False 允许跨线程访问（TestClient 需要）。
    """
    engine = create_async_engine(
        #  修改为异步的
        'sqlite+aiosqlite:///:memory:',
        # 不同线程之间可以实现共享
        connect_args={'check_same_thread': False},
        # 所有请求使用同一连接
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(table_registry.metadata.create_all)

    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(table_registry.metadata.drop_all)


@pytest.fixture
def client(session):
    async def get_session_override():
        return session

    # `dependency_overrides` 是 FastAPI 合法属性，IDE 误报可忽略
    app.dependency_overrides[get_session] = get_session_override  # type: ignore[attr-defined]

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()  # type: ignore[attr-defined]


@pytest_asyncio.fixture
async def user(session):
    password = 'testtest'
    # 修改为用户工厂创建，来进行测试
    user = UserFactory(password=get_password_hash(password))

    session.add(user)
    await session.commit()
    await session.refresh(user)

    user.clean_password = password

    return user


@pytest_asyncio.fixture
async def other_user(session):
    password = 'testtest'
    user = UserFactory(password=get_password_hash(password))

    session.add(user)
    await session.commit()
    await session.refresh(user)

    user.clean_password = password

    return user


@pytest.fixture
def token(client, user):
    response = client.post(
        '/auth/token',
        data={'username': user.email, 'password': user.clean_password},
    )
    return response.json()['access_token']


@contextmanager
def _mock_db_time(*, model, time=datetime(2024, 1, 1)):

    def fake_time_hook(mapper, connection, target):
        if hasattr(target, 'created_at'):
            target.created_at = time

    event.listen(model, 'before_insert', fake_time_hook)

    yield time

    event.remove(model, 'before_insert', fake_time_hook)


@pytest.fixture
def mock_db_time():

    return _mock_db_time
