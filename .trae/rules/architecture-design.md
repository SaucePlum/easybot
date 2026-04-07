---
alwaysApply: true
description: 架构设计原则，包括模块组织、SOLID 原则、内部模块约定和公共 API 设计
---

# 架构设计原则

## 项目结构组织

### 顶层目录结构
```
easybot/
├── __init__.py          # 公共 API 导出（__all__ 定义）
├── bot.py               # Bot 主类
├── api.py               # API 封装层
├── models.py            # 数据模型定义
├── builders.py          # 消息构建器
├── protocol.py          # 协议管理（WebSocket/Webhook/Remote Webhook）
├── session.py           # 会话管理
├── plugins.py           # 插件系统
├── logger.py            # 日志系统
├── exceptions.py        # 异常定义
├── sandbox.py           # 沙箱环境
├── version.py           # 版本号
├── crypto/              # 加密模块（Ed25519 签名验证）
│   ├── __init__.py
│   └── ed25519.py
└── _internal/           # 内部实现细节（不作为公共 API）
    ├── __init__.py
    ├── http_client.py   # HTTP 客户端封装
    ├── ws_client.py     # WebSocket 客户端
    ├── ws_base.py       # WebSocket 基类
    ├── event_dispatcher.py  # 事件分发器
    ├── event_utils.py   # 事件处理工具
    ├── message_utils.py # 消息处理工具
    ├── intent.py        # Intent 计算和管理
    ├── lifecycle.py     # 生命周期管理
    ├── reply_strategy.py # 消息回复策略
    ├── dedup.py         # 消息去重
    ├── constants.py     # 常量定义
    └── ...              # 其他内部模块
```

### _internal 模块约定
- **用途**：存放不应被用户直接使用的内部实现
- **导入限制**：外部代码**禁止**直接从 `_internal` 导入任何内容
- **变更通知**：_internal 模块的 API 可能在不通知的情况下更改
- **测试例外**：单元测试可以导入 _internal 进行白盒测试

### crypto 模块说明
- **用途**：提供加密相关功能，如 Ed25519 签名验证
- **使用场景**：Webhook 消息签名验证、安全通信等
- **依赖**：可选依赖 `cryptography` 库，无依赖时使用纯 Python 实现

## SOLID 原则应用

### 单一职责原则 (SRP)
每个类/模块只负责一个明确的功能：
- `Bot` - 机器人生命周期和事件注册
- `API` - HTTP API 调用封装
- `Model` - 数据结构定义
- `Logger` - 日志记录
- `SessionManager` - 会话状态管理
- `Plugins` - 插件和命令管理
- `Protocol` - 连接协议抽象

### 开闭原则 (OCP)
- 通过装饰器模式扩展事件处理能力（`@bot.on_xxx`）
- 通过插件系统扩展功能，无需修改核心代码
- 使用策略模式支持多种协议（WebSocket / Webhook / Remote Webhook）

### 里氏替换原则 (LSP)
- 所有异常类可替换基类 `EasyBotException` 使用
- 协议实现类可互换使用（WebSocketProtocol / WebhookProtocol / RemoteWebhookProtocol）
- 模型类都继承自 `BaseModel` 并提供统一接口

### 接口隔离原则 (ISP)
- 公共 API 仅暴露必要的方法和属性
- 内部实现细节隐藏在 `_internal` 中
- 用户不需要了解 HTTP 客户端或 WebSocket 的具体实现

### 依赖倒置原则 (DIP)
- 依赖抽象而非具体实现：Bot → Protocol（接口）→ WebSocket/Webhook/Remote Webhook
- 通过依赖注入传递 Logger 和 API 实例
- 使用 TYPE_CHECKING 避免循环依赖

## 公共 API 设计

### __init__.py 导出规范
只在 `__init__.py` 中导出公共 API：
```python
__all__ = [
    "Bot",
    "API",
    "Model",
    "MessagesModel",
    "Builders",
    "Proto",
    "SandBox",
    "Logger",
    "EasyBotException",
    "APIError",
    "AuthenticationError",
    "PermissionError",
    "RateLimitError",
    "NetworkError",
    "ValidationError",
    "CommandValidScenes",
    "BotAdminManager",
    "BotCommandObject",
    "BoundSession",
    "Plugins",
    "SessionManager",
    "Scope",
    "WaitTimeoutError",
    "WaitError",
    "with_session",
    "StopProcessing",
    "__version__",
]
```

### API 稳定性承诺
- **稳定 API**：Bot, API, Model, Builders, Plugins, SessionManager 等主要类
- **实验性功能**：在文档中标注为实验性的 API
- **内部 API**：_internal 下所有内容，可能随时变更

### 向后兼容性
- 不移除公共 API，使用废弃警告替代
- 新增参数必须提供默认值
- 不改变现有方法的返回值类型（可扩展子类）

## 设计模式应用

### 装饰器模式
用于事件注册：
```python
@property
def on_guild_message(self):
    def decorator(func: Callable):
        self._register_handler(...)
        return func
    return decorator
```

### 工厂模式
用于协议创建和模型创建：
```python
class Proto:
    @staticmethod
    def websocket(...) -> WebSocketProtocol:
        return WebSocketProtocol(...)

@classmethod
def from_dict(cls, data: dict) -> T:
    """从字典创建实例"""
    pass
```

### 单例/管理器模式
用于资源共享：
- `LoggerManager` - 共享日志 handler
- `SessionManager` - 全局会话状态
- `BotAdminManager` - 管理员数据持久化

### 观察者模式
用于事件系统：
- 事件分发器维护处理器列表
- 支持生命周期事件的订阅和发布

### 策略模式
用于消息回复策略：
- `ReplyStrategy` - 根据消息类型选择不同的回复方式
- 支持频道消息、群聊消息、单聊消息、私信等不同场景

## 配置管理

### 初始化参数设计
Bot 类的构造函数接受所有配置项：
```python
bot = Bot(
    app_id="...",
    app_secret="...",
    is_private=False,
    is_sandbox=False,
    sandbox=None,
    protocol=Proto.websocket(),  # 可选，有默认值
    is_retry=3,
    is_log_error=True,
    no_permission_warning=True,
    api_timeout=20,
    is_debug=False,
    auto_load_plugins=False,
    plugins_dir="plugins",
    plugins_recursive=False,
)
```

### 配置优先级
1. 构造函数显式参数
2. 默认值
3. 环境变量（如需要）
4. 配置文件（如插件系统使用 YAML）

## 错误处理架构

### 分层错误处理
1. **用户代码层**：捕获并处理业务异常
2. **SDK 层**：记录日志并转换为 SDK 异常
3. **传输层**：处理网络错误并重试

### 异常传播原则
- 底层异常应包装为语义明确的 SDK 异常
- 保持原始异常信息用于调试
- 关键路径必须有错误处理

### 异常体系
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
