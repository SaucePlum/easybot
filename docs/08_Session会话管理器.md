# Session 会话管理器

SessionManager 是 EasyBot SDK 的会话状态管理组件，用于在多轮对话中维护用户/群组的状态信息。它支持多种作用域（Scope），提供超时自动回复、自动持久化和垃圾回收机制。

> **导入**: 通过 `bot.session` 访问（返回 `SessionManager` 实例）
> **模块**: `from easybot import SessionManager`

---

## 核心概念

### 什么是 Session？

在 QQ 机器人开发中，**单次消息处理是无状态的**——每次收到消息时，机器人不知道用户之前说过什么。Session 的作用就是**跨消息持久化状态**，使多轮对话成为可能。

```
用户: "帮我订一张去北京的票"
    ↓ with session.bind(msg): session.new(Scope.USER, "booking", {...})
机器人: "好的，请问什么时间出发？"

用户: "明天上午"
    ↓ session.update(Scope.USER, "booking", {...})
机器人: "已为您预订：北京 → 明天上午，确认吗？"

用户: "确认"
    ↓ session.remove(scope=Scope.USER, key="booking")
机器人: "✅ 订单已提交！"
```

### SessionObject 数据结构

`new()` / `get()` / `update()` 返回的是 `SessionObject` 对象：

| 属性 | 类型 | 说明 |
|------|------|------|
| `scope` | `str` | 会话作用域（如 `"USER"`、`"GUILD"`） |
| `status` | `int` | 会话状态：`0`=活跃(ACTIVE)，`1`=非活跃(INACTIVE) |
| `key` | `Hashable` | 会话键 |
| `data` | `dict` | 会话数据 |
| `identify` | `Hashable \| None` | 作用域内的标识（如 user_id、guild_id） |

### 内部 _SessionObject（开发者一般不直接使用）

SDK 内部使用 `_SessionObject` 存储更详细的会话信息：

| 字段 | 类型 | 说明 |
|------|------|------|
| `status` | `int` | 会话状态 |
| `data` | `dict` | 会话数据字典 |
| `timeout` | `float \| None` | 超时时间（秒），None 表示永不过期 |
| `last_operate` | `float` | 最后操作时间戳 |
| `timeout_reply` | `str \| Message \| ... \| None` | 超时时自动发送的回复内容 |
| `inactive_gc_timeout` | `float` | 非活跃会话的回收等待时间（秒） |
| `gc_timeout_stamp` | `float \| None` | 计划回收的时间戳 |
| `send_reply_on_msg_id_expired` | `bool` | msg_id 过期后是否仍发送消息（默认 False） |

---

## 作用域 Scope

作用域决定了 Session 的**隔离粒度**和**唯一标识**。

### 作用域类型

```python
from easybot import Scope

Scope.USER      # 用户级别
Scope.GUILD     # 频道级别
Scope.CHANNEL   # 子频道级别
Scope.GROUP     # 群聊级别
Scope.GLOBAL    # 全局级别
```

`Scope` 是一个包含字符串常量的类，不是枚举：

```python
class Scope:
    USER = "USER"
    GUILD = "GUILD"
    CHANNEL = "CHANNEL"
    GROUP = "GROUP"
    GLOBAL = "GLOBAL"
```

### 作用域选择指南

| 场景 | 推荐作用域 | 说明 |
|------|-----------|------|
| 用户个人设置/多轮对话 | `USER` | 同一用户在不同场景共享状态 |
| 群内游戏/群活动 | `GROUP` | 群成员共享同一状态 |
| 频道管理功能 | `GUILD` | 频道内所有成员共享 |
| 子频道投票/讨论 | `CHANNEL` | 该子频道的专属状态 |
| 全局计数器/配置 | `GLOBAL` | 所有场景共享同一状态 |

### Identify 自动识别规则

当通过 `bind(msg)` 绑定消息对象后，SDK 会根据消息对象和作用域自动推断标识（identify）：

