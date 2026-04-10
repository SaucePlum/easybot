---
alwaysApply: true
description: Python 语言特定约定，包括 dataclass 使用、异常体系、类型系统和标准库使用
---

# Python 语言约定

## Dataclass 使用规范

### 模型定义
- 所有数据模型使用 `@dataclass` 装饰器定义
- 继承自 `BaseModel` 基类（位于 `easybot/models.py`）
- 字段必须包含类型注解和默认值

```python
@dataclass
class GuildMessage(BaseModel):
    """频道消息模型"""
    guild_id: str = ""
    channel_id: str = ""
    content: str = ""
    _raw_data: dict | None = field(default=None, repr=False, compare=False)
```

### 字段定义规则
- 内部字段使用 `_` 前缀：`_raw_data`, `_reply_strategy`
- 不参与比较的字段标记：`repr=False, compare=False`
- 提供默认值以避免初始化错误
- 使用 `field()` 进行复杂默认值配置

### 模型方法约定
- 提供 `from_dict()` 类方法用于从字典创建实例
- 提供 `to_dict()` 实例方法用于序列化（如需要）
- 使用缓存机制优化字段信息获取（参考 BaseModel 实现）

## 异常体系

### 异常层次结构
```
EasyBotException (基类)
├── APIError - API 调用错误（含 code, message, trace_id）
├── AuthenticationError - 认证失败
├── PermissionError - 权限不足
├── RateLimitError - 频率限制（含 retry_after）
├── NetworkError - 网络连接问题
├── ValidationError - 参数验证失败
├── StopProcessing - 中断处理流程（用于预处理器）
├── WaitError - 等待任务被意外删除
└── WaitTimeoutError - 等待超时
```

### 异常使用原则
- **不要**捕获过于宽泛的 `Exception`，应捕获具体异常类型
- 自定义异常必须继承自 `EasyBotException`
- 异常消息应包含足够的上下文信息便于调试
- API 错误必须包含错误码和追踪 ID

### 特殊异常说明

#### StopProcessing
用于在预处理器中中断事件处理流程：
```python
async def preprocessor(event):
    if should_skip(event):
        raise StopProcessing("跳过此事件")
```

#### WaitError / WaitTimeoutError
用于会话等待机制：
```python
try:
    result = await session.wait_for("key", timeout=60)
except WaitTimeoutError:
    # 等待超时
    pass
except WaitError:
    # 等待任务被意外删除
    pass
```

## 类型系统使用

### TYPE_CHECKING 使用
- 导入仅在类型注解中使用的模块时，使用 `TYPE_CHECKING`
- 避免循环导入问题：

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .bot import Bot
```

### 泛型使用
- 使用 `TypeVar` 定义泛型约束
- 在类方法中使用泛型返回正确类型：
```python
T = TypeVar("T", bound="BaseModel")

def from_dict(cls: type[T], data: dict) -> T:
    ...
```

### 常用类型注解
```python
from typing import Any, Callable, Optional, Union
from collections.abc import Awaitable

# 联合类型（Python 3.10+）
result: str | None = None

# 可调用类型
handler: Callable[[Model.GuildMessage], Awaitable[None]]

# 字典类型
data: dict[str, Any] = {}

# 列表类型
items: list[Model.Guild] = []
```

## 标准库和第三方库使用

### 优先使用的标准库
- `asyncio` - 异步编程
- `logging` / `logging.handlers` - 日志系统
- `dataclasses` - 数据类定义
- `enum` - 枚举类型
- `pathlib` - 路径操作（优先于 os.path）
- `datetime` - 时间处理
- `json` / `yaml` - 数据序列化
- `threading` - 线程安全（用于 LoggerManager 等）
- `base64` / `hashlib` - 编码和加密辅助
- `collections.abc` - 抽象基类（Callable, Iterable 等）
- `contextlib` - 上下文管理器工具
- `pickle` - 对象序列化（用于会话数据持久化）
- `os` / `sys` - 系统接口

### 第三方库依赖
```toml
[project]
dependencies = [
    "aiohttp>=3.9.0",      # HTTP 客户端（异步）
    "pyyaml>=6.0",         # YAML 配置解析
]

[project.optional-dependencies]
crypto = ["cryptography>=3.0"]  # Ed25519 签名验证（可选）
```

### 避免的做法
- 不要重复造轮子，优先使用标准库或成熟第三方库
- 不要在不必要时引入重量级依赖
- 不要使用已废弃的模块或函数

## 特殊模式

### 属性装饰器作为事件注册器
使用 `@property` 创建装饰器风格的 API：
```python
@property
def on_guild_message(self):
    """事件装饰器"""
    def decorator(func: Callable):
        self._register_handler("AT_MESSAGE_CREATE", func, Intent.PUBLIC_GUILD_MESSAGES)
        return func
    return decorator
```

### IntEnum 用于标志位
使用 `IntEnum` 定义位掩码常量（如 Intent 系统）：
```python
class Intent(IntEnum):
    PUBLIC_GUILD_MESSAGES = 1 << 30
    GROUP_AND_C2C_EVENT = 1 << 25
