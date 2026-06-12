from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from jwt import encode
from pwdlib import PasswordHash

# 配置信息
SECRET_KEY = "sk-69523***********************c087"
ALGORITHM = 'HS256'
ASSESS_TOKEN_MINUTES = 30
pwd_context = PasswordHash.recommended()


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