| 作用域 | 识别字段来源 | 示例 |
|--------|-------------|------|
| `USER` | `msg.author.id` 或 `msg.user_openid` 或其他用户标识字段 | 用户 OpenID |
| `GUILD` | `msg.guild_id` | 频道 ID |
| `CHANNEL` | `msg.channel_id` | 子频道 ID |
| `GROUP` | `msg.group_openid` | 群 OpenID |
| `GLOBAL` | 不适用 | 无需 identify |

---

## 使用方式概览

### 方式一：bind() 上下文管理器（推荐）

使用 `with session.bind(msg)` 绑定当前消息对象，在 `with` 块内直接操作会话：

```python
from easybot import Bot, Scope

bot = Bot(app_id="xxx", app_secret="xxx")

@bot.on_command(command="/book")
async def start_booking(msg):
    with bot.session.bind(msg) as s:
        s.new(
            scope=Scope.USER,
            key="booking",
            data={"step": "ask_destination"},
            timeout=600,
            timeout_reply="⏰ 订票超时",
        )
    await msg.reply("请输入目的地")

@bot.on_guild_message
async def handle_booking(msg):
    with bot.session.bind(msg) as s:
        session = s.get(scope=Scope.USER, key="booking")
        if not session or session.status != 0:
            return

        step = session.data.get("step")
        if step == "ask_destination":
            s.update(scope=Scope.USER, key="booking", data={
                "destination": msg.content, "step": "ask_date",
            })
            await msg.reply(f"目的地: {msg.content}\n请输入出发日期")
```

**要点**：
- `bind(msg)` 返回一个上下文管理器，`as s` 得到的是 `BoundSession` 对象
- `with` 块结束后自动解除绑定，不影响后续代码
- `BoundSession` 的方法签名**不需要传入 `obj` 参数**

### 方式二：@with_session 装饰器

使用装饰器自动注入绑定的 session，无需手动写 `with` 语句：

```python
from easybot import Bot, Scope, with_session

bot = Bot(app_id="xxx", app_secret="xxx")

@bot.on_guild_message
@with_session
async def handle_booking(msg, session=None):
    """
    session 参数由 @with_session 自动注入，
    类型为 BoundSession，已经绑定了当前 msg
    """
    if not session:
        return

    s = session.new(
        scope=Scope.USER,
        key="chat",
        data={"step": "waiting"},
    )
    data = session.get(scope=Scope.USER, key="chat")
    if data:
        print(data.data)
```

**要点**：
- 装饰器放在事件注册器**之后**（`@bot.on_guild_message` 在上，`@with_session` 在下）
- 处理函数必须接受 `session` 关键字参数（默认值 `None`）
- `session` 参数的类型是 `BoundSession`，可以直接调用 `.new()` / `.get()` / `.update()` / `.remove()` / `.wait_for()`

---

## API 参考

### bind — 绑定消息对象（上下文管理器）

将消息对象与会话管理器绑定，返回 `BoundSession` 实例。所有会话操作必须在 `with` 块内进行。

```python
with bot.session.bind(msg) as session:
    # session 是 BoundSession 实例
    session.new(Scope.USER, "key", {"data": 1})
    result = session.get(Scope.USER, "key")
```

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `obj` | `Model` | ✅ | 当前事件的消息对象，用于自动推断 identify 和获取回复参数 |

**返回值**: 上下文管理器，`as` 变量类型为 `BoundSession`

**行为**:
- 进入 `with` 块时将 `obj` 设为当前绑定对象
- 退出 `with` 块时（包括异常退出）自动恢复之前的绑定状态

---

### BoundSession 绑定后的会话对象

`BoundSession` 是 `bind()` 返回的包装器，其方法签名中**不再需要 `obj` 参数**。

#### BoundSession.new — 创建会话

```python
session_obj: SessionObject = session.new(
    scope=Scope.USER,
    key="my_session",
    data={"step": "waiting_input"},
    # 可选参数:
    identify=None,          # 手动指定标识，默认从 bind 的 msg 自动推断
    is_replace=True,        # 已存在时是否替换，默认 True
    timeout=None,           # 超时时间(秒)，None 表示永不过期
    timeout_reply=None,     # 超时时自动发送的消息（支持 str / MessagesModel 子类）
    inactive_gc_timeout=0,  # 变为 INACTIVE 后多久被 GC 回收(秒)，0 表示立即回收
    send_reply_on_msg_id_expired=False,  # msg_id 过期后是否仍发送消息
)
```

