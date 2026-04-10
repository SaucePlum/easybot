# Session 会话管理器

本章介绍 EasyBot SDK 的会话状态管理组件，用于在多轮对话中维护用户/群组的状态信息。

---

## 一、概述

**模块**: `easybot.session`  
**访问方式**: `bot.session`（通过 Bot 实例访问）

SessionManager 用于跨消息持久化状态，使多轮对话成为可能。

### 1.1 什么是 Session？

在 QQ 机器人开发中，**单次消息处理是无状态的**——每次收到消息时，机器人不知道用户之前说过什么。Session 的作用就是**跨消息持久化状态**。

```
用户: "帮我订一张去北京的票"
    ↓ 创建会话
机器人: "好的，请问什么时间出发？"

用户: "明天上午"
    ↓ 更新会话
机器人: "已为您预订：北京 → 明天上午，确认吗？"

用户: "确认"
    ↓ 删除会话
机器人: "✅ 订单已提交！"
```

### 1.2 SessionObject 数据结构

`new()` / `get()` / `update()` 返回的是 `SessionObject` 对象：

| 属性 | 类型 | 说明 |
|------|------|------|
| `scope` | `str` | 会话作用域 |
| `status` | `int` | 会话状态：`0`=活跃，`1`=非活跃 |
| `key` | `Hashable` | 会话键 |
| `data` | `dict` | 会话数据 |
| `identify` | `Hashable \| None` | 作用域内的标识 |

---

## 二、作用域 Scope

作用域决定了 Session 的**隔离粒度**和**唯一标识**。

### 2.1 作用域类型

```python
from easybot import Scope

Scope.USER      # 用户级别
Scope.GUILD     # 频道级别
Scope.CHANNEL   # 子频道级别
Scope.GROUP     # 群聊级别
Scope.GLOBAL    # 全局级别
```

### 2.2 作用域选择指南

| 场景 | 推荐作用域 | 说明 |
|------|-----------|------|
| 用户个人设置/多轮对话 | `USER` | 同一用户在不同场景共享状态 |
| 群内游戏/群活动 | `GROUP` | 群成员共享同一状态 |
| 频道管理功能 | `GUILD` | 频道内所有成员共享 |
| 子频道投票/讨论 | `CHANNEL` | 该子频道的专属状态 |
| 全局计数器/配置 | `GLOBAL` | 所有场景共享同一状态 |

### 2.3 Identify 自动识别规则

当通过 `bind(msg)` 绑定消息对象后，SDK 会根据消息对象和作用域自动推断标识：

| 作用域 | 识别字段来源 | 示例 |
|--------|-------------|------|
| `USER` | `msg.author.id` 或 `msg.user_openid` | 用户 OpenID |
| `GUILD` | `msg.guild_id` | 频道 ID |
| `CHANNEL` | `msg.channel_id` | 子频道 ID |
| `GROUP` | `msg.group_openid` | 群 OpenID |
| `GLOBAL` | 不适用 | 无需 identify |

---

## 三、使用方式

### 3.1 bind() 上下文管理器（推荐）

使用 `with session.bind(msg)` 绑定当前消息对象，在 `with` 块内直接操作会话：

#### 方式1：通过 bot 实例（主程序推荐）

```python
from easybot import Bot, Model, Scope

bot = Bot(app_id="xxx", app_secret="xxx")

@bot.on_command(command="/book")
async def start_booking(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
) -> None:
    with bot.session.bind(msg) as s:
        await s.new(
            scope=Scope.USER,
            key="booking",
            data={"step": "ask_destination"},
            timeout=600,
            timeout_reply="⏰ 订票超时",
        )
    await msg.reply("请输入目的地")

@bot.on_guild_message
async def handle_booking(msg: Model.GuildMessage) -> None:
    with bot.session.bind(msg) as s:
        session = await s.get(scope=Scope.USER, key="booking")
        if not session or session.status != 0:
            return

        step = session.data.get("step")
        if step == "ask_destination":
            await s.update(scope=Scope.USER, key="booking", data={
                "destination": msg.content, "step": "ask_date",
            })
            await msg.reply(f"目的地: {msg.content}\n请输入出发日期")
```

#### 方式2：通过消息对象（插件推荐）⭐

