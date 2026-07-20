from datetime import datetime
from enum import Enum

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import (
    Mapped,
    mapped_as_dataclass,
    mapped_column,
    registry,
    relationship,
)

table_registry = registry()


class TodeState(str, Enum):
    draft = 'draft'
    todo = 'todo'
    doing = 'doing'
    done = 'done'
    trash = 'trash'


@mapped_as_dataclass(table_registry)
class User:
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    # server_default, 在对象实例化的时候执行此函数
    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )

    # 声明俩者存在一对多的关系， 建立俩者的双向关系， user.todos
    todos: Mapped[list['Todo']] = relationship(
        init=False,
        cascade='all, delete-orphan',
        lazy='selectin',
    )


# 新建任务类，任务的外键是用户user
@mapped_as_dataclass(table_registry)
class Todo:
    __tablename__ = 'todos'

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    title: Mapped[str]
    description: Mapped[str]
    state: Mapped[TodeState]

    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