**参数说明**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `scope` | `str` | ✅ | — | 作用域，使用 `Scope.XXX` 常量 |
| `key` | `Hashable` | ✅ | — | 会话唯一键 |
| `data` | `dict \| None` | ❌ | `{}` | 初始会话数据 |
| `identify` | `Hashable \| None` | ❌ | `None` | 手动指定标识，为 None 则从 bind 的 msg 自动推断 |
| `is_replace` | `bool` | ❌ | `True` | 已存在同 key 会话时是否替换 |
| `timeout` | `float \| None` | ❌ | `None` | 超时时间（秒），超时后状态变为 INACTIVE 并可触发 timeout_reply |
| `timeout_reply` | `str \| Message \| ... \| None` | ❌ | `None` | 超时后自动发送的回复，支持纯文本或 MessagesModel 各子类 |
| `inactive_gc_timeout` | `float` | ❌ | `0` | 非活跃会话的 GC 回收等待时间（秒） |
| `send_reply_on_msg_id_expired` | `bool` | ❌ | `False` | msg_id 过期（超过5分钟）后是否仍发送消息 |

**返回值**: `SessionObject`

**异常**: `KeyError` — 当 `is_replace=False` 且已存在同名会话时抛出

---

#### BoundSession.get — 获取会话

获取已存在的会话数据。每次获取时会更新最后操作时间（`last_operate`）。

```python
session_obj: SessionObject = session.get(
    scope=Scope.USER,
    key="my_session",
    # 可选参数:
    identify=None,
    default=None,       # 会话不存在时的返回值
)
```

**参数说明**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `scope` | `str` | ✅ | — | 作用域 |
| `key` | `Hashable` | ✅ | — | 会话键 |
| `identify` | `Hashable \| None` | ❌ | `None` | 手动指定标识 |
| `default` | `Any` | ❌ | `None` | 会话不存在时的返回值 |

**返回值**: `SessionObject` — 存在时返回会话对象；不存在或已过期返回 `default`

> **注意**: 这是一个**同步方法**，不是异步的。

---

#### BoundSession.update — 更新会话数据

更新已有会话的 `data` 字典（合并方式：`target_session.data.update(data)`）。

```python
session_obj: SessionObject = session.update(
    scope=Scope.USER,
    key="my_session",
    data={"step": "confirmed", "result": "ok"},
    # 可选参数:
    identify=None,
)
```

**参数说明**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `scope` | `str` | ✅ | 作用域 |
| `key` | `Hashable` | ✅ | 会话键 |
| `data` | `dict` | ✅ | 要合并的数据字典 |
| `identify` | `Hashable \| None` | ❌ | 手动指定标识 |

**返回值**: `SessionObject`

**异常**: `KeyError` — 指定的会话不存在时抛出

---

#### BoundSession.remove — 删除会话

删除一个或多个会话。通过不同参数组合实现不同的删除范围：

```python
# 清空某个作用域的所有会话
session.remove(scope=Scope.USER)

# 清空某作用域下某个 identify 的所有会话
session.remove(scope=Scope.USER, identify="user_123")

# 删除具体某个会话
session.remove(scope=Scope.USER, identify="user_123", key="my_session")
```

**参数说明**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `scope` | `str \| None` | ❌ | 作用域，不传则清空全部 |
| `identify` | `Hashable \| None` | ❌ | 标识 |
| `key` | `Hashable \| None` | ❌ | 会话键 |

**行为总结**:

| scope | identify | key | 行为 |
|-------|----------|-----|------|
| 不传 | 不传 | 不传 | 清空所有作用域的所有会话 |
| 传了 | 不传 | 不传 | 清空该 scope 下所有会话 |
| 传了 | 传了 | 不传 | 清空该 scope+identify 下所有会话 |
| 传了 | 传了 | 传了 | 仅删除该具体会话 |

