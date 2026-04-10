# EasyBot 会话管理完整文档

## 目录

1. [概述](#概述)
2. [会话作用域](#会话作用域)
3. [基本操作](#基本操作)
4. [wait_for 多轮对话](#wait_for-多轮对话)
5. [会话持久化](#会话持久化)
6. [高级用法](#高级用法)

---

## 概述

EasyBot 会话管理系统提供了强大的状态管理和多轮对话能力：

- **多作用域**：用户级、频道级、群聊级、全局级
- **持久化**：自动保存到文件，重启后恢复
- **超时机制**：自动清理过期会话
- **wait_for**：等待用户输入，实现多轮对话

---

## 会话作用域

使用 `Scope` 定义会话的隔离级别：

```python
from easybot import Scope

Scope.USER    # 用户级别 - 同一用户在不同地方隔离
Scope.GUILD   # 频道级别 - 同一频道内共享
Scope.CHANNEL # 子频道级别 - 同一子频道内共享
Scope.GROUP   # 群聊级别 - 同一群内共享
Scope.GLOBAL  # 全局级别 - 整个机器人共享
```

### 作用域选择指南

| 作用域 | 适用场景 | 示例 |
|--------|----------|------|
| USER | 用户个人状态、游戏进度 | 猜数字游戏、个人设置 |
| GUILD | 频道公共状态 | 频道配置、公告 |
| CHANNEL | 子频道特定状态 | 子频道主题、规则 |
| GROUP | 群聊公共状态 | 群公告、群游戏 |
| GLOBAL | 全局状态 | 系统配置、统计 |

---

## 基本操作

### 绑定消息对象

使用 `session.bind()` 上下文管理器绑定消息：

```python
from easybot import Model

@bot.on_command(command="test")
async def test_cmd(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
) -> None:
    with bot.session.bind(msg) as s:
        # s 自动从 msg 中提取用户标识
        # 注意：所有会话操作都是异步方法
        await s.new(Scope.USER, "key", {"data": "value"})
        session = await s.get(Scope.USER, "key")
```

### 创建会话

```python
with bot.session.bind(msg) as s:
    # 创建新会话（异步方法）
    await s.new(
        scope=Scope.USER,
        key="game_state",
        data={"score": 0, "level": 1},
        timeout=3600,  # 1小时超时（默认 1800 秒/30 分钟）
        timeout_reply="游戏会话已过期",  # 超时提示（支持多种消息类型）
        inactive_gc_timeout=300,  # 超时后5分钟清理
        is_replace=True,  # 是否替换现有会话（默认 True）
        send_reply_on_msg_id_expired=False,  # msg_id过期后是否仍发送
    )
```

> **重要说明**：
> 1. `timeout` 参数有默认值 **1800 秒（30 分钟）**。即使不显式设置，会话也会在 30 分钟无操作后自动超时，防止永久占用内存和存储。
> 2. `is_replace` 参数控制是否替换现有会话：
>    - `True`（默认）：如果会话已存在，直接替换
>    - `False`：如果会话已存在，抛出 `KeyError` 异常
> 3. `timeout_reply` 支持多种消息类型：
>    - 字符串：`"游戏会话已过期"`
>    - Embed 消息：`MessagesModel.MessageEmbed(title="超时", content=["会话已过期"])`
>    - Markdown 消息：`MessagesModel.MessageMarkdown(content="# 超时提示")`
>    - Ark 消息：`MessagesModel.MessageArk23/24/37(...)`

### 获取会话

```python
with bot.session.bind(msg) as s:
    # 获取会话（异步方法）
    session = await s.get(Scope.USER, "game_state")
    
    if session:
        print(f"分数: {session.data['score']}")
    else:
        print("会话不存在")
    
    # 带默认值
    session = await s.get(Scope.USER, "game_state", default=None)
    
    # 窥视模式（不更新最后操作时间）
    session = await s.get(Scope.USER, "game_state", skip_update_last_op=True)
```

### 更新会话

```python
with bot.session.bind(msg) as s:
    # 更新会话数据（合并，异步方法）
    await s.update(Scope.USER, "game_state", {
        "score": 100,
        "new_field": "value"
    })
```

### 删除会话

```python
with bot.session.bind(msg) as s:
    # 删除特定会话（异步方法）
    await s.remove(scope=Scope.USER, key="game_state")
    
    # 删除用户所有会话
    await s.remove(scope=Scope.USER)
    
    # 清空所有会话
    await s.remove()
```

---

## wait_for 多轮对话

`wait_for` 是实现多轮对话的核心方法。

### 方法签名

```python
async def wait_for(
    self,
    scopes: str | Sequence[str],
    command: BotCommandObject | str | Sequence[str] | Pattern[str] | None = None,
    timeout: int | None = None,
    predicate: Callable[[Any], bool] | None = None,
    on_timeout: Callable[[], None] | None = None,
) -> GuildMessage | GroupMessage | C2CMessage | DirectMessage:
    """
    等待用户发送匹配的消息

    Args:
        scopes: 作用域，可以是单个作用域或作用域列表
        command: 命令匹配，支持多种类型：
            - BotCommandObject: 直接传入命令对象，可使用全部参数
            - str: 精确匹配消息内容
            - list/tuple: 匹配列表中的任意一个
            - Pattern: 正则表达式匹配
            - None: 接受任意输入
        timeout: 超时时间（秒）
        predicate: 自定义过滤函数
        on_timeout: 超时回调函数

    Returns:
        匹配的消息对象，类型取决于消息来源场景：
            - GuildMessage: 频道消息
            - GroupMessage: 群聊消息
            - C2CMessage: 单聊消息
            - DirectMessage: 频道私信消息

    Raises:
        WaitTimeoutError: 等待超时
        WaitError: 等待任务被意外删除
    """
```

**重要提示：**
1. 这是一个异步方法，必须使用 `await` 调用
2. 使用轮询机制检查消息，轮询间隔为 **0.5 秒**
3. 当使用快捷方式（`str`/`list`/`Pattern`）时，会自动包装为 `BotCommandObject(valid_scenes=CommandValidScenes.ALL)`

### 基本用法

```python
from easybot import Model, Scope, WaitTimeoutError, WaitError

@bot.on_command(command="确认")
async def confirm_cmd(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
) -> None:
    with bot.session.bind(msg) as s:
        await msg.reply("请在30秒内回复「是」或「否」")
        
        try:
            result = await s.wait_for(
                scopes=Scope.USER,
                command=["是", "否"],
                timeout=30
            )
            
            if "是" in result.content:
                await msg.reply("✅ 已确认")
            else:
                await msg.reply("❌ 已取消")
        
        except WaitTimeoutError:
            await msg.reply("⏰ 等待超时")
        except WaitError as e:
            await msg.reply(f"❌ 错误: {e}")
```

### 命令匹配

```python
# 精确匹配
result = await s.wait_for(
    scopes=Scope.USER,
    command="yes",
    timeout=30
)

# 多个选项
result = await s.wait_for(
    scopes=Scope.USER,
    command=["yes", "no", "cancel"],
    timeout=30
)

# 正则匹配
import re
result = await s.wait_for(
    scopes=Scope.USER,
    command=re.compile(r"\d+"),  # 匹配数字
    timeout=30
)

# 接受任意输入
result = await s.wait_for(
    scopes=Scope.USER,
    timeout=30
)

# 高级用法：使用 BotCommandObject
from easybot import BotCommandObject
cmd = BotCommandObject(
    command="确认",
    admin=True,  # 仅管理员可触发
    admin_error_msg="需要管理员权限",
    at=True,  # 需要@机器人
)
result = await s.wait_for(
    scopes=Scope.USER,
    command=cmd,
    timeout=60
)
```

> **重要说明**：
> - 当使用快捷方式（`str`/`list`/`Pattern`）传入 `command` 时，内部会自动包装为 `BotCommandObject(valid_scenes=CommandValidScenes.ALL)`
> - 如需使用高级参数（如权限校验、@要求等），请直接构造并传入 `BotCommandObject` 实例
> - `wait_for` 使用 `asyncio.Future` 实现即时唤醒，消息到达时直接通知等待者，无轮询延迟

### 自定义过滤

```python
def is_valid_number(msg):
    try:
        num = int(msg.content)
        return 1 <= num <= 100
    except ValueError:
        return False

result = await s.wait_for(
    scopes=Scope.USER,
    timeout=60,
    predicate=is_valid_number  # 自定义过滤函数
)
```

### 多作用域等待

```python
# 等待来自特定频道或群的消息
result = await s.wait_for(
    scopes=[Scope.GUILD, Scope.GROUP],
    command="确认",
    timeout=30
)
```

### 超时回调

```python
def on_timeout():
    bot.logger.info("等待超时")

result = await s.wait_for(
    scopes=Scope.USER,
    timeout=30,
    on_timeout=on_timeout
)
```

---

## 会话持久化

### 自动持久化

默认情况下，会话会自动保存到 `sdk_data/sessions.pickle`：

```python
bot = Bot(
    app_id="...",
    app_secret="...",
    # 会话自动持久化，无需额外配置
)
```

### 自定义持久化配置

```python
from easybot import Bot

bot = Bot(
    app_id="...",
    app_secret="...",
    # 自定义会话管理器配置（高级用法）
)

# 通过 bot.session 访问会话管理器
# 注意：以下参数需要在 Bot 初始化时通过其他方式配置
# commit_path: 会话数据持久化路径，默认为当前目录下的 sdk_data
# is_auto_commit: 是否自动持久化，默认为 True
```

> **说明**：
> - `commit_path`：会话数据保存路径，默认为 `./sdk_data/sessions.pickle`
> - `is_auto_commit`：
>   - `True`（默认）：每次会话操作后自动保存，数据安全但性能略低
>   - `False`：需要手动调用 `commit_data()`，适合高频操作场景

### 手动持久化

```python
# 手动保存（异步方法）
await bot.session.commit_data()

# 批量操作时关闭自动保存（需要在初始化时设置 is_auto_commit=False）
# 然后手动保存
await bot.session.commit_data(is_info=False)  # is_info=False 不记录日志
```

### 恢复会话

程序重启后会话会自动恢复：

```python
from easybot import Model

@bot.on_command(command="继续")
async def continue_game(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
) -> None:
    with bot.session.bind(msg) as s:
        # 尝试恢复之前的会话
        session = await s.get(Scope.USER, "game_state")
        if session:
            await msg.reply(f"继续游戏，当前分数: {session.data['score']}")
        else:
            await msg.reply("没有找到之前的游戏记录")
```

---

## 高级用法

### 超时回复

```python
with bot.session.bind(msg) as s:
    await s.new(
        scope=Scope.USER,
        key="waiting_payment",
        data={"order_id": "12345"},
        timeout=300,  # 5分钟超时
        timeout_reply="⏰ 支付超时，订单已取消",
        send_reply_on_msg_id_expired=True,  # msg_id过期后仍发送
    )
```

### 会话状态检查

```python
from easybot.models import SessionStatus

with bot.session.bind(msg) as s:
    session = await s.get(Scope.USER, "key")
    if session:
        if session.status == SessionStatus.ACTIVE:
            print("会话活跃")
        elif session.status == SessionStatus.INACTIVE:
            print("会话已过期")
```

### with_session 装饰器

简化会话绑定的装饰器：

```python
from easybot import BoundSession, Model, Scope, with_session

@bot.on_command(command="test")
@with_session  # 自动注入 session 参数
async def test_cmd(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
    session: BoundSession | None = None,
) -> None:
    # session 已绑定到 msg，所有操作都是异步方法
    if not session:
        return
    await session.new(Scope.USER, "key", {"data": "value"})
    data = await session.get(Scope.USER, "key")
```

### 多步骤表单

```python
from easybot import Model

@bot.on_command(command="注册")
async def register(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
) -> None:
    with bot.session.bind(msg) as s:
        # 步骤1：获取用户名
        await msg.reply("请输入用户名：")
        name_result = await s.wait_for(scopes=Scope.USER, timeout=60)
        username = name_result.content.strip()
        
        # 步骤2：获取邮箱
        await msg.reply("请输入邮箱：")
        email_result = await s.wait_for(scopes=Scope.USER, timeout=60)
        email = email_result.content.strip()
        
        # 步骤3：确认
        await msg.reply(f"确认注册？\n用户名: {username}\n邮箱: {email}\n回复「确认」继续")
        confirm_result = await s.wait_for(
            scopes=Scope.USER,
            command="确认",
            timeout=30
        )
        
        # 保存数据
        await s.new(Scope.USER, "profile", {
            "username": username,
            "email": email
        })
        await msg.reply("✅ 注册成功！")
```

### 游戏状态管理

```python
from easybot import Model

@bot.on_command(command="猜数字")
async def guess_number(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
) -> None:
    import random
    target = random.randint(1, 100)
    attempts = 0
    
    with bot.session.bind(msg) as s:
        # 保存游戏状态
        await s.new(
            scope=Scope.USER,
            key="guess_game",
            data={"target": target, "attempts": 0},
            timeout=300,
            timeout_reply="游戏超时结束"
        )
        
        await msg.reply("我想了一个1-100的数字，开始猜吧！")
        
        while True:
            try:
                result = await s.wait_for(
                    scopes=Scope.USER,
                    timeout=60
                )
                
                try:
                    guess = int(result.content)
                except ValueError:
                    await msg.reply("请输入数字！")
                    continue
                
                # 更新尝试次数
                session = await s.get(Scope.USER, "guess_game")
                await s.update(Scope.USER, "guess_game", {
                    "attempts": session.data["attempts"] + 1
                })
                
                if guess == target:
                    await msg.reply(f"🎉 恭喜你猜对了！用了 {session.data['attempts'] + 1} 次")
                    await s.remove(scope=Scope.USER, key="guess_game")
                    break
                elif guess < target:
                    await msg.reply("太小了，再试试！")
                else:
                    await msg.reply("太大了，再试试！")
            
            except WaitTimeoutError:
                await msg.reply(f"⏰ 超时！答案是 {target}")
                await s.remove(scope=Scope.USER, key="guess_game")
                break
```

### 取消等待任务

使用 `clear_wait_for()` 方法强制取消等待任务：

```python
from easybot import Model, Scope

@bot.on_command(command="取消", valid_scenes=CommandValidScenes.ALL)
async def cancel_wait(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
) -> None:
    with bot.session.bind(msg) as s:
        # 取消特定用户的所有等待任务
        bot.session.clear_wait_for(scope=Scope.USER, identify=msg.author.id)
        await msg.reply("已取消所有等待任务")
        
        # 取消所有等待任务
        bot.session.clear_wait_for()
```

> **说明**：
> - 清除等待任务后，对应的 `wait_for()` 会抛出 `WaitError` 异常
> - 适用于用户主动取消操作、强制中断等待等场景

---

## 会话超时与垃圾回收机制

### 超时机制详解

会话超时采用**两阶段清理**机制：

1. **超时阶段**：会话变为 `INACTIVE` 状态
   - 如果设置了 `timeout_reply`，会发送超时提示消息
   - 会话数据仍然保留，用户有机会"恢复"

2. **GC 清理阶段**：真正删除会话数据
   - 根据 `inactive_gc_timeout` 参数延迟清理
   - 默认立即清理（`inactive_gc_timeout=0`）

### 时间线示例

```python
# 创建会话，设置超时和延迟清理
await s.new(
    scope=Scope.USER,
    key="payment",
    data={"order_id": "12345"},
    timeout=300,  # 5分钟无操作后超时
    timeout_reply="支付超时，订单已取消",
    inactive_gc_timeout=600,  # 超时后10分钟才真正删除
)

# 时间线：
# T=0: 创建会话
# T=300: 会话超时，变为 INACTIVE，发送超时提示
# T=900: GC 清理会话数据（超时后600秒）
```

### 启动时清理

程序重启时会自动清理已过期的会话：

```python
# 程序停机期间可能已有会话超时
# 启动时会检查并清理这些会话
# 避免用户 get() 到本该过期的会话
```

### GC 清理周期

- **检查频率**：每 5 秒检查一次会话超时状态
- **清理频率**：每 30 秒执行一次垃圾回收
- **性能优化**：使用 `yield_threshold` 机制，每处理 100 个会话让出事件循环

---

## SessionObject 属性

```python
class SessionObject:
    scope: str          # 作用域
    status: int         # 状态（ACTIVE/INACTIVE）
    key: Hashable       # 会话键
    data: dict          # 会话数据
    identify: Hashable  # 标识符
```

## SessionStatus 常量

```python
class SessionStatus:
    ACTIVE = 0    # 活跃状态
    INACTIVE = 1  # 非活跃状态（已超时）
```

## 异常类型

```python
from easybot import WaitError, WaitTimeoutError
```
