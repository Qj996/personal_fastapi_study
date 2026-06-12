# FastAPI 学习笔记

> 项目：`fast_zero` | 日期：2026-06-12
> 包管理：Poetry | 测试：pytest + coverage | ORM：SQLAlchemy 2.x

---

## 一、当前已掌握的知识点

### 1.1 项目结构

```
fast_zero/
├── fast_zero/              # 应用包
│   ├── __init__.py
│   ├── app.py              # FastAPI 路由入口
│   ├── models.py           # SQLAlchemy ORM 模型
│   └── schemas.py          # Pydantic 数据校验
├── tests/                  # 测试目录
│   ├── __init__.py
│   ├── conftest.py         # pytest 夹具（fixtures）
│   ├── test_app.py         # 路由测试
│   └── test_db.py          # 数据库模型测试
├── pyproject.toml          # 项目配置（依赖/工具）
├── poetry.lock
└── README.md
```

### 1.2 FastAPI 基础

```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

# GET 路由 - 返回 JSON
@app.get('/')
def read_root():
    return {'message': 'Olá Mundo!'}

# GET 路由 - 自定义状态码 + 返回 HTML
@app.get("/test", status_code=HTTPStatus.OK, response_class=HTMLResponse)
def my_try():
    return "<html>...</html>"

# POST 路由 - 接收 JSON 请求体 + response_model 过滤输出
@app.post("/create_user", status_code=HTTPStatus.CREATED, response_model=UserPublic)
def create_user(user: UserSchemas):
    user_id = UserDb(**user.model_dump(), id=len(database) + 1)
    database.append(user_id)
    return user_id
```

**掌握要点：**

| 概念 | 说明 |
|------|------|
| `response_model` | 自动过滤/转换返回值，只暴露指定字段（如隐藏 password） |
| `status_code` | 自定义 HTTP 响应码，POST 常用 `201 CREATED` |
| `response_class` | 指定响应格式，默认 JSON，可切换为 `HTMLResponse` |
| 类型注解 | FastAPI 根据参数类型自动解析请求体、做数据校验 |

### 1.3 Pydantic Schema（数据校验层）

```python
from pydantic import BaseModel, EmailStr

# 请求 Schema —— 客户端发送的数据格式
class UserSchemas(BaseModel):
    user_name: str
    email: EmailStr       # 自动校验邮箱格式
    password: str

# 响应 Schema —— 返回给客户端的数据（隐藏敏感字段）
class UserPublic(BaseModel):
    user_name: str
    email: EmailStr

# 继承复用 —— 在请求 Schema 基础上扩展
class UserDb(UserSchemas):
    id: int               # 数据库生成的 ID
```

**Pydantic 数据流向：**

```
客户端请求 → UserSchemas（校验输入）
                    ↓ model_dump() 转 dict → ** 解包
                UserDb（存储模型，含 id）
                    ↓
客户端响应 ← UserPublic（过滤输出）← response_model 自动转换
```

> `model_dump()` 把 Pydantic 对象转成字典，`**` 解包后传给下一个模型构造函数。

### 1.4 SQLAlchemy ORM 模型

```python
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_as_dataclass, mapped_column, registry

table_registry = registry()

@mapped_as_dataclass(table_registry)
class User:
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
```

**关键概念：**

| 语法 | 含义 |
|------|------|
| `registry()` | 注册表，管理所有 ORM 映射类 |
| `@mapped_as_dataclass` | 既是 ORM 映射类，又是 Python dataclass |
| `Mapped[int]` | 声明数据库列的类型 |
| `init=False` | 构造 `__init__` 时不包含此字段（由数据库生成） |
| `primary_key=True` | 主键 |
| `unique=True` | 唯一约束 |
| `server_default=func.now()` | 数据库端默认值，INSERT 时调用 `now()` |

### 1.5 测试体系

#### Fixture：数据库会话

```python
@pytest.fixture
def session():
    engine = create_engine('sqlite:///:memory:')       # 内存数据库（不落盘）
    table_registry.metadata.create_all(engine)          # 建表
    with Session(engine) as session:
        yield session                                   # 提供给测试函数
    table_registry.metadata.drop_all(engine)            # 测试结束删表
    engine.dispose()
```

