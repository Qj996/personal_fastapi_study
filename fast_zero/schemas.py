from typing import List

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from fast_zero.models import TodeState


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
    password: str  # 确保收到的是一个邮件


class UserDb(UserSchemas):
    id: int


class UserList(BaseModel):
    users: List[UserPublic]


class Token(BaseModel):
    access_token: str
    token_type: str


class FilterPage(BaseModel):
    # 防止传参为负数
    offset: int = Field(0, ge=0)
    limit: int = Field(100, ge=1)


# 新增任务类，控制进出的api输出和输入
class TodoSchema(BaseModel):
    title: str
    description: str
    state: TodeState


class TodoPublic(TodoSchema):
    id: int


class TodoList(BaseModel):
    todos: list[TodoPublic]


# 设置多个搜索参数，使用这个FilterPage，还能额外使用页数和限制
class FileterTodo(FilterPage):
    title: str | None = Field(None, min_length=2, max_length=20)
    description: str | None = Field(None, min_length=3, max_length=30)
    state: TodeState | None = None


# 跟新任务
class TodoUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    state: TodeState | None = None