```python
from easybot import Model, Plugins, Scope

@Plugins.on_command(command="/book")
async def start_booking(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
) -> None:
    # ✅ 在插件中使用 msg.session 快捷方式
    with msg.session.bind(msg) as s:
        await s.new(
            scope=Scope.USER,
            key="booking",
            data={"step": "ask_destination"},
            timeout=600,
            timeout_reply="⏰ 订票超时",
        )
    await msg.reply("请输入目的地")
```

> **提示**：
> - 在主程序中，使用 `bot.session.bind(msg)` 更直观
> - 在插件中，使用 `msg.session.bind(msg)` 更方便（无需访问 bot 变量）
> - `msg.session` 等同于 `msg.bot.session`，是访问会话管理器的快捷方式

**要点**：
- `bind(msg)` 返回一个上下文管理器，`as s` 得到的是 `BoundSession` 对象
- `with` 块结束后自动解除绑定
- `BoundSession` 的方法签名**不需要传入 `obj` 参数**
- **所有会话操作方法都是异步的**，需要使用 `await` 调用

### 3.2 @with_session 装饰器

使用装饰器自动注入绑定的 session：

```python
from easybot import Bot, BoundSession, Model, Scope, with_session

bot = Bot(app_id="xxx", app_secret="xxx")

@bot.on_guild_message
@with_session
async def handle_booking(
    msg: Model.GuildMessage,
    session: BoundSession | None = None,
) -> None:
    """
    session 参数由 @with_session 自动注入，
    类型为 BoundSession，已经绑定了当前 msg
    """
    if not session:
        return

    s = await session.new(
        scope=Scope.USER,
        key="chat",
        data={"step": "waiting"},
    )
```

**要点**：
- 装饰器放在事件注册器**之后**
- 处理函数必须接受 `session` 关键字参数（默认值 `None`）
- **所有会话操作方法都是异步的**，需要使用 `await` 调用

---

## 四、消息对象的 treated_msg 属性

在使用 Session 和命令系统时，消息对象（`GuildMessage`、`GroupMessage`、`C2CMessage`、`DirectMessage`）都有一个特殊的 `treated_msg` 属性，它提供了**经过处理的消息内容**。

### 4.1 treated_msg 与 content 的区别

| 属性 | 说明 | 示例 |
|------|------|------|
| `content` | 消息的**原始内容**，不做任何处理 | `"@机器人 你好"` 或 `"/ping test"` |
| `treated_msg` | **处理后的内容**，根据场景自动清理 | `"你好"` 或 `"test"` |

### 4.2 treated_msg 的处理规则

`treated_msg` 的值取决于消息的触发方式：

#### 场景 1：普通消息事件（@机器人）

在 `@bot.on_guild_message` 等事件处理器中：

```python
@bot.on_guild_message
async def handle(msg: Model.GuildMessage):
    # 用户发送: "@机器人 你好"
    print(f"原始内容: {msg.content}")      # "@机器人 你好"
    print(f"处理后内容: {msg.treated_msg}")  # "你好"
    
    # 用户发送: "你好"（未@机器人，私域机器人）
    print(f"原始内容: {msg.content}")      # "你好"
    print(f"处理后内容: {msg.treated_msg}")  # "你好"
```

**处理规则**：
- 自动去除 `@机器人` 的文本
- 保留消息的实际内容

#### 场景 2：命令处理器（@bot.on_command）

在命令处理器中，`treated_msg` 会去除命令前缀：

```python
@bot.on_command(command="ping", valid_scenes=CommandValidScenes.ALL)
async def ping_cmd(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
):
    # 用户发送: "/ping test"
    print(f"原始内容: {msg.content}")      # "/ping test"
    print(f"处理后内容: {msg.treated_msg}")  # "test"
    
    # 用户发送: "ping hello"（无斜杠）
    print(f"原始内容: {msg.content}")      # "ping hello"
    print(f"处理后内容: {msg.treated_msg}")  # "hello"
```

**处理规则**：
- 自动去除命令关键词（如 `/ping`、`ping`）
- 保留命令后的参数部分

#### 场景 3：正则匹配命令（regex 参数）

当使用 `regex` 参数时，`treated_msg` 会返回**正则表达式的捕获组**：

