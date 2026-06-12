from typing import List

from pydantic import BaseModel, ConfigDict, EmailStr


class UserPublic(BaseModel):
    id: int
    username: str
    email: EmailStr
    # Pydantic无法将SQLAlchemy模型转化为Pydantic模型， 添加下面的
    model_config = ConfigDict(from_attributes=True)


class MyResponse(BaseModel):
    message: str


class UserSchemas(BaseModel):
    username: str
    email: EmailStr
    password: str    # 确保收到的是一个邮件


class UserDb(UserSchemas):
    id: int


class UserList(BaseModel):
    users: List[UserPublic]
