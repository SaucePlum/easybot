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

## 四、API 参考

### 4.1 BoundSession.new — 创建会话

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

### 4.2 BoundSession.get — 获取会话

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

### 4.3 BoundSession.update — 更新会话数据

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

### 4.4 BoundSession.remove — 删除会话

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

### 4.5 BoundSession.wait_for — 等待命令

等待指定的命令被触发。这是一个**异步方法**：

```python
from easybot import Scope

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

### 5.2 自动持久化

SessionManager 默认开启自动持久化，将所有会话数据以 **pickle 格式**保存到本地文件：

- **存储路径**: 默认 `<工作目录>/sdk_data/sessions.pickle`
- **保存时机**: 会话创建、更新、删除时自动保存
- **加载时机**: Bot 启动时自动加载

> **注意**: 当前版本暂不支持通过 Bot 构造函数自定义会话存储路径。会话数据默认保存在工作目录下的 `sdk_data/sessions.pickle` 文件中。

### 5.3 垃圾回收机制

SessionManager 内置垃圾回收机制，定期清理过期会话：

- **GC 间隔**: 每 5 秒检查一次
- **回收条件**: 会话状态为 INACTIVE 且超过 `inactive_gc_timeout` 时间
- **超时触发**: 会话超过 `timeout` 时间未被访问时状态变为 INACTIVE

---

## 六、最佳实践

### 6.1 多步骤交互流程

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

### 6.2 使用 wait_for 简化交互

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

### 6.3 两步收集姓名和年龄（WaitFor + 超时）

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
                command=re_compile(r"^\\d{1,3}$"),
                timeout=30,
            )
        except WaitTimeoutError:
            await msg.reply("⏰ 超时未收到年龄，请重新开始")
            return

        age = int(age_msg.content.strip())
        await msg.reply(f"收到：姓名={name}，年龄={age}")
```

### 6.4 群聊共享状态

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

### 6.5 并发多场景多轮对话（跨频道/群聊/C2C + 超时 + GC）

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
from typing import Any

from easybot import CommandValidScenes, Model, Scope, WaitError, WaitTimeoutError

@bot.on_command(command="/wizard", valid_scenes=CommandValidScenes.ALL)
async def wizard(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
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

## 七、下一步

- [常见问题 Q&A](./09_常见问题Q&A.md) — 错误码、调试指南、FAQ
- [联系和反馈](./10_联系和反馈.md) — 获取技术支持
