---
alwaysApply: true
description: 适用于所有 Python 文件的代码格式化、命名规范和代码风格规则
---

# 代码格式与风格规范

## 格式化工具配置

### Black 配置
- 行宽限制：**88 字符**
- 目标 Python 版本：3.10, 3.11, 3.12, 3.13
- 所有 `.py` 和 `.pyi` 文件必须通过 black 格式化检查

### Import 排序
- 使用 `isort` 对 import 语句进行排序
- 标准库导入 → 第三方库导入 → 本地应用导入
- 每组之间用空行分隔

## 命名规范

### 变量和函数
- 使用 **snake_case** 命名
- 示例：`bot_id`, `api_timeout`, `get_guild_list()`

### 类名
- 使用 **PascalCase** 命名
- 示例：`Bot`, `API`, `LoggerManager`

### 常量
- 使用 **UPPER_SNAKE_CASE** 命名
- 示例：`DEFAULT_FORMAT`, `MAX_RETRY_COUNT`

### 私有成员
- 使用单下划线前缀：`_bot_id`, `_http_client`
- 受保护属性使用单下划线前缀

### 特殊命名约定
- 数据模型类以功能域为前缀或后缀：`GuildMessage`, `UserInfo`
- 异常类以 `Error` 或 `Exception` 结尾：`APIError`, `NetworkError`
- 工厂方法或构造方法：`from_dict()`, `from_json()`

## 代码结构

### 文件头部
每个 Python 文件应包含：
```python
#!/usr/bin/env python3
"""
模块简短描述

详细说明模块的功能、提供的类/函数列表。
"""
```

### 类定义顺序
1. 文档字符串（docstring）
2. 类属性和类变量
3. `__init__` 方法
4. 属性装饰器（@property）
5. 公共方法
6. 私有方法（以下划线开头）
7. 特殊方法（__enter__, __exit__ 等）

### 函数/方法文档字符串格式
使用 Google 风格的 docstring：
```python
def method_name(self, param1: str, param2: int) -> bool:
    """
    方法简短描述

    详细说明（可选）

    Args:
        param1: 参数1说明
        param2: 参数2说明

    Returns:
        返回值说明

    Raises:
        ExceptionType: 异常触发条件

    Examples:
        >>> obj.method_name("test", 42)
        True
    """
```

## 空行和缩进

- 顶级定义之间使用 **2 个空行**
- 类内部方法之间使用 **1 个空行**
- 缩进使用 **4 个空格**（不使用 Tab）
- 使用隐式字符串连接而非显式 `+` 拼接长字符串

## 类型注解

- 所有公共 API 必须包含完整的类型提示
- 使用 `|` 语法进行联合类型注解（Python 3.10+）：`str | None`
- 复杂类型使用 `typing` 模块：`list[Model.Guild]`, `dict[str, Any]`
- 回调函数类型使用 `Callable[[参数类型], 返回值类型]`

## 注释规范

- 注释应解释**为什么**这样做，而不是做了什么
- 使用中文编写注释（与用户规则保持一致）
- 避免显而易见的注释，如 `# 增加计数器 i += 1`
- 对于复杂逻辑，添加行内注释说明设计决策原因

## 代码组织最佳实践

### 模块导入顺序
```python
# 1. 标准库
import asyncio
import logging
from typing import TYPE_CHECKING, Any, Callable

# 2. 第三方库
import aiohttp

# 3. 本地应用导入
from .exceptions import APIError
from .models import Model

# 4. TYPE_CHECKING 导入（避免循环依赖）
if TYPE_CHECKING:
    from .bot import Bot
```

