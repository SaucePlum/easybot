---
name: easybot-assistant
description: |
  EasyBot QQ机器人开发助手 - 帮助开发者快速构建QQ官方机器人应用。
  
  使用场景：
  - 用户明确提及 "EasyBot"、"EasyBot SDK" 时
  - 用户提及 QQ机器人开发、QQ频道机器人、QQ群聊机器人、QQ官方机器人 时
  - 用户要求创建机器人项目、处理QQ消息事件、实现QQ机器人命令 时
  - 用户询问如何使用装饰器注册事件处理器、如何实现多轮对话、如何发送富媒体消息 时
  - 用户需要了解 QQ机器人 API、会话管理、插件系统、消息构建器 时
  
  技能涵盖：快速入门、插件系统、会话管理、消息构建、API参考、最佳实践、故障排除。
---

# EasyBot QQ机器人开发助手

## 概述

EasyBot 是一个轻量级 QQ 官方机器人 SDK，专注于简洁、易上手且稳定的开发体验。本技能帮助开发者快速掌握 EasyBot SDK 的使用方法，从基础入门到高级功能全面覆盖。

**核心特性：**
- 多协议支持：WebSocket、Webhook、远程 Webhook
- 装饰器风格的事件注册
- 强大的插件系统和命令处理
- 会话管理与多轮对话支持
- 丰富的消息构建器（Embed、Ark、Markdown）

## 快速入门

### 安装

```bash
pip install easybot-qq
```

### 最简示例

```python
from easybot import Bot, Model

bot = Bot(
    app_id="your_app_id",
    app_secret="your_app_secret",
)

@bot.on_guild_message
async def handle_message(msg: Model.GuildMessage):
    await msg.reply(f"收到：{msg.treated_msg}")

bot.start()
```

### 连接协议选择

```python
from easybot import Bot, Proto

# WebSocket 模式（默认，最常用）
bot = Bot(app_id="...", app_secret="...")

# Webhook 模式（需要公网 IP）
bot = Bot(
    app_id="...",
    app_secret="...",
    protocol=Proto.webhook(port=8080)
)

# 远程 Webhook 模式（通过中转服务器）
bot = Bot(
    app_id="...",
    app_secret="...",
    protocol=Proto.remote_webhook(url="wss://your-server.com")
)
```

## 核心概念

### 1. Bot 实例

Bot 是机器人的核心类，负责连接管理和事件分发：

```python
bot = Bot(
    app_id="your_app_id",        # 机器人 AppID
    app_secret="your_app_secret", # 机器人密钥
    is_private=False,             # 是否私域机器人
    is_sandbox=False,             # 是否沙箱环境
    is_debug=False,               # 是否调试模式
    auto_load_plugins=False,      # 是否自动加载插件
    plugins_dir="plugins",        # 插件目录
)
```

### 2. 事件处理器

使用装饰器注册事件处理器，**务必为每个处理器指定正确的类型提示**：

```python
# 频道@机器人消息
@bot.on_guild_message
async def on_guild(msg: Model.GuildMessage):
    await msg.reply("收到频道消息")

# 群聊@机器人消息
@bot.on_group_message
async def on_group(msg: Model.GroupMessage):
    await msg.reply("收到群聊消息")

# 单聊消息
@bot.on_c2c_message
async def on_c2c(msg: Model.C2CMessage):
    await msg.reply("收到私信")

# 频道私信
@bot.on_direct_message
async def on_dm(msg: Model.DirectMessage):
    await msg.reply("收到私信")
```

### 3. 消息模型

所有消息模型继承自 `MessageBase`，提供统一的 `reply()` 方法：

**推荐使用 `reply()` 方法进行快速回复**，只有在复杂场景（如主动发送消息到其他频道）才需要调用 API：

```python
@bot.on_guild_message
async def handle(msg: Model.GuildMessage):
    # 基本属性
    msg.id           # 消息 ID
    msg.content      # 原始内容
    msg.treated_msg  # 处理后的内容（去除@等）
    msg.author       # 发送者信息
    msg.timestamp    # 时间戳
    
    # 推荐：使用 reply() 快速回复
    await msg.reply("回复内容")
    await msg.reply("引用回复", reference=True)
    
    # 复杂场景：主动发送消息到其他频道
    await bot.api.send_guild_message(
        channel_id="其他频道ID",
        content="主动消息"
    )
```

### 4. 命令系统

使用 `@bot.on_command` 注册命令处理器，**类型提示应与 `valid_scenes` 匹配**：

