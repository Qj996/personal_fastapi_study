from http import HTTPStatus

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fast_zero.database import get_session
from fast_zero.models import User
from fast_zero.schemas import Token, UserList, UserPublic, UserSchemas
from fast_zero.security import (
    create_assess_token,
    get_current_user,
    get_password_hash,
    verify_password,
)

app = FastAPI()


@app.post("/token", response_model=Token)
def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),
        session: Session = Depends(get_session)
):
    user = session.scalar(select(User).where(User.email == form_data.username))

    if not user:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    if not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    access_token = create_assess_token(data={"sub": user.email})

    return {"access_token": access_token, "token_type": "bearer"}


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
                status_code=HTTPStatus.CONFLICT,  # 409冲突
                detail="Username has already exists"
            )
        elif db_user.email == user.email:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail='Email has already exists'
            )

    hash_password = get_password_hash(user.password)

    db_user = User(
        username=user.username,
        email=user.email,
        password=hash_password
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
        session: Session = Depends(get_session),
        current_user: User = Depends(get_current_user)
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail="Not enough permission"
        )
    # 但是更新存在一个问题，就是之前我们设置了username和email是唯一的
    db_user = session.scalar(select(User).where(User.id == user_id))

    hash_password = get_password_hash(
        user.password
    )
    try:
        db_user.username = user.username
        db_user.email = user.email
        db_user.password = hash_password
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
        session: Session = Depends(get_session),
        current_user: User = Depends(get_current_user)
):
    if user_id != current_user.id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail="Not enough permission"
        )

    session.delete(current_user)
    session.commit()

    return {"message": "User has deleted"}
