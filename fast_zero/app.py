from http import HTTPStatus

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fast_zero.database import get_session
from fast_zero.models import User
from fast_zero.schemas import UserList, UserPublic, UserSchemas

app = FastAPI()


@app.get('/')
def read_root():
    return {'message': 'Olá Mundo!'}


@app.get("/test", status_code=HTTPStatus.OK, response_class=HTMLResponse)
def my_try():
    return """
    <html>
      <head>
        <title>Hello World !</title>
      </head>
      <body>
        <h1>Hello World</h1>
      </body>
    </html>
    """


@app.post(
    "/create_user",
    status_code=HTTPStatus.CREATED,
    response_model=UserPublic
)
# 依赖注入
def create_user(user: UserSchemas, session=Depends(get_session)):
    # 查询这个用户是否存在
    db_user = session.scalar(
        select(User).where(
            (User.username == user.username) | (User.email == user.email)
        )
    )

    # 处理报错
    if db_user:
        if db_user.username == user.username:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,   # 409冲突
                detail="Username has already exists"
            )
        elif db_user.email == user.email:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail='Email has already exists'
            )

    db_user = User(
        username=user.username, email=user.email, password=user.password
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return db_user


@app.get("/users/", response_model=UserList)
def read_users(
        skip: int = 0,
        limit: int = 100,
        session: Session = Depends(get_session),
):
    users = session.scalars(select(User).offset(skip).limit(limit)).all()
    return {"users": users}


@app.put("/users/{user_id}", response_model=UserPublic)
def update_user(
        user_id: int,
        user: UserSchemas,
        session: Session = Depends(get_session)
):
    # 但是更新存在一个问题，就是之前我们设置了username和email是唯一的
    db_user = session.scalar(select(User).where(User.id == user_id))
    if not db_user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="User not found"
        )

    try:
        db_user.username = user.username
        db_user.email = user.email
        db_user.password = user.password
        session.commit()
        session.refresh(db_user)
    except IntegrityError:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail="Username or Email already exists"
        )
    return db_user


@app.delete("/users/{user_id}")
def delete_user(
        user_id: int,
        session: Session = Depends(get_session)
):
    db_user = session.scalar(select(User).where(user_id == User.id))

    if not db_user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='User not found'
        )

    session.delete(db_user)
    session.commit()

    return {"message": "User has deleted"}