**异常**: `KeyError` — 指定删除的具体会话不存在时抛出

---

#### BoundSession.wait_for — 等待命令

等待指定的命令被触发。这是一个**异步方法**，会阻塞直到命令被触发或超时。

```python
result_msg: Model = await session.wait_for(
    scopes=Scope.USER,              # 单个作用域或作用域列表
    command=["确认", "取消"],       # 简化用法：字符串/列表/正则
    timeout=60,                     # 超时时间(秒)，None 为永远等待
    predicate=my_predicate_func,    # 可选：自定义匹配谓词函数
    on_timeout=timeout_callback,     # 可选：超时回调函数
)
```

**参数说明**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `scopes` | `str \| Iterable[str]` | ✅ | 作用域或作用域列表（如 `[Scope.USER, Scope.GROUP]`） |
| `command` | `Any` | ❌ | 要等待的命令对象，多种输入格式详见下文 |
| `timeout` | `int \| None` | ❌ | 超时时间（秒），None 表示永远等待 |
| `predicate` | `Callable[[Any], bool] \| None` | ❌ | 自定义谓词函数，用于判断消息是否匹配 |
| `on_timeout` | `Callable[[], Any] \| None` | ❌ | 超时回调函数，在等待超时时调用 |

**返回值**: `Model` — 触发该命令时收到的消息对象

**异常**:
- `WaitTimeoutError` — 等待超时时抛出
- `WaitError` — 找不到对应的等待任务时抛出

**command 参数支持多种输入格式**:

`command` 参数非常灵活，支持以下类型：

1. **字符串** - 单个命令词
```python
result = await session.wait_for(
    scopes=Scope.USER,
    command="确认",  # 直接使用字符串
    timeout=30,
)
```

2. **列表/元组** - 多个命令词
```python
result = await session.wait_for(
    scopes=Scope.USER,
    command=["确认", "取消", "是", "否"],
    timeout=30,
)
```

3. **正则表达式对象** - 正则匹配
```python
from re import compile as re_compile

result = await session.wait_for(
    scopes=Scope.USER,
    command=re_compile(r"^(\d+)$"),  # 直接传正则
    timeout=30,
)
# 可以通过 result.treated_msg 获取捕获组
num = int(result.treated_msg[0])
```

4. **BotCommandObject** - 完整配置（兼容旧用法）
```python
from easybot import BotCommandObject

command = BotCommandObject(
    command=["确认", "取消"],
    is_require_at=False,
    valid_scenes=CommandValidScenes.ALL,
)

result = await session.wait_for(
    scopes=Scope.USER,
    command=command,
    timeout=30,
)
```

5. **None** - 接受任意输入
```python
result = await session.wait_for(
    scopes=Scope.USER,
    command=None,  # 不指定命令，接受任意输入
    timeout=30,
)
```

**使用自定义谓词函数**:

当需要更复杂的匹配逻辑时，使用 `predicate` 参数：

```python
def has_multiple_emojis(message):
    """自定义匹配函数：检查消息中是否包含至少3个表情符号"""
    content = message.content
    emoji_chars = [c for c in content if ord(c) > 0x1F000]
    return len(emoji_chars) >= 3

result = await session.wait_for(
    scopes=Scope.USER,
    command=None,  # 不使用命令匹配
    predicate=has_multiple_emojis,  # 自定义谓词
    timeout=60,
)
```

`predicate` 函数接收消息对象，返回 `True` 表示匹配成功。

**使用超时回调**:

```python
timeout_happened = False

def on_timeout():
    """超时回调函数"""
    nonlocal timeout_happened
    timeout_happened = True

try:
    result = await session.wait_for(
        scopes=Scope.USER,
        command="收到",
        timeout=10,
        on_timeout=on_timeout
    )
except WaitTimeoutError:
    if timeout_happened:
        await msg.reply("超时回调已执行")
```

---

### SessionManager 直接调用（需先 bind）

除了通过 `BoundSession` 操作外，也可以在 `with session.bind(msg)` 块内直接调用 `SessionManager` 自身的方法：