### 类属性定义顺序
```python
class Bot:
    """Bot 类文档字符串"""

    # 类常量
    DEFAULT_TIMEOUT = 20

    # 类变量
    _instances: dict[str, "Bot"] = {}

    # 实例初始化
    def __init__(self, app_id: str, app_secret: str):
        self._app_id = app_id
        self._app_secret = app_secret

    # 属性装饰器
    @property
    def app_id(self) -> str:
        return self._app_id

    # 公共方法
    def start(self) -> None:
        pass

    # 私有方法
    def _initialize(self) -> None:
        pass

    # 上下文管理器
    async def __aenter__(self) -> "Bot":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        await self.stop_async()
        return False
```

### 函数参数设计
- 必需参数在前，可选参数在后
- 使用类型注解和默认值
- 避免可变默认参数（如 `[]`, `{}`）

```python
# 好的做法
def send_message(
    self,
    channel_id: str,
    content: str,
    mention: bool = False,
    reply_to: str | None = None,
) -> Model.Message:
    pass

# 不好的做法
def send_message(self, channel_id, content, mention=False, reply_to=None):
    pass

# 避免可变默认参数
def add_items(self, items: list | None = None):  # 好
    if items is None:
        items = []

def add_items(self, items=[]):  # 不好！
    pass
```

## 错误处理风格

### 异常捕获
- 捕获具体异常而非宽泛的 `Exception`
- 使用 `as` 语法绑定异常变量
- 记录异常信息用于调试

```python
# 好的做法
try:
    result = await self.api.call()
except APIError as e:
    self.logger.error(f"API 调用失败: {e}")
    raise
except asyncio.TimeoutError as e:
    self.logger.warning(f"请求超时: {e}")
    raise NetworkError("请求超时") from e

# 不好的做法
try:
    result = await self.api.call()
except Exception:  # 太宽泛
    pass  # 吞掉异常
```

### 异常链
使用 `raise ... from` 保留原始异常信息：
```python
try:
    data = json.loads(response_text)
except json.JSONDecodeError as e:
    raise ValidationError("无效的 JSON 数据") from e
```

## 代码复杂度控制

### 函数长度
- 单个函数不超过 50 行（不含文档字符串）
- 超过 30 行考虑拆分

### 圈复杂度
- 单个函数的分支不超过 5 个
- 嵌套层级不超过 3 层
- 使用早返回（early return）减少嵌套

```python
# 好的做法：早返回
def process_message(self, msg: Model.GuildMessage) -> None:
    if not msg.content:
        return

    if not self._is_valid(msg):
        self.logger.warning("无效消息")
        return

    # 主逻辑
    self._handle(msg)

# 不好的做法：深层嵌套
def process_message(self, msg: Model.GuildMessage) -> None:
    if msg.content:
        if self._is_valid(msg):
            # 主逻辑
            self._handle(msg)
        else:
            self.logger.warning("无效消息")
```

## 文档字符串模板

### 模块级文档
```python
"""
API 封装模块

提供对 QQ 机器人 HTTP API 的封装，包括：
- 频道管理 API
- 消息发送 API
- 成员管理 API

使用示例：
    bot = Bot(app_id="...", app_secret="...")
    guilds = await bot.api.get_guild_list()
"""
```

### 类级文档
```python
class API:
    """
    API 封装类

    提供对 QQ 机器人 HTTP API 的完整封装，支持：
    - 频道、子频道管理
    - 消息发送与回复
    - 成员权限管理
    - 用户信息获取

    Attributes:
        bot: 关联的 Bot 实例
        logger: 日志记录器

    Examples:
        >>> api = API(bot)
        >>> guilds = await api.get_guild_list()
    """
```

### 方法级文档
```python
async def send_message(
    self,
    channel_id: str,
    content: str,
    mention: bool = False,
) -> Model.Message:
    """
    发送频道消息

    Args:
        channel_id: 子频道 ID
        content: 消息内容
        mention: 是否 @ 全体成员（需要权限）

    Returns:
        发送的消息对象

    Raises:
        APIError: API 调用失败
        PermissionError: 无权限 @ 全体成员

    Examples:
        >>> msg = await api.send_message("123456", "Hello World")
        >>> print(msg.id)
    """
```
