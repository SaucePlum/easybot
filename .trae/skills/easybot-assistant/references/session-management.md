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
@bot.on_command(command="test")
async def test_cmd(msg):
    with bot.session.bind(msg) as s:
        # s 自动从 msg 中提取用户标识
        s.new(Scope.USER, "key", {"data": "value"})
        session = s.get(Scope.USER, "key")
```

### 创建会话

```python
with bot.session.bind(msg) as s:
    # 创建新会话
    s.new(
        scope=Scope.USER,
        key="game_state",
        data={"score": 0, "level": 1},
        timeout=3600,  # 1小时超时
        timeout_reply="游戏会话已过期",  # 超时提示
        inactive_gc_timeout=300,  # 超时后5分钟清理
    )
```

### 获取会话

```python
with bot.session.bind(msg) as s:
    # 获取会话
    session = s.get(Scope.USER, "game_state")
    
    if session:
        print(f"分数: {session.data['score']}")
    else:
        print("会话不存在")
    
    # 带默认值
    session = s.get(Scope.USER, "game_state", default=None)
    
    # 窥视模式（不更新最后操作时间）
    session = s.get(Scope.USER, "game_state", skip_update_last_op=True)
```

### 更新会话

```python
with bot.session.bind(msg) as s:
    # 更新会话数据（合并）
    s.update(Scope.USER, "game_state", {
        "score": 100,
        "new_field": "value"
    })
```

### 删除会话

```python
with bot.session.bind(msg) as s:
    # 删除特定会话
    s.remove(scope=Scope.USER, key="game_state")
    
    # 删除用户所有会话
    s.remove(scope=Scope.USER)
    
    # 清空所有会话
    s.remove()
```

---

## wait_for 多轮对话

`wait_for` 是实现多轮对话的核心方法。

### 基本用法

```python
from easybot import Scope, WaitTimeoutError, WaitError

@bot.on_command(command="确认")
async def confirm_cmd(msg):
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
```

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
async def on_timeout():
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

### 手动持久化

```python
# 手动保存
bot.session.commit_data()

# 批量操作时关闭自动保存
# （需要在 SessionManager 初始化时设置 is_auto_commit=False）
```

### 恢复会话

程序重启后会话会自动恢复：

```python
@bot.on_command(command="继续")
async def continue_game(msg):
    with bot.session.bind(msg) as s:
        # 尝试恢复之前的会话
        session = s.get(Scope.USER, "game_state")
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
    s.new(
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
from easybot import SessionStatus

session = s.get(Scope.USER, "key")
if session:
    if session.status == SessionStatus.ACTIVE:
        print("会话活跃")
    elif session.status == SessionStatus.INACTIVE:
        print("会话已过期")
```

### with_session 装饰器

简化会话绑定的装饰器：

```python
from easybot import with_session

@bot.on_command(command="test")
@with_session  # 自动注入 session 参数
async def test_cmd(msg, session=None):
    # session 已绑定到 msg
    session.new(Scope.USER, "key", {"data": "value"})
    data = session.get(Scope.USER, "key")
```

### 多步骤表单

```python
@bot.on_command(command="注册")
async def register(msg):
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
        s.new(Scope.USER, "profile", {
            "username": username,
            "email": email
        })
        await msg.reply("✅ 注册成功！")
```

### 游戏状态管理

```python
@bot.on_command(command="猜数字")
async def guess_number(msg):
    import random
    target = random.randint(1, 100)
    attempts = 0
    
    with bot.session.bind(msg) as s:
        # 保存游戏状态
        s.new(
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
                session = s.get(Scope.USER, "guess_game")
                s.update(Scope.USER, "guess_game", {
                    "attempts": session.data["attempts"] + 1
                })
                
                if guess == target:
                    await msg.reply(f"🎉 恭喜你猜对了！用了 {session.data['attempts'] + 1} 次")
                    s.remove(scope=Scope.USER, key="guess_game")
                    break
                elif guess < target:
                    await msg.reply("太小了，再试试！")
                else:
                    await msg.reply("太大了，再试试！")
            
            except WaitTimeoutError:
                await msg.reply(f"⏰ 超时！答案是 {target}")
                s.remove(scope=Scope.USER, key="guess_game")
                break
```

---

## SessionObject 属性

```python
class SessionObject:
    scope: str          # 作用域
    status: int         # 状态（ACTIVE/INACTIVE）
    key: Hashable       # 会话键
    data: Dict          # 会话数据
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
class WaitError(Exception):
    """等待错误（等待任务被意外删除）"""
    pass

class WaitTimeoutError(Exception):
    """等待超时错误"""
    pass
```