**生命周期：**

```
创建引擎 → 建表 → 提供 Session → [测试执行] → 删表 → 销毁引擎
```

#### Fixture：冻结时间

```python
@contextmanager
def _mock_db_time(*, model, time=datetime(2024, 1, 1)):
    def fake_time_hook(mapper, connection, target):
        if hasattr(target, "created_at"):
            target.created_at = time
    event.listen(model, "before_insert", fake_time_hook)  # 注册钩子
    yield time
    event.remove(model, "before_insert", fake_time_hook)  # 清理钩子

@pytest.fixture
def mock_db_time():
    return _mock_db_time
```

**使用方式：**

```python
def test_user_db(session, mock_db_time):
    with mock_db_time(model=User) as time:   # 进入 with：绑定钩子
        new_user = User(...)                  # 此时创建的用户，created_at 被固定
        session.add(new_user)
        session.commit()
    # 退出 with：钩子自动移除
```

#### contextmanager 装饰器本质

```python
@contextmanager          # 等价于一个类：
def my_cm():             # __enter__() → 执行 yield 之前
    setup()              # __exit__()  → 执行 yield 之后（异常也会执行）
    yield value
    teardown()
```

#### TestClient 测试路由

```python
from fastapi.testclient import TestClient
from fast_zero.app import app

client = TestClient(app)

def test_root_deve():
    response = client.get('/')
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'Olá Mundo!'}
```

#### SQLAlchemy 查询

```python
from sqlalchemy import select

# scalar() —— 返回单个结果，无结果返回 None，多条抛异常
user = session.scalar(select(User).where(User.username == "alice"))

# dataclass → dict 用于断言
from dataclasses import asdict
assert asdict(user) == {"id": 1, "username": "...", ...}
```

### 1.6 工程化工具链

| 工具 | 用途 | 命令 |
|------|------|------|
| **Poetry** | 依赖管理 | `poetry add/install` |
| **Ruff** | 代码检查+格式化 | `ruff check` / `ruff format` |
| **pytest** | 测试运行 | `pytest -s -x -vv` |
| **pytest-cov** | 覆盖率 | `--cov=fast_zero` |
| **taskipy** | 快捷任务 | `task lint` / `task test` |

---

## 二、FastAPI 学习路线图（5 阶段）

### 🔵 第一阶段：路由与请求参数

| # | 知识点 | 核心概念 | 状态 |
|---|--------|----------|------|
| 1.1 | **路径参数** | `@app.get("/users/{user_id}")` — 必填参数在 URL 中 | ⬜ |
| 1.2 | **查询参数** | `?page=1&size=10` — 可选参数，用于过滤/分页 | ⬜ |
| 1.3 | **PUT 全量更新** | 替换整个资源，需传所有字段 | ⬜ |
| 1.4 | **DELETE 删除** | 删除指定资源 | ⬜ |
| 1.5 | **PATCH 部分更新** | 只传要修改的字段 | ⬜ |
| 1.6 | **参数组合** | 路径参数 + 查询参数 + 请求体同时使用 | ⬜ |

### 🟢 第二阶段：数据库 CRUD 完善

| # | 知识点 | 核心概念 | 状态 |
|---|--------|----------|------|
| 2.1 | **集成 Session** | 用 `Depends()` 注入数据库会话，替代 `database = []` | ⬜ |
| 2.2 | **完整 CRUD** | Create / Read / Update / Delete 全部实现 | ⬜ |
| 2.3 | **依赖注入** | `Depends(get_session)` — FastAPI 最核心的设计模式 | ⬜ |
| 2.4 | **Session 生命周期** | 请求进来创建会话，响应返回关闭会话 | ⬜ |
| 2.5 | **表关系** | ForeignKey、relationship、一对多、多对多 | ⬜ |
| 2.6 | **Alembic 迁移** | 数据库版本管理，`alembic revision --autogenerate` | ⬜ |

### 🟡 第三阶段：认证与安全