```python
with bot.session.bind(msg):
    # 这些方法与 BoundSession 方法等价，内部使用 _current_obj
    bot.session.new(Scope.USER, "key", {"data": 1})
    bot.session.get(Scope.USER, "key")
    bot.session.update(Scope.USER, "key", {"data": 2})
```

**区别**:
- `SessionManager.new/get/update/wait_for` 在未 `bind` 时调用会抛出 `ValueError`（"请先使用 with session.bind(obj) 绑定消息对象"）
- `SessionManager.get` 在未 `bind` 时**不会报错**，而是返回 `default` 值
- `SessionManager.remove` **不需要 bind** 即可调用（见下方说明）

---

### remove — 全局删除（无需 bind）

`remove()` 方法是唯一**不需要先 bind** 就能调用的公共方法，因为它只依赖 scope/identify/key 定位会话，不需要从消息对象提取信息：

```python
# 可以在任何地方调用，不需要 with session.bind(msg)
bot.session.remove(scope=Scope.USER)                    # 清空 USER 作用域
bot.session.remove(scope=Scope.USER, key="my_key")       # 删除特定会话
bot.session.remove()                                     # 清空全部
```

---

## 高级功能

### 超时自动回复

`new()` 方法的 `timeout` 和 `timeout_reply` 参数配合使用，可以在会话超时后**自动发送提示消息**给用户：

```python
@bot.on_command(command="/quiz")
async def start_quiz(msg):
    with bot.session.bind(msg) as s:
        s.new(
            scope=Scope.USER,
            key="quiz",
            data={"question": 1, "score": 0},
            timeout=120,                    # 2分钟无操作则超时
            timeout_reply="⏰ 回答超时，测验结束！",
            inactive_gc_timeout=300,         # 超时后5分钟才真正清理
        )
    await msg.reply("开始答题！你有2分钟时间。")
```

**超时回复的工作机制**:

1. SDK 每 5 秒检查一次所有会话的超时状态
2. 当发现 ACTIVE 状态的会话超过 `timeout` 时间未被访问：
   - 如果设置了 `timeout_reply`，自动通过 API 发送回复消息
   - 将会话状态设为 INACTIVE
3. INACTIVE 状态的会话在经过 `inactive_gc_timeout` 后被 GC 回收

**msg_id 过期处理**:

QQ 官方 API 中，用于回复消息的 `msg_id` 有 **5 分钟有效期**。当会话超时时间超过 5 分钟时，需要考虑以下情况：

| 场景 | 默认行为 (`send_reply_on_msg_id_expired=False`) | 设置为 `True` |
|------|------------------------------------------------|---------------|
| `timeout=60` (1分钟) | 正常发送回复消息 | 正常发送回复消息 |
| `timeout=600` (10分钟) | **跳过发送**，输出警告日志 | 发送主动消息（非回复形式，消耗主动消息配额） |

```python
# 示例：超时时间较长时的处理
with bot.session.bind(msg) as s:
    s.new(
        scope=Scope.USER,
        key="long_task",
        data={...},
        timeout=600,  # 10分钟
        timeout_reply="⏰ 任务超时",
        # send_reply_on_msg_id_expired=False  # 默认：msg_id 过期后不发送
        send_reply_on_msg_id_expired=True     # 可选：过期后仍发送主动消息
    )
```

> **注意**: 主动消息受 QQ 官方频率限制和每日配额限制，建议仅在必要时设置 `send_reply_on_msg_id_expired=True`。

**timeout_reply 支持的类型**:

```python
# 纯文本
timeout_reply="⏰ 超时了！"

# MessagesModel 各种子类
from easybot import MessagesModel

timeout_reply=MessagesModel.MessageEmbed(
    title="会话超时",
    content=["你的操作已超时，请重新开始"],
)

timeout_reply=MessagesModel.MessageArk23(...)
timeout_reply=MessagesModel.MessageMarkdown(content="# 超时\n请重新开始")
```

### WaitFor 等待命令

`wait_for()` 用于在会话中等待特定命令的输入，常用于多步交互场景。这是一个**异步方法**：