```python
from re import compile as re_compile

@bot.on_command(regex=re_compile(r"掷骰子(\d+)d(\d+)"))
async def dice(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
):
    # 用户发送: "掷骰子3d6"
    print(f"原始内容: {msg.content}")      # "掷骰子3d6"
    print(f"处理后内容: {msg.treated_msg}")  # ('3', '6')
    
    # treated_msg 是 groups() 的结果，可以直接解包
    count, sides = msg.treated_msg
    await msg.reply(f"掷 {count} 个 {sides} 面骰子")
```

**处理规则**：
- `treated_msg` 返回 `re.Match.groups()` 的结果（tuple）
- 如果没有捕获组，返回空 tuple `()`
- 如果正则不匹配，该命令不会被触发

#### 场景 4：wait_for 中的正则匹配

在 `wait_for` 中使用正则表达式时，返回的消息对象也有 `treated_msg`：

```python
from re import compile as re_compile

@bot.on_command(command="验证码")
async def verify_code(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
):
    with bot.session.bind(msg) as s:
        await msg.reply("请输入 4 位数字验证码：")
        
        result = await s.wait_for(
            scopes=Scope.USER,
            command=re_compile(r"^(\d{4})$"),
            timeout=60,
        )
        
        # 用户回复: "1234"
        code = result.treated_msg[0]  # '1234'
        await msg.reply(f"验证码已接收: {code}")
```

### 4.3 使用建议

#### ✅ 推荐做法

```python
# 1. 命令参数处理 - 使用 treated_msg
@bot.on_command(command="查询")
async def query(msg: Model.GuildMessage):
    keyword = msg.treated_msg.strip()  # 直接获取参数
    if not keyword:
        await msg.reply("请提供查询关键词")
        return
    # 执行查询...

# 2. 正则捕获 - 使用 treated_msg
@bot.on_command(regex=re_compile(r"计算(\d+)\+(\d+)"))
async def calc(msg: Model.GuildMessage):
    a, b = msg.treated_msg
    result = int(a) + int(b)
    await msg.reply(f"结果: {result}")

# 3. wait_for 正则匹配 - 使用 treated_msg
result = await s.wait_for(scopes=Scope.USER, command=re_compile(r"^(\d+)$"))
number = int(result.treated_msg[0])
```

#### ❌ 不推荐做法

```python
# 1. 手动处理命令前缀 - 不推荐
@bot.on_command(command="查询")
async def query(msg: Model.GuildMessage):
    keyword = msg.content.replace("查询", "").strip()  # ❌ 容易出错
    # 应该使用: keyword = msg.treated_msg.strip()

# 2. 手动解析正则 - 不推荐
@bot.on_command(regex=re_compile(r"计算(\d+)\+(\d+)"))
async def calc(msg: Model.GuildMessage):
    import re
    match = re.search(r"计算(\d+)\+(\d+)", msg.content)  # ❌ 重复匹配
    a, b = match.groups()
    # 应该直接使用: a, b = msg.treated_msg
```

### 4.4 注意事项

1. **类型不确定性**：
   - `treated_msg` 的类型取决于触发方式
   - 普通消息：`str`
   - 正则匹配：`tuple` 或 `None`
   - 使用前建议检查类型

2. **空值处理**：
   ```python
   # treated_msg 可能为空字符串或 None
   text = msg.treated_msg or msg.content
   if not text:
       await msg.reply("消息内容为空")
       return
   ```

3. **正则匹配的边界情况**：
   ```python
   # 如果正则没有捕获组，treated_msg 是空 tuple
   @bot.on_command(regex=re_compile(r"\d+"))
   async def number(msg: Model.GuildMessage):
       # treated_msg = ()
       # 需要使用 msg.content 获取完整内容
       number = msg.content
   ```

---

## 五、API 参考

### 5.1 BoundSession.new — 创建会话

```python
session_obj = await session.new(
    scope=Scope.USER,
    key="my_session",
    data={"step": "waiting_input"},
    # 可选参数:
    identify=None,          # 手动指定标识
    is_replace=True,        # 已存在时是否替换
    timeout=None,           # 超时时间(秒)
    timeout_reply=None,     # 超时时自动发送的消息
    inactive_gc_timeout=0,  # 变为 INACTIVE 后多久被 GC 回收(秒)
)
```