| # | 知识点 | 核心概念 | 状态 |
|---|--------|----------|------|
| 3.1 | **密码哈希** | passlib / bcrypt — 永不存储明文密码 | ⬜ |
| 3.2 | **OAuth2 流程** | `OAuth2PasswordBearer` — FastAPI 内置支持 | ⬜ |
| 3.3 | **JWT Token** | `python-jose` — 签发、验证、过期处理 | ⬜ |
| 3.4 | **登录接口** | `POST /token` — 返回 access_token | ⬜ |
| 3.5 | **保护路由** | `get_current_user` 依赖，只有登录用户能访问 | ⬜ |
| 3.6 | **权限控制** | 普通用户 vs 管理员，角色区分 | ⬜ |

### 🟠 第四阶段：FastAPI 核心特性

| # | 知识点 | 核心概念 | 状态 |
|---|--------|----------|------|
| 4.1 | **Depends() 深入** | 依赖嵌套、依赖缓存、yield 依赖 | ⬜ |
| 4.2 | **异常处理器** | `@app.exception_handler` — 统一错误响应格式 | ⬜ |
| 4.3 | **中间件** | `@app.middleware("http")` — 请求/响应的钩子 | ⬜ |
| 4.4 | **CORS** | 跨域资源共享配置 | ⬜ |
| 4.5 | **后台任务** | `BackgroundTasks` — 响应后异步执行 | ⬜ |
| 4.6 | **路由分组** | `APIRouter` — 模块化拆分路由 | ⬜ |
| 4.7 | **字段验证器** | `@field_validator` — 自定义校验逻辑 | ⬜ |

### 🔴 第五阶段：进阶实战

| # | 知识点 | 核心概念 | 状态 |
|---|--------|----------|------|
| 5.1 | **环境配置** | `pydantic-settings`（已安装）— 多环境管理 | ⬜ |
| 5.2 | **文件上传** | `UploadFile` — 处理文件上传 | ⬜ |
| 5.3 | **异步数据库** | `async SQLAlchemy` — 非阻塞数据库操作 | ⬜ |
| 5.4 | **WebSocket** | 实时双向通信 | ⬜ |
| 5.5 | **Docker 部署** | 容器化 + docker-compose | ⬜ |
| 5.6 | **分页与过滤** | 通用分页方案、动态过滤 | ⬜ |

---

## 三、重点复习卡片

### 🔑 核心概念 1：Pydantic 数据流转

```
请求体(JSON) → UserSchemas (输入校验)
                    ↓ model_dump()
                  dict
                    ↓ ** 解包
                UserDb (存储模型，含 id)
                    ↓ response_model=UserPublic
              返回 JSON (password 被过滤)
```

> **记忆点**：输入用完整 Schema 校验，输出用精简 Schema 过滤敏感字段。

### 🔑 核心概念 2：response_model 的过滤机制

`response_model` 只返回该模型中定义的字段，其余字段**自动丢弃**。

```python
# UserDb 有：id, user_name, email, password
@app.post("/create_user", response_model=UserPublic)
# UserPublic 只有：user_name, email
# → 返回 JSON 中不会出现 id 和 password
```

### 🔑 核心概念 3：mapped_as_dataclass 的本质

`@mapped_as_dataclass` = ORM 声明式映射 + Python dataclass，二合一。

| 特性 | 说明 |
|------|------|
| ORM 能力 | 可以 `session.add()`、`session.query()` |
| Dataclass 能力 | `asdict(user)`、自动 `__init__`、`__repr__` |
| `init=False` | 字段不出现在 `__init__` 参数中（由数据库生成） |
| `server_default` | 数据库端的默认值（SQL 层面） |

### 🔑 核心概念 4：pytest fixture 的 yield 模式

```python
@pytest.fixture
def session():
    # === SETUP ===
    engine = create_engine('sqlite:///:memory:')
    table_registry.metadata.create_all(engine)
    with Session(engine) as session:
        yield session          # === 测试函数在这里执行 ===
    # === TEARDOWN ===
    table_registry.metadata.drop_all(engine)
    engine.dispose()
```

