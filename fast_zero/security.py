from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from http import HTTPStatus

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt import DecodeError, decode, encode
from mako.util import restore__ast
from pwdlib import PasswordHash

from sqlalchemy import select
from sqlalchemy.orm import Session

from fast_zero.database import get_session
from fast_zero.models import User

# 配置信息
SECRET_KEY = "sk-69523***********************c087"
ALGORITHM = 'HS256'
ASSESS_TOKEN_MINUTES = 30
pwd_context = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_assess_token(data: dict):

    to_encode = data.copy()
    expire = datetime.now(tz=ZoneInfo('UTC')) + timedelta(
        minutes=ASSESS_TOKEN_MINUTES
    )
    to_encode.update({"exp": expire})
    encode_jwt = encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encode_jwt


def get_password_hash(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def get_current_user(
        session: Session = Depends(get_session),
        token: str = Depends(oauth2_scheme)
):
    credentials_exception = HTTPException(
        status_code=HTTPStatus.UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        payload = encode(token, SECRET_KEY, algorithm=[ALGORITHM])
        subject_email = payload.get("sub")

        if not subject_email:
            raise credentials_exception

    except DecodeError:
        raise  credentials_exception

    user = session.scalar(select(User).where(subject_email==User.email))

    if not user:
        raise credentials_exception

    return user