**参数说明**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `scope` | `str` | ✅ | — | 作用域 |
| `key` | `Hashable` | ✅ | — | 会话唯一键 |
| `data` | `dict \| None` | ❌ | `{}` | 初始会话数据 |
| `identify` | `Hashable \| None` | ❌ | `None` | 手动指定标识 |
| `is_replace` | `bool` | ❌ | `True` | 已存在同 key 会话时是否替换 |
| `timeout` | `float \| None` | ❌ | `1800` | 超时时间（秒），默认 30 分钟 |
| `timeout_reply` | `str \| Message \| ... \| None` | ❌ | `None` | 超时后自动发送的回复 |
| `inactive_gc_timeout` | `float` | ❌ | `0` | 非活跃会话的 GC 回收等待时间 |

**返回值**: `SessionObject`

### 5.2 BoundSession.get — 获取会话

```python
session_obj = await session.get(
    scope=Scope.USER,
    key="my_session",
    identify=None,
    default=None,
)
```

**参数说明**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `scope` | `str` | ✅ | — | 作用域 |
| `key` | `Hashable` | ✅ | — | 会话键 |
| `identify` | `Hashable \| None` | ❌ | `None` | 手动指定标识 |
| `default` | `Any` | ❌ | `None` | 会话不存在时的返回值 |

**返回值**: `SessionObject` — 存在时返回会话对象；不存在或已过期返回 `default`

### 5.3 BoundSession.update — 更新会话数据

```python
session_obj = await session.update(
    scope=Scope.USER,
    key="my_session",
    data={"step": "confirmed", "result": "ok"},
    identify=None,
)
```

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `scope` | `str` | ✅ | 作用域 |
| `key` | `Hashable` | ✅ | 会话键 |
| `data` | `dict` | ✅ | 要合并的数据字典 |
| `identify` | `Hashable \| None` | ❌ | 手动指定标识 |

**返回值**: `SessionObject`

### 5.4 BoundSession.remove — 删除会话

```python
# 清空某个作用域的所有会话
await session.remove(scope=Scope.USER)

# 清空某作用域下某个 identify 的所有会话
await session.remove(scope=Scope.USER, identify="user_123")

# 删除具体某个会话
await session.remove(scope=Scope.USER, identify="user_123", key="my_session")
```

**行为总结**：

| scope | identify | key | 行为 |
|-------|----------|-----|------|
| 不传 | 不传 | 不传 | 清空所有作用域的所有会话 |
| 传了 | 不传 | 不传 | 清空该 scope 下所有会话 |
| 传了 | 传了 | 不传 | 清空该 scope+identify 下所有会话 |
| 传了 | 传了 | 传了 | 仅删除该具体会话 |

### 5.5 BoundSession.wait_for — 等待命令

等待指定的命令被触发。这是一个**异步方法**：

```python
from easybot import Scope

result_msg = await session.wait_for(
    scopes=Scope.USER,              # 单个作用域或作用域列表
    command=["确认", "取消"],       # BotCommandObject / 字符串 / 列表 / 正则
    timeout=60,                     # 超时时间(秒)
    predicate=my_predicate_func,    # 可选：自定义匹配谓词函数
)
```

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `scopes` | `str \| Sequence[str]` | ✅ | 作用域或作用域列表 |
| `command` | `BotCommandObject \| str \| Sequence[str] \| Pattern \| None` | ❌ | 要等待的命令 |
| `timeout` | `int \| None` | ❌ | 超时时间（秒），None 表示永远等待 |
| `predicate` | `Callable[[Any], bool] \| None` | ❌ | 自定义谓词函数 |
| `on_timeout` | `Callable[[], Any] \| None` | ❌ | 超时回调函数 |

**返回值**: 消息对象（`GuildMessage` / `GroupMessage` / `C2CMessage` / `DirectMessage`）

**异常**:
- `WaitTimeoutError` — 等待超时时抛出
- `WaitError` — 找不到对应的等待任务时抛出

#### command 参数支持多种输入格式

**快捷方式（自动包装为默认配置的 BotCommandObject）**：

```python
# 1. 字符串 — 精确匹配
result = await session.wait_for(scopes=Scope.USER, command="确认")

# 2. 列表/元组 — 匹配列表中的任意一个
result = await session.wait_for(scopes=Scope.USER, command=["确认", "取消"])

# 3. 正则表达式 — 正则匹配
from re import compile as re_compile
result = await session.wait_for(scopes=Scope.USER, command=re_compile(r"^(\d+)$"))

# 4. None - 接受任意输入
result = await session.wait_for(scopes=Scope.USER, command=None)
```