```python
from easybot import CommandValidScenes, Model

# 仅频道场景 -> 使用 GuildMessage
@bot.on_command(
    command="频道命令",
    valid_scenes=CommandValidScenes.GUILD,
)
async def guild_cmd(msg: Model.GuildMessage):
    print(msg.channel_id)  # 可访问频道特有字段
    await msg.reply("频道命令执行")

# 仅群聊场景 -> 使用 GroupMessage
@bot.on_command(
    command="群聊命令",
    valid_scenes=CommandValidScenes.GROUP,
)
async def group_cmd(msg: Model.GroupMessage):
    print(msg.group_openid)  # 可访问群聊特有字段
    await msg.reply("群聊命令执行")

# 仅单聊场景 -> 使用 C2CMessage
@bot.on_command(
    command="私聊命令",
    valid_scenes=CommandValidScenes.C2C,
)
async def c2c_cmd(msg: Model.C2CMessage):
    await msg.reply("私聊命令执行")

# 多场景或全部场景 -> 使用 Union 或 MessageBase
@bot.on_command(
    command=["hello", "你好"],
    valid_scenes=CommandValidScenes.GUILD | CommandValidScenes.GROUP,
)
async def hello_cmd(msg: Model.GuildMessage | Model.GroupMessage):
    # 类型提示精确，IDE 可正确推断
    if isinstance(msg, Model.GuildMessage):
        print(msg.channel_id)
    else:
        print(msg.group_openid)
    await msg.reply("你好！")

# 全部场景 -> 使用 MessageBase
@bot.on_command(
    command="全局命令",
    valid_scenes=CommandValidScenes.ALL,
)
async def global_cmd(msg: Model.MessageBase):
    # 四种场景都可能，需判断类型
    await msg.reply("全局命令执行")
```

### 5. 会话管理

使用 `session.bind()` 实现多轮对话：

```python
from easybot import Scope, WaitTimeoutError, Model

@bot.on_command(command="猜数字", valid_scenes=CommandValidScenes.ALL)
async def guess_game(msg: Model.MessageBase):
    import random
    target = random.randint(1, 100)
    
    with bot.session.bind(msg) as s:
        await msg.reply("我想了一个1-100的数字，猜猜看！")
        
        while True:
            try:
                reply = await s.wait_for(
                    scopes=Scope.USER,
                    timeout=60
                )
                guess = int(reply.content)
                
                if guess == target:
                    await msg.reply("恭喜你猜对了！")
                    break
                elif guess < target:
                    await msg.reply("太小了，再试试！")
                else:
                    await msg.reply("太大了，再试试！")
            except WaitTimeoutError:
                await msg.reply("超时了，游戏结束！")
                break
```

## 消息构建

### Embed 消息

```python
from easybot import MessagesModel

embed = MessagesModel.MessageEmbed(
    title="标题",
    prompt="提示文本",
    content=[
        "第一行内容",
        "第二行内容",
    ],
    image="https://example.com/image.png"
)
await msg.reply(embed)
```

### Markdown 消息

```python
markdown = MessagesModel.MessageMarkdown(
    content="# 标题\n**粗体** *斜体*"
)
await msg.reply(markdown)
```

### 按钮键盘

```python
md = MessagesModel.MessageMarkdown(
    content="请选择：",
    keyboard_content={
        "rows": [
            {
                "buttons": [
                    {
                        "render_data": {"label": "按钮1", "style": 1},
                        "action": {"type": 1, "data": "callback_data"}
                    }
                ]
            }
        ]
    }
)
await msg.reply(md)
```

## 生命周期事件

```python
from easybot import Model

@bot.on_startup
async def on_startup(event: Model.StartupEvent):
    bot.logger.info("机器人启动成功")

@bot.on_shutdown
async def on_shutdown(event: Model.ShutdownEvent):
    bot.logger.info("机器人正在关闭")

@bot.on_timer(interval=60)
async def on_timer(event: Model.TimerEvent):
    bot.logger.info("定时任务执行")
```

## 代码模板

### 基础机器人模板

```python
from easybot import Bot, Model, CommandValidScenes

bot = Bot(
    app_id="your_app_id",
    app_secret="your_app_secret",
    is_debug=True,
)

# 预处理器：多场景使用 MessageBase
@bot.before_command(valid_scenes=CommandValidScenes.ALL)
async def log_message(msg: Model.MessageBase):
    bot.logger.info(f"收到消息: {msg.treated_msg}")

# 事件处理器：使用具体类型
@bot.on_guild_message
async def on_guild(msg: Model.GuildMessage):
    await msg.reply(f"收到: {msg.treated_msg}")

# 命令处理器：根据 valid_scenes 选择类型
@bot.on_command(command="ping", valid_scenes=CommandValidScenes.ALL)
async def ping(msg: Model.MessageBase):
    await msg.reply("pong!")

bot.start()
```

