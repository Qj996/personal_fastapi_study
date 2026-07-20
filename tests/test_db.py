from dataclasses import asdict

import pytest
from sqlalchemy import select

from fast_zero.models import Todo, User


@pytest.mark.asyncio
async def test_user_db(session, mock_db_time):
    with mock_db_time(model=User) as time:
        new_user = User(
            username='alice', email='test111@example.com', password='123456'
        )
        session.add(new_user)
        await session.commit()
    user = await session.scalar(select(User).where(User.username == 'alice'))
    assert asdict(user) == {
        'id': 1,
        'username': user.username,
        'password': user.password,
        'email': user.email,
        'created_at': time,
        'todos': [],
    }


# 新建测试任务类是否创建成功
@pytest.mark.asyncio
async def test_creat_todo(session, user):
    todo = Todo(
        title='test Todo',
        description='the is a test for todo',
        state='draft',
        user_id=user.id,
    )

    session.add(todo)
    await session.commit()

    todo = await session.scalar(select(Todo))

    assert asdict(todo) == {
        'description': 'the is a test for todo',
        'id': 1,
        'state': 'draft',
        'title': 'test Todo',
        'user_id': 1,
    }


# 测试用户和任务之间是否进行关联
@pytest.mark.asyncio
async def test_user_todo_relationship(session, user: User):
    todo = Todo(
        title='test Todo',
        description='test Desc',
        state='draft',
        user_id=user.id,
    )

    session.add(todo)
    await session.commit()
    # 重新查询这个对象并且刷新他
    await session.refresh(user)

    user = await session.scalar(select(User).where(User.id == user.id))
    assert user.todos == [todo]