**高级用法：直接传入 BotCommandObject**

当需要使用更多控制参数（如权限校验、@要求、场景限制等）时，
可以直接构造并传入 `BotCommandObject` 实例，以获得完整的功能支持：

```python
from re import compile as re_compile
from easybot import BotCommandObject, CommandValidScenes, Scope

# 示例 1: 要求管理员权限 + 自定义错误提示
cmd = BotCommandObject(
    command="确认",
    admin=True,
    admin_error_msg="⚠️ 此操作需要管理员权限",
)
result = await session.wait_for(scopes=Scope.USER, command=cmd)

# 示例 2: 正则匹配 + 要求 @机器人
cmd = BotCommandObject(
    regex=re_compile(r"^\d{4}$"),
    at=True,
)
result = await session.wait_for(scopes=Scope.USER, command=cmd)

# 示例 3: 限制有效场景（仅在频道和群聊生效）
cmd = BotCommandObject(
    command="开始",
    valid_scenes=CommandValidScenes.GUILD | CommandValidScenes.GROUP,
)
result = await session.wait_for(scopes=Scope.USER, command=cmd)

# 示例 4: 要求机器人管理员权限
cmd = BotCommandObject(
    command="shutdown",
    is_require_bot_admin=True,
    bot_admin_error_msg="⚠️ 仅机器人管理员可执行此操作",
)
result = await session.wait_for(scopes=Scope.USER, command=cmd)
```

> **注意**: 使用快捷方式传入 `str`/`list`/`Pattern` 时，内部会自动包装为
> `BotCommandObject(command=..., valid_scenes=CommandValidScenes.ALL)`。
> 如果需要更细粒度的控制（如限制触发场景、权限校验等），请直接传入 `BotCommandObject`。

---

## 六、高级功能

### 6.1 超时自动回复

`new()` 方法的 `timeout` 和 `timeout_reply` 参数配合使用，可以在会话超时后**自动发送提示消息**。

> **重要说明**：从 v1.x 版本开始，`timeout` 参数有默认值 **1800 秒（30 分钟）**。即使不显式设置 `timeout`，会话也会在 30 分钟无操作后自动超时。这个设计是为了防止会话永久占用内存和存储空间。如果你需要会话长期存在，可以显式设置更大的 `timeout` 值。

```python
from easybot import Model, Scope

@bot.on_command(command="/quiz")
async def start_quiz(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
) -> None:
    with bot.session.bind(msg) as s:
        await s.new(
            scope=Scope.USER,
            key="quiz",
            data={"question": 1, "score": 0},
            timeout=120,                    # 2分钟无操作则超时
            timeout_reply="⏰ 回答超时，测验结束！",
            inactive_gc_timeout=300,         # 超时后5分钟才真正清理
        )
    await msg.reply("开始答题！你有2分钟时间。")
```

**timeout_reply 支持的类型**：

```python
# 纯文本
timeout_reply="⏰ 超时了！"

# MessagesModel 各种子类
from easybot import MessagesModel

timeout_reply=MessagesModel.MessageEmbed(
    title="会话超时",
    content=["你的操作已超时，请重新开始"],
)
```

### 6.2 自动持久化

SessionManager 默认开启自动持久化，将所有会话数据以 **pickle 格式**保存到本地文件：

- **存储路径**: 默认 `<工作目录>/sdk_data/sessions.pickle`
- **保存时机**: 会话创建、更新、删除时自动保存
- **加载时机**: Bot 启动时自动加载

> **注意**: 当前版本暂不支持通过 Bot 构造函数自定义会话存储路径。会话数据默认保存在工作目录下的 `sdk_data/sessions.pickle` 文件中。

### 6.3 垃圾回收机制

SessionManager 内置垃圾回收机制，定期清理过期会话：

- **GC 间隔**: 每 5 秒检查一次
- **回收条件**: 会话状态为 INACTIVE 且超过 `inactive_gc_timeout` 时间
- **超时触发**: 会话超过 `timeout` 时间未被访问时状态变为 INACTIVE

---

## 七、最佳实践

### 7.1 多步骤交互流程