### 插件开发模板

```python
from easybot import Plugins, CommandValidScenes, Model

@Plugins.before_command(valid_scenes=CommandValidScenes.ALL)
def preprocessor(msg: Model.MessageBase):
    print(f"预处理: {msg.treated_msg}")

@Plugins.on_command(
    command=["help", "帮助"],
    valid_scenes=CommandValidScenes.ALL
)
async def help_command(msg: Model.MessageBase):
    await msg.reply("这是帮助信息")

def register(bot):
    bot.logger.info("插件已加载")
```

## 消息类型对照表

### 事件处理器类型

| 场景 | 装饰器 | 消息类型 | 说明 |
|------|--------|----------|------|
| 频道@机器人 | `@bot.on_guild_message` | `Model.GuildMessage` | 公域机器人@消息 |
| 频道全量 | `@bot.on_guild_full_message` | `Model.GuildMessage` | 私域机器人全量消息 |
| 群聊@机器人 | `@bot.on_group_message` | `Model.GroupMessage` | 群聊@消息 |
| 单聊 | `@bot.on_c2c_message` | `Model.C2CMessage` | QQ单聊消息 |
| 频道私信 | `@bot.on_direct_message` | `Model.DirectMessage` | 频道私信 |
| 互动按钮 | `@bot.on_interaction` | `Model.Interaction` | 按钮点击事件 |

### 命令处理器类型（根据 valid_scenes 选择）

| valid_scenes | 消息类型 | 说明 |
|--------------|----------|------|
| `CommandValidScenes.GUILD` | `Model.GuildMessage` | 仅频道 |
| `CommandValidScenes.GROUP` | `Model.GroupMessage` | 仅群聊 |
| `CommandValidScenes.C2C` | `Model.C2CMessage` | 仅单聊 |
| `CommandValidScenes.DM` | `Model.DirectMessage` | 仅频道私信 |
| 多场景组合 | `Union` 或 `\|` 语法 | 如 `GuildMessage \| GroupMessage` |
| `CommandValidScenes.ALL` | `Model.MessageBase` | 四种场景都可能 |

### 多场景类型提示示例

```python
from typing import Union
from easybot import CommandValidScenes, Model

# 方式1：使用 Union（Python 3.9 及以下）
@bot.on_command(
    command="测试",
    valid_scenes=CommandValidScenes.GUILD | CommandValidScenes.GROUP,
)
async def test_cmd(msg: Union[Model.GuildMessage, Model.GroupMessage]):
    if isinstance(msg, Model.GuildMessage):
        print(f"频道: {msg.channel_id}")
    else:
        print(f"群聊: {msg.group_openid}")

# 方式2：使用 | 语法（Python 3.10+）
@bot.on_command(
    command="测试",
    valid_scenes=CommandValidScenes.GUILD | CommandValidScenes.GROUP,
)
async def test_cmd(msg: Model.GuildMessage | Model.GroupMessage):
    if isinstance(msg, Model.GuildMessage):
        print(f"频道: {msg.channel_id}")
    else:
        print(f"群聊: {msg.group_openid}")
```

## 参考文档

根据需要查阅以下详细文档：

| 文档 | 说明 |
|------|------|
| [API 参考](references/api-reference.md) | 完整的 API 方法列表 |
| [插件系统](references/plugin-system.md) | 插件开发完整指南 |
| [会话管理](references/session-management.md) | Session 和 wait_for 详细用法 |
| [消息构建器](references/message-builders.md) | Embed、Ark、Markdown 等消息格式 |
| [最佳实践](references/best-practices.md) | 代码规范、性能优化、安全实践 |
| [故障排除](references/troubleshooting.md) | 错误码、调试指南、FAQ |

## 示例项目

完整示例项目位于 `assets/examples/` 目录：

- **猜数字游戏** - 展示会话管理和多轮对话
- **待办事项机器人** - 展示数据持久化和命令系统
- **客服问答机器人** - 展示富媒体消息和交互设计

---

**注意：** 本技能基于 EasyBot SDK 最新版本，如遇 API 变更请参考官方文档。