```python
@bot.on_command(command="/interactive")
async def interactive_cmd(msg):
    with bot.session.bind(msg) as s:
        try:
            result = await s.wait_for(
                scopes=Scope.USER,
                command=my_command_obj,
                timeout=60,
            )
            await msg.reply(f"收到结果: {result.content}")
        except WaitTimeoutError:
            await msg.reply("⏰ 等待超时")
        except WaitError as e:
            await msg.reply(f"❌ {e}")
```

> **注意**: `wait_for` 与插件系统的命令注册配合使用。需要在其他地方有对应的命令处理器能匹配到 `command` 对象，否则会抛出 `WaitError`。

### 自动持久化

SessionManager 默认开启自动持久化，将所有会话数据以 **pickle 格式**保存到本地文件：

- **存储路径**: 默认 `<工作目录>/sdk_data/sessions.pickle`
- **写入时机**: 每次 `new()`、`update()`、`remove()` 操作后自动写入
- **启动加载**: Bot 启动时自动从文件恢复之前的会话数据
- **格式**: Python pickle 二进制格式

```python
# SessionManager 构造函数中的相关参数:
SessionManager(
    logger=logger,
    commit_path="./my_sessions",   # 自定义持久化目录
    is_auto_commit=True,            # 是否自动持久化（默认 True）
)
```

### GC 垃圾回收

SDK 内置了会话垃圾回收机制：

1. **活跃会话超时**: 超过 `timeout` 未被访问 → 状态变为 INACTIVE → 触发 timeout_reply
2. **非活跃会话回收**: INACTIVE 状态超过 `inactive_gc_timeout` → 从内存中彻底删除
3. **检查频率**: 每 5 秒执行一次超时检查，每 30 秒执行一次 GC 扫描（异步执行，每处理 100 个会让出事件循环避免阻塞）

```python
# inactive_gc_timeout 使用示例:
with bot.session.bind(msg) as s:
    s.new(
        scope=Scope.USER,
        key="temp",
        data={...},
        timeout=300,              # 5分钟后超时
        timeout_reply="超时了",
        inactive_gc_timeout=600,  # 超时后再保留10分钟供查询，之后才彻底清除
    )
```

---

## 异常说明

| 异常类 | 触发条件 |
|--------|---------|
| `ValueError` | 调用 `new()` / `update()` / `wait_for()` 但未先 `bind(msg)` 时 |
| `KeyError` | `new(is_replace=False)` 时已存在同名会话；`update()` / `remove()` 指定的会话不存在时 |
| `WaitError` | `wait_for()` 找不到对应的等待任务时 |
| `WaitTimeoutError` | `wait_for()` 超过指定 timeout 时间仍未收到结果时 |

---

## 使用示例

### 示例 1: 多轮对话 — 订票流程（使用 bind）

```python
from easybot import Bot, Scope, MessagesModel

bot = Bot(app_id="xxx", app_secret="xxx")

@bot.on_command(command="/book")
async def start_booking(msg):
    with bot.session.bind(msg) as s:
        s.new(
            scope=Scope.USER,
            key="booking",
            data={"step": "ask_destination"},
            timeout=600,
            timeout_reply="⏰ 订票超时，请重新输入 /book 开始",
        )
    await msg.reply(MessagesModel.MessageEmbed(
        title="🎫 订票助手",
        content=["请输入目的地"],
        prompt="开始订票",
    ))

@bot.on_guild_message
async def handle_booking(msg):
    with bot.session.bind(msg) as s:
        session = s.get(scope=Scope.USER, key="booking")
        if not session or session.status != 0:  # 0 = ACTIVE
            return

        step = session.data.get("step")

        if step == "ask_destination":
            s.update(scope=Scope.USER, key="booking", data={
                "destination": msg.content, "step": "ask_date",
            })
            await msg.reply(f"目的地: {msg.content}\n请输入出发日期")

        elif step == "ask_date":
            s.update(scope=Scope.USER, key="booking", data={
                "date": msg.content, "step": "confirm",
            })
            await msg.reply(f"日期确认: {msg.content}，回复「确认」完成订票")

        elif step == "confirm":
            if "确认" in msg.content:
                order_id = submit_order(session.data)
                s.remove(scope=Scope.USER, key="booking")
                await msg.reply(f"✅ 订单已提交！订单号: {order_id}")
            else:
                s.remove(scope=Scope.USER, key="booking")
                await msg.reply("已取消订票。输入 /book 重新开始")
```