```python
from easybot import Model, Scope

@bot.on_command(command="/order")
async def start_order(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
) -> None:
    with bot.session.bind(msg) as s:
        await s.new(
            scope=Scope.USER,
            key="order",
            data={"step": 1, "items": []},
            timeout=600,
            timeout_reply="订单超时，请重新开始",
        )
    await msg.reply("开始下单！请输入商品名称")

@bot.on_guild_message
async def handle_order(msg: Model.GuildMessage) -> None:
    with bot.session.bind(msg) as s:
        session = await s.get(scope=Scope.USER, key="order")
        if not session or session.status != 0:
            return

        step = session.data.get("step")
        
        if step == 1:
            await s.update(scope=Scope.USER, key="order", data={
                "item": msg.content, "step": 2
            })
            await msg.reply(f"商品: {msg.content}\n请输入数量")
        
        elif step == 2:
            quantity = int(msg.content)
            await s.update(scope=Scope.USER, key="order", data={
                "quantity": quantity, "step": 3
            })
            await msg.reply(f"数量: {quantity}\n确认订单？(是/否)")
        
        elif step == 3:
            if msg.content == "是":
                await msg.reply("✅ 订单已提交")
                await s.remove(scope=Scope.USER, key="order")
            else:
                await msg.reply("订单已取消")
                await s.remove(scope=Scope.USER, key="order")
```

### 7.2 使用 wait_for 简化交互

```python
from easybot import Model, Scope, WaitTimeoutError

@bot.on_command(command="/confirm")
async def confirm_action(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
) -> None:
    with bot.session.bind(msg) as s:
        await msg.reply("确认执行此操作？(是/否)")
        
        try:
            result = await s.wait_for(
                scopes=Scope.USER,
                command=["是", "否"],
                timeout=60,
            )
            
            if result.content == "是":
                await msg.reply("✅ 操作已执行")
            else:
                await msg.reply("❌ 操作已取消")
        
        except WaitTimeoutError:
            await msg.reply("⏰ 确认超时")
```

### 7.3 两步收集姓名和年龄（WaitFor + 超时）

```python
from re import compile as re_compile

from easybot import Model, Scope, WaitTimeoutError

@bot.on_command(command="/profile")
async def collect_profile(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
) -> None:
    with bot.session.bind(msg) as s:
        await msg.reply("请告诉我你的姓名（30 秒内回复）")

        try:
            name_msg = await s.wait_for(scopes=Scope.USER, command=None, timeout=30)
        except WaitTimeoutError:
            await msg.reply("⏰ 超时未收到姓名，请重新开始")
            return

        name = (name_msg.treated_msg or name_msg.content).strip()
        if not name:
            await msg.reply("姓名不能为空，请重新开始")
            return

        await msg.reply("请告诉我你的年龄（仅数字，30 秒内回复）")

        try:
            age_msg = await s.wait_for(
                scopes=Scope.USER,
                command=re_compile(r"^\d{1,3}$"),
                timeout=30,
            )
        except WaitTimeoutError:
            await msg.reply("⏰ 超时未收到年龄，请重新开始")
            return

        age = int(age_msg.content.strip())
        await msg.reply(f"收到：姓名={name}，年龄={age}")
```

### 7.4 群聊共享状态

```python
from easybot import Model

@bot.on_command(command="/vote")
async def start_vote(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
) -> None:
    with bot.session.bind(msg) as s:
        await s.new(
            scope=Scope.GROUP,  # 群聊级别
            key="vote",
            data={
                "topic": "今天吃什么？",
                "options": {"火锅": 0, "烧烤": 0, "外卖": 0},
                "voters": [],
            },
            timeout=3600,
        )
    await msg.reply("投票开始！回复 火锅/烧烤/外卖 进行投票")

@bot.on_group_message
async def handle_vote(msg: Model.GroupMessage) -> None:
    with bot.session.bind(msg) as s:
        session = await s.get(scope=Scope.GROUP, key="vote")
        if not session or session.status != 0:
            return

        user_id = msg.author.id
        if user_id in session.data["voters"]:
            await msg.reply("你已经投过票了")
            return

        choice = msg.content
        if choice in session.data["options"]:
            session.data["options"][choice] += 1
            session.data["voters"].append(user_id)
            await s.update(scope=Scope.GROUP, key="vote", data=session.data)
            await msg.reply(f"投票成功！当前票数: {session.data['options']}")
```

### 7.5 并发多场景多轮对话（跨频道/群聊/C2C + 超时 + GC）

