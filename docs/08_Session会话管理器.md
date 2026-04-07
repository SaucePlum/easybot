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
- `with` 块结束后自动解除绑定
- `BoundSession` 的方法签名**不需要传入 `obj` 参数**

### 3.2 @with_session 装饰器

使用装饰器自动注入绑定的 session：

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
```

**要点**：
- 装饰器放在事件注册器**之后**
- 处理函数必须接受 `session` 关键字参数（默认值 `None`）

---

## 四、API 参考

### 4.1 BoundSession.new — 创建会话

```python
session_obj = session.new(
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
| `timeout` | `float \| None` | ❌ | `None` | 超时时间（秒） |
| `timeout_reply` | `str \| Message \| ... \| None` | ❌ | `None` | 超时后自动发送的回复 |
| `inactive_gc_timeout` | `float` | ❌ | `0` | 非活跃会话的 GC 回收等待时间 |

**返回值**: `SessionObject`

### 4.2 BoundSession.get — 获取会话

```python
session_obj = session.get(
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

### 4.3 BoundSession.update — 更新会话数据

```python
session_obj = session.update(
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

### 4.4 BoundSession.remove — 删除会话

```python
# 清空某个作用域的所有会话
session.remove(scope=Scope.USER)

# 清空某作用域下某个 identify 的所有会话
session.remove(scope=Scope.USER, identify="user_123")

# 删除具体某个会话
session.remove(scope=Scope.USER, identify="user_123", key="my_session")
```

**行为总结**：

| scope | identify | key | 行为 |
|-------|----------|-----|------|
| 不传 | 不传 | 不传 | 清空所有作用域的所有会话 |
| 传了 | 不传 | 不传 | 清空该 scope 下所有会话 |
| 传了 | 传了 | 不传 | 清空该 scope+identify 下所有会话 |
| 传了 | 传了 | 传了 | 仅删除该具体会话 |

### 4.5 BoundSession.wait_for — 等待命令

等待指定的命令被触发。这是一个**异步方法**：

```python
result_msg = await session.wait_for(
    scopes=Scope.USER,              # 单个作用域或作用域列表
    command=["确认", "取消"],       # 字符串/列表/正则
    timeout=60,                     # 超时时间(秒)
    predicate=my_predicate_func,    # 可选：自定义匹配谓词函数
)
```

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `scopes` | `str \| Sequence[str]` | ✅ | 作用域或作用域列表 |
| `command` | `str \| Sequence[str] \| Pattern \| None` | ❌ | 要等待的命令 |
| `timeout` | `int \| None` | ❌ | 超时时间（秒），None 表示永远等待 |
| `predicate` | `Callable[[Any], bool] \| None` | ❌ | 自定义谓词函数 |
| `on_timeout` | `Callable[[], Any] \| None` | ❌ | 超时回调函数 |

**返回值**: 消息对象（`GuildMessage` / `GroupMessage` / `C2CMessage` / `DirectMessage`）

**异常**:
- `WaitTimeoutError` — 等待超时时抛出
- `WaitError` — 找不到对应的等待任务时抛出

**command 参数支持多种输入格式**：

```python
# 1. 字符串
result = await session.wait_for(scopes=Scope.USER, command="确认")

# 2. 列表/元组
result = await session.wait_for(scopes=Scope.USER, command=["确认", "取消"])

# 3. 正则表达式
from re import compile as re_compile
result = await session.wait_for(scopes=Scope.USER, command=re_compile(r"^(\d+)$"))

# 4. None - 接受任意输入
result = await session.wait_for(scopes=Scope.USER, command=None)
```

---

## 五、高级功能

### 5.1 超时自动回复

`new()` 方法的 `timeout` 和 `timeout_reply` 参数配合使用，可以在会话超时后**自动发送提示消息**：

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

### 5.2 自动持久化

SessionManager 默认开启自动持久化，将所有会话数据以 **pickle 格式**保存到本地文件：

- **存储路径**: 默认 `<工作目录>/sdk_data/sessions.pickle`
- **保存时机**: 会话创建、更新、删除时自动保存
- **加载时机**: Bot 启动时自动加载

```python
# 自定义存储路径
bot = Bot(
    app_id="xxx",
    app_secret="xxx",
    session_data_dir="/path/to/my_data",
)
```

### 5.3 垃圾回收机制

SessionManager 内置垃圾回收机制，定期清理过期会话：

- **GC 间隔**: 每 5 秒检查一次
- **回收条件**: 会话状态为 INACTIVE 且超过 `inactive_gc_timeout` 时间
- **超时触发**: 会话超过 `timeout` 时间未被访问时状态变为 INACTIVE

---

## 六、最佳实践

### 6.1 多步骤交互流程

```python
@bot.on_command(command="/order")
async def start_order(msg):
    with bot.session.bind(msg) as s:
        s.new(
            scope=Scope.USER,
            key="order",
            data={"step": 1, "items": []},
            timeout=600,
            timeout_reply="订单超时，请重新开始",
        )
    await msg.reply("开始下单！请输入商品名称")

@bot.on_guild_message
async def handle_order(msg):
    with bot.session.bind(msg) as s:
        session = s.get(scope=Scope.USER, key="order")
        if not session or session.status != 0:
            return

        step = session.data.get("step")
        
        if step == 1:
            s.update(scope=Scope.USER, key="order", data={
                "item": msg.content, "step": 2
            })
            await msg.reply(f"商品: {msg.content}\n请输入数量")
        
        elif step == 2:
            quantity = int(msg.content)
            s.update(scope=Scope.USER, key="order", data={
                "quantity": quantity, "step": 3
            })
            await msg.reply(f"数量: {quantity}\n确认订单？(是/否)")
        
        elif step == 3:
            if msg.content == "是":
                await msg.reply("✅ 订单已提交")
                s.remove(scope=Scope.USER, key="order")
            else:
                await msg.reply("订单已取消")
                s.remove(scope=Scope.USER, key="order")
```

### 6.2 使用 wait_for 简化交互

```python
@bot.on_command(command="/confirm")
async def confirm_action(msg):
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

### 6.3 群聊共享状态

```python
@bot.on_command(command="/vote")
async def start_vote(msg):
    with bot.session.bind(msg) as s:
        s.new(
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
async def handle_vote(msg):
    with bot.session.bind(msg) as s:
        session = s.get(scope=Scope.GROUP, key="vote")
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
            s.update(scope=Scope.GROUP, key="vote", data=session.data)
            await msg.reply(f"投票成功！当前票数: {session.data['options']}")
```

---

## 七、下一步

- [常见问题 Q&A](./09_常见问题Q&A.md) — 错误码、调试指南、FAQ
- [联系和反馈](./10_联系和反馈.md) — 获取技术支持