### 示例 2: 多轮对话 — 订票流程（使用 @with_session）

```python
from easybot import Bot, Scope, MessagesModel, with_session

bot = Bot(app_id="xxx", app_secret="xxx")

@bot.on_command(command="/book")
async def start_booking(msg):
    with bot.session.bind(msg) as s:
        s.new(
            scope=Scope.USER,
            key="booking",
            data={"step": "ask_destination"},
            timeout=600,
            timeout_reply="⏰ 订票超时",
        )
    await msg.reply(MessagesModel.MessageEmbed(
        title="🎫 订票助手",
        content=["请输入目的地"],
        prompt="开始订票",
    ))

@bot.on_guild_message
@with_session
async def handle_booking(msg, session=None):
    if not session:
        return

    s = session.get(scope=Scope.USER, key="booking")
    if not s or s.status != 0:
        return

    step = s.data.get("step")

    if step == "ask_destination":
        session.update(scope=Scope.USER, key="booking", data={
            "destination": msg.content, "step": "ask_date",
        })
        await msg.reply(f"目的地: {msg.content}\n请输入出发日期")

    elif step == "confirm":
        if "确认" in msg.content:
            order_id = submit_order(s.data)
            session.remove(scope=Scope.USER, key="booking")
            await msg.reply(f"✅ 订单已提交！订单号: {order_id}")
```

### 示例 3: 群内小游戏 — 猜数字

```python
import random
from easybot import Bot, Scope, CommandValidScenes

bot = Bot(app_id="xxx", app_secret="xxx")

@bot.on_command(command="/guess", valid_scenes=CommandValidScenes.GROUP)
async def start_guess(msg):
    target = random.randint(1, 100)
    with bot.session.bind(msg) as s:
        s.new(
            scope=Scope.GROUP,
            key="guess_game",
            data={
                "target": target,
                "attempts": 0,
                "started_by": msg.author.username,
            },
            timeout=1200,
            timeout_reply="⏰ 猜数字游戏已结束，太久了没人猜中",
        )
    await msg.reply(f"🎯 猜数字游戏开始！范围 1~100\n由 **{msg.author.username}** 发起")

@bot.on_group_message
async def handle_guess(msg):
    with bot.session.bind(msg) as s:
        session = s.get(scope=Scope.GROUP, key="guess_game")
        if not session or session.status != 0:
            return

        try:
            guess = int(msg.content.strip())
        except ValueError:
            return

        new_data = {"attempts": session.data["attempts"] + 1}
        target = session.data["target"]

        if guess < target:
            hint = "📈 太小了"
        elif guess > target:
            hint = "📉 太大了"
        else:
            hint = f"🎉 **{msg.author.username}** 猜对了！答案就是 **{target}**\n共猜了 {new_data['attempts']} 次"
            s.remove(scope=Scope.GROUP, key="guess_game")
            await msg.reply(hint)
            return

        s.update(scope=Scope.GROUP, key="guess_game", data=new_data)
        await msg.reply(hint)
```

### 示例 4: 用户偏好设置持久化

```python
@bot.on_command(command="/set_lang")
async def set_language(msg):
    lang = msg.treated_msg.strip().lower()
    if lang in ("zh", "en"):
        with bot.session.bind(msg) as s:
            s.new(
                scope=Scope.USER,
                key="settings",
                data={"language": lang},
                timeout=None,  # 永不过期
            )
        await msg.reply(f"语言已设置为: {'中文' if lang == 'zh' else 'English'}")
    else:
        await msg.reply("支持的语言: zh / en")

@bot.on_command(command="/my_settings")
async def show_settings(msg):
    with bot.session.bind(msg) as s:
        session = s.get(scope=Scope.USER, key="settings")
        if session and session.status == 0:
            lang_display = {"zh": "中文", "en": "English"}
            await msg.reply(f"语言: {lang_display.get(session.data.get('language'), '未设置')}")
        else:
            await msg.reply("暂无设置，使用 /set_lang 设置语言")
```