当你希望同一套多轮对话逻辑能够：

- 同时服务多个用户（并发会话互不干扰）
- 在不同消息场景中都可用（频道/群聊/C2C）
- 自动超时变为非活跃，并在后台定期 GC 清理

推荐的设计是：

- 使用 `Scope.USER` 作为隔离粒度，让每个用户有独立会话（天然支持并发）
- 使用 `key` 区分不同流程（例如 `"wizard"`），避免同一用户的多条流程互相覆盖
- 用 `timeout` 控制“整体流程”最大闲置时间；用 `inactive_gc_timeout` 控制会话在超时后多久被垃圾回收删除
- 用 `wait_for(..., timeout=...)` 控制“每一步输入”的等待时间，并用 `predicate` 过滤不合格输入（不合格的消息会继续参与其他命令匹配）

下面是一个“表单式流程”的最小实现：先问姓名，再问年龄，最终确认；在任意场景都可以继续对话，并在用户长时间不回复时自动超时与回收。

跨场景继续对话依赖 `Scope.USER` 在不同消息场景中提取到同一用户标识符；如果你发现用户在频道/群聊/C2C 场景下标识不一致，会表现为“跨场景无法命中 wait_for”。

```python
from easybot import CommandValidScenes, Model, Scope, WaitError, WaitTimeoutError

@bot.on_command(command="/wizard", valid_scenes=CommandValidScenes.ALL)
async def wizard(
    msg: Model.Message,
) -> None:
    with bot.session.bind(msg) as s:
        await s.new(
            scope=Scope.USER,
            key="wizard",
            data={"step": "name"},
            timeout=240,
            timeout_reply="⏰ 会话已超时，请重新输入 /wizard 开始",
            inactive_gc_timeout=300,
        )

        try:
            await msg.reply("请输入姓名（60 秒内回复，发送 取消 可退出）")

            def name_ok(m: Any) -> bool:
                text = (m.treated_msg or m.content).strip()
                return bool(text) and text != "取消" and len(text) <= 32

            name_msg = await s.wait_for(
                scopes=Scope.USER,
                command=None,
                timeout=60,
                predicate=name_ok,
            )
            name = (name_msg.treated_msg or name_msg.content).strip()
            await s.update(scope=Scope.USER, key="wizard", data={"name": name, "step": "age"})

            await msg.reply("请输入年龄（1-120，60 秒内回复，发送 取消 可退出）")

            def age_ok(m: Any) -> bool:
                text = m.content.strip()
                if text == "取消":
                    return False
                if not text.isdigit():
                    return False
                age = int(text)
                return 1 <= age <= 120

            age_msg = await s.wait_for(
                scopes=Scope.USER,
                command=None,
                timeout=60,
                predicate=age_ok,
            )
            age = int(age_msg.content.strip())
            await s.update(scope=Scope.USER, key="wizard", data={"age": age, "step": "confirm"})

            await msg.reply(f"确认提交？姓名={name} 年龄={age}（回复 是/否）")
            confirm_msg = await s.wait_for(
                scopes=Scope.USER,
                command=["是", "否", "取消"],
                timeout=60,
            )

            if confirm_msg.content.strip() != "是":
                await msg.reply("已取消")
                await s.remove(scope=Scope.USER, key="wizard")
                return

            await msg.reply("已提交")
            await s.remove(scope=Scope.USER, key="wizard")

        except WaitTimeoutError:
            await msg.reply("⏰ 本步骤超时，请重新输入 /wizard 开始")
            await s.remove(scope=Scope.USER, key="wizard")
        except WaitError:
            await s.remove(scope=Scope.USER, key="wizard")
```

这个流程在并发场景下的隔离方式是：同一个 `key="wizard"` 会在 `Scope.USER` 下按用户标识符分桶存储，因此多个用户同时运行互不影响。

会话的“自动超时 + GC”由 SessionManager 后台循环处理：默认每 5 秒检查一次超时，每 30 秒执行一次垃圾回收；会话超时后先标记为 `INACTIVE`，并在达到 `inactive_gc_timeout` 后被自动删除。

---

## 八、下一步

- [常见问题 Q&A](./09_常见问题Q&A.md) — 错误码、调试指南、FAQ
- [联系和反馈](./10_联系和反馈.md) — 获取技术支持
