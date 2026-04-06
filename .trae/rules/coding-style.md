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
