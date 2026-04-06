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
└── StopProcessing - 中断处理流程（用于预处理器）
```

### 异常使用原则
- **不要**捕获过于宽泛的 `Exception`，应捕获具体异常类型
- 自定义异常必须继承自 `EasyBotException`
- 异常消息应包含足够的上下文信息便于调试
- API 错误必须包含错误码和追踪 ID

## 类型系统使用

### 类型别名定义
为复杂或重复使用的类型定义别名：
```python
MessageContent = Union[str, MessagesModel.Message, ...]
```

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

### 第三方库依赖
- `aiohttp >= 3.9.0` - HTTP 客户端（异步）
- `pyyaml >= 6.0` - YAML 配置解析
- 不要引入未在 `requirements.txt` 或 `pyproject.toml` 中声明的依赖

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