### 示例 5: 使用 wait_for 等待用户下一步操作

```python
from easybot import Bot, Scope, WaitTimeoutError, WaitError, with_session, BotCommandObject

bot = Bot(app_id="xxx", app_secret="xxx")

@bot.on_command(command="/confirm_action")
async def confirm_action(msg):
    with bot.session.bind(msg) as s:
        await msg.reply("请在30秒内回复「确认」或「取消」")
        try:
            # 使用 BotCommandObject 定义等待的命令
            result = await s.wait_for(
                scopes=Scope.USER,
                command=BotCommandObject(command=["确认", "取消"]),
                timeout=30,
            )
            if "确认" in result.content:
                await msg.reply("✅ 已确认！")
            else:
                await msg.reply("❌ 已取消")
        except WaitTimeoutError:
            await msg.reply("⏰ 等待超时，操作取消")
        except WaitError as e:
            await msg.reply(f"❌ 错误: {e}")
```

---

## 最佳实践

### 1. 合理设置超时时间

```python
# ✅ 根据交互复杂度调整超时
简单问答:   timeout=180        # 3分钟
表单填写:   timeout=900        # 15分钟
游戏进程:   timeout=3600       # 1小时
用户配置:   timeout=None       # 永不过期

# ✅ 配合 timeout_reply 提升用户体验
with bot.session.bind(msg) as s:
    s.new(scope=Scope.USER, key="flow", data={...},
         timeout=300, timeout_reply="⏰ 操作超时，请重新开始")
```

### 2. 会话结束时及时清理

```python
# ✅ 流程结束立即 remove
if success:
    with bot.session.bind(msg) as s:
        s.remove(scope=Scope.USER, key="booking")
    await msg.reply("完成!")

# ✅ 利用 timeout + timeout_reply 作为兜底
# 即使用户中途离开，也会收到超时提示
```

### 3. 使用结构化的会话数据

```python
# ✅ 推荐方式 — 结构清晰
with bot.session.bind(msg) as s:
    s.new(scope=Scope.USER, key="order", data={
        "order": {
            "destination": "上海",
            "date": "2026-01-20",
        },
        "current_step": "payment",
    })
```

### 4. 选择合适的使用方式

```python
# 方式一：bind 上下文管理器 — 适合需要精确控制绑定范围的场景
@bot.on_guild_message
async def handler(msg):
    with bot.session.bind(msg) as s:
        s.new(Scope.USER, "key", data={...})

# 方式二：@with_session 装饰器 — 适合整个处理函数都需要 session 的场景
@bot.on_guild_message
@with_session
async def handler(msg, session=None):
    session.new(Scope.USER, "key", data={...})
```

### 5. 注意 get/update/new 需要 bind，但 remove 不需要

```python
# ✅ 正确 — new/get/update 需要 bind
with bot.session.bind(msg) as s:
    s.new(Scope.USER, "key", data={...})
    s.get(Scope.USER, "key")
    s.update(Scope.USER, "key", data={...})

# ✅ remove 不需要 bind，可以在任何地方调用
bot.session.remove(scope=Scope.USER, key="old_key")

# ❌ 错误 — 未 bind 就调用 new/update
# bot.session.new(Scope.USER, "key", data={...})  # 抛出 ValueError
```

### 6. 区分 SessionObject 的 status

```python
with bot.session.bind(msg) as s:
    session = s.get(scope=Scope.USER, key="test")
    if session and session.status == 0:   # SessionStatus.ACTIVE
        print("会话活跃，可以继续操作")
    elif session and session.status == 1:  # SessionStatus.INACTIVE
        print("会话已过期/失活")
    else:
        print("会话不存在")
```

---

## 下一步

- [常见问题 Q&A](./09_常见问题Q&A.md) — 排查开发中的问题
- [联系和反馈](./10_联系和反馈.md) — 获取技术支持