> **核心**：`yield` 之前是准备阶段，`yield` 之后是清理阶段（无论测试通过或失败都会执行清理）。

### 🔑 核心概念 5：SQLAlchemy event 钩子

```python
# 在每条数据 insert 之前触发，可用于固定时间戳
event.listen(User, "before_insert", fake_time_hook)
# 测试结束后必须移除，否则污染其他测试
event.remove(User, "before_insert", fake_time_hook)
```

### 🔑 核心概念 6：select + scalar 查询模式

```python
from sqlalchemy import select

# select() 构建查询语句
stmt = select(User).where(User.username == "alice")

# scalar() 执行并返回单个对象
user = session.scalar(stmt)   # 0 条 → None，>1 条 → 抛异常
```

### 🔑 核心概念 7：FastAPI 路由参数自动解析

FastAPI 根据参数声明**自动判断**参数来源：

| 声明方式 | 参数来源 | 示例 |
|----------|----------|------|
| 函数参数在路径中 | 路径参数 | `def get(user_id: int)` + `/users/{user_id}` |
| 函数参数不在路径中 | 查询参数 | `def list(page: int = 1)` → `?page=1` |
| Pydantic 类型参数 | 请求体(JSON) | `def create(user: UserSchemas)` |

---

## 四、当前代码中的关键注解解读

### app.py

```python
# model_dump 将模型实例转换为 json 字典
# —— 也就是将属性转换为键值对
user_id = UserDb(**user.model_dump(), id=len(database) + 1)
```

| 步骤 | 代码 | 结果 |
|------|------|------|
| 1 | `user.model_dump()` | `{"user_name": "...", "email": "...", "password": "..."}` |
| 2 | `**` 解包 | 变成关键字参数 |
| 3 | `id=len(database)+1` | 追加 id 参数 |
| 4 | `UserDb(...)` | 构造完整数据库模型 |

### conftest.py

```python
# 装饰器，作用是每个测试得到全新的数据库环境
@pytest.fixture
def session():
    ...  # SQLite 内存数据库，测试隔离
```

> 每个测试独立使用一个全新的空数据库，测试之间不互相影响。

### schemas.py

```python
password: str    # 注释有误，应为"密码字段"而非"确保收到的是一个邮件"
```

> 真正的邮箱校验由 `EmailStr` 类型完成。

---

## 五、每日/每周复习计划

| 频次 | 内容 | 时长 |
|------|------|------|
| **每日** | 敲一遍当天的路由代码（手感记忆） | 30 min |
| **每 2 天** | 阅读官方文档对应章节 + 写测试 | 1 h |
| **每周** | 回顾错误笔记、用自己话解释核心概念 | 30 min |
| **每阶段** | 做一个小项目（如 Todo API、Blog API） | 2-3 天 |

### 快速自测清单

- [ ] 能不能从零写出一个带 POST 的 FastAPI 应用？
- [ ] 能不能手写 `pytest.fixture` 的 setup/teardown 模式？
- [ ] 能不能解释 `response_model` 和 `model_dump()` 的作用？
- [ ] 能不能说清楚 `init=False` 和 `server_default` 的区别？
- [ ] 能不能理解 SQLAlchemy `select` + `scalar` 的查询模式？
- [ ] 能不能解释 `contextmanager` 装饰器的工作原理？

---

## 六、下一步行动

**当前最自然的推进方向：**

```
将 app.py 中的 database = [] 替换为真正的 SQLAlchemy 数据库操作
→ 引入 Depends() 依赖注入
→ 实现完整的 User CRUD
```

**快速预览下一阶段会用到的模式：**

```python
# ---- 依赖注入：获取数据库会话 ----
from fastapi import Depends

def get_session():
    with Session(engine) as session:
        yield session

# ---- 路由中使用 ----
@app.post("/users", response_model=UserPublic)
def create_user(user: UserSchemas, session: Session = Depends(get_session)):
    db_user = User(**user.model_dump())
    session.add(db_user)
    session.commit()
    session.refresh(db_user)      # 获取数据库生成的 id
    return db_user
```

---

> 📌 持续更新中 | 下一阶段：路由参数 + 数据库 CRUD
