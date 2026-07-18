from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from fast_zero.database import get_session
from fast_zero.models import User
from fast_zero.schemas import (
    FilterPage,
    UserList,
    UserPublic,
    UserSchemas,
)
from fast_zero.security import (
    get_current_user,
    get_password_hash,
)

T_Session = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]
# 设定为前缀，然后在app.py里面注册
router = APIRouter(prefix='/users', tags=['users'])


@router.post(
    '/create_user', status_code=HTTPStatus.CREATED, response_model=UserPublic
)
# 依赖注入
async def create_user(user: UserSchemas, session: T_Session):
    # 查询这个用户是否存在
    db_user = await session.scalar(
        select(User).where(
            (User.username == user.username) | (User.email == user.email)
        )
    )

    # 处理报错
    if db_user:
        if db_user.username == user.username:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,  # 409冲突
                detail='Username has already exists',
            )
        elif db_user.email == user.email:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail='Email has already exists',
            )

    hash_password = get_password_hash(user.password)

    db_user = User(
        username=user.username, email=user.email, password=hash_password
    )
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)

    return db_user


@router.get('/', response_model=UserList)
async def read_users(
    session: T_Session, filter_users: Annotated[FilterPage, Query()]
):
    # 这里需要将俩部分拆开
    users = (
        await session.scalars(
            select(User).offset(filter_users.offset).limit(filter_users.limit)
        )
    ).all()
    return {'users': users}


@router.put('/{user_id}', response_model=UserPublic)
async def update_user(
    user_id: int,
    user: UserSchemas,
    session: T_Session,
    current_user: CurrentUser,
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Not enough permission'
        )
    # 但是更新存在一个问题，就是之前我们设置了username和email是唯一的
    db_user = await session.scalar(select(User).where(User.id == user_id))

    hash_password = get_password_hash(user.password)
    try:
        db_user.username = user.username
        db_user.email = user.email
        db_user.password = hash_password
        await session.commit()
        await session.refresh(db_user)
    except IntegrityError:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='Username or Email already exists',
        )
    return db_user


@router.delete('/{user_id}')
async def delete_user(
    user_id: int,
    session: T_Session,
    current_user: CurrentUser,
):
    if user_id != current_user.id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Not enough permission'
        )

    await session.delete(current_user)
    await session.commit()

    return {'message': 'User has deleted'}