```

### 上下文管理器
使用 `@contextmanager` 装饰器创建上下文管理器，配合 `ContextVar` 实现协程隔离：
```python
from contextlib import contextmanager
from contextvars import ContextVar

_current_obj_var: ContextVar = ContextVar("_current_obj", default=None)

@contextmanager
def bind(self, obj):
    """绑定对象的上下文管理器"""
    token = self._current_obj_var.set(obj)
    try:
        yield BoundSession(self, obj)
    finally:
        self._current_obj_var.reset(token)
```

## 枚举类型使用

### StrEnum 使用
Python 3.11+ 提供 `StrEnum`，用于自定义字符串枚举：
```python
from enum import StrEnum

class MyEnum(StrEnum):
    """自定义字符串枚举示例"""
    A = "A"
    B = "B"
```

EasyBot 内置的会话作用域 `Scope` 是常量类（值为大写字符串）：
```python
from easybot import Scope

Scope.USER
Scope.GUILD
Scope.CHANNEL
Scope.GROUP
Scope.GLOBAL
```

### IntFlag 使用
用于可组合的标志位：
```python
from enum import IntFlag

class Permission(IntFlag):
    READ = 1
    WRITE = 2
    EXECUTE = 4
    ADMIN = READ | WRITE | EXECUTE
```

## 数据模型最佳实践

### BaseModel 实现
```python
@dataclass
class BaseModel:
    """模型基类"""

    @classmethod
    @cache
    def _get_fields(cls) -> dict[str, Any]:
        """获取字段信息（缓存）"""
        return {f.name: f for f in fields(cls)}

    @classmethod
    def from_dict(cls: type[T], data: dict | None) -> T | None:
        """从字典创建实例"""
        if data is None:
            return None

        fields = cls._get_fields()
        filtered = {k: v for k, v in data.items() if k in fields}
        return cls(**filtered)
```

### 模型继承
```python
@dataclass
class Message(BaseModel):
    """消息基类"""
    id: str = ""
    content: str = ""

@dataclass
class GuildMessage(Message):
    """频道消息"""
    guild_id: str = ""
    channel_id: str = ""
```

## 函数和方法的类型注解

### 异步方法
```python
async def send_message(
    self,
    channel_id: str,
    content: str,
) -> Model.Message:
    """发送消息"""
    pass
```

### 回调函数类型
```python
from collections.abc import Callable, Awaitable

# 无参数异步回调
Callback = Callable[[], Awaitable[None]]

# 带参数的异步回调
MessageHandler = Callable[[Model.GuildMessage], Awaitable[None]]

# 注册处理器
def on_message(self, handler: MessageHandler) -> None:
    self._handlers.append(handler)
```

### 可选参数和默认值
```python
def get_user(
    self,
    user_id: str,
    guild_id: str | None = None,  # 可选参数
) -> Model.User:
    pass
```

## 属性和描述符

### @property 使用
```python
class Bot:
    def __init__(self, app_id: str):
        self._app_id = app_id

    @property
    def app_id(self) -> str:
        """只读属性"""
        return self._app_id

    @property
    def api(self) -> API:
        """延迟初始化属性"""
        if self._api is None:
            self._api = API(self)
        return self._api
```

### @cached_property 使用
Python 3.8+ 提供 `@cached_property`：
```python
from functools import cached_property

class Bot:
    @cached_property
    def logger(self) -> Logger:
        """缓存属性，只计算一次"""
        return Logger(bot_id=self.app_id)
```

## 类方法和静态方法

### @classmethod 使用
用于工厂方法和替代构造器：
```python
class Protocol:
    @classmethod
    def websocket(cls, url: str | None = None) -> WebSocketProtocol:
        """创建 WebSocket 协议实例"""
        return WebSocketProtocol(url)

    @classmethod
    def webhook(cls, port: int = 8080) -> WebhookProtocol:
        """创建 Webhook 协议实例"""
        return WebhookProtocol(port)
```

### @staticmethod 使用
用于不需要访问实例或类的工具方法：
```python
class Utils:
    @staticmethod
    def validate_id(id_str: str) -> bool:
        """验证 ID 格式"""
        return id_str.isdigit()
```

## 模块组织

### __init__.py 设计
```python
"""
EasyBot SDK

QQ 机器人开发 SDK，支持公域和私域机器人。
"""

from .bot import Bot
from .api import API
from .models import Model, MessagesModel
from .builders import Builders
from .protocol import Proto
from .logger import Logger
from .exceptions import (
    EasyBotException,
    APIError,
    # ...
)
from .version import __version__

__all__ = [
    "Bot",
    "API",
    "Model",
    # ...
    "__version__",
]
```

### 相对导入
在包内部使用相对导入：
```python
# 好的做法
from .exceptions import APIError
from .models import Model

# 不好的做法（在包内部）
from easybot.exceptions import APIError
```
