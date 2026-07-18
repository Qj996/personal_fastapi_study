from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from fast_zero.settings import Settings

engine = create_async_engine(Settings().DATABASE_URL)


async def get_session():
    # expire_on_commit=False,提交数据后，不删除已加载的对象数据
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session
