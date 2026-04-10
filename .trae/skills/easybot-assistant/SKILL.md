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
- 完善的权限控制（频道管理员、机器人管理员）

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

### 参数类型提示约束

**所有函数参数都必须使用 SDK 提供的类型进行标注**，包括 `msg`、`session` 等任何参数。禁止使用裸参数名（如 `msg`）而不加类型提示。

正确示例：
```python
async def on_guild(msg: Model.GuildMessage): ...
async def help_cmd(msg: Model.GuildMessage | Model.GroupMessage): ...
async def form_step(msg: Model.GuildMessage, session: BoundSession): ...
```

错误示例（会导致 SDK 无法正确识别类型）：
```python
async def on_guild(msg): ...           # 缺少类型提示
async def on_group(msg: Model.GroupMessage | Model.C2CMessage | Model.GuildMessage): ...  # 混入了不存在于 SDK 的联合类型
```



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
    plugins_recursive=False,      # 是否递归加载插件
    max_concurrency=64,           # 事件处理器/命令最大并发数
)
```

### 2. 事件处理器

使用装饰器注册事件处理器，**必须为每个处理器参数添加类型提示**（如 `msg: Model.GuildMessage`），否则 SDK 无法正确识别消息类型，可能导致意外行为：

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

所有消息模型继承自 `MessageBase`，提供统一的 `reply()` 方法和 `api` 属性：

**推荐使用 `reply()` 方法进行快速回复**；如需主动调用其他接口，可通过 `msg.api` 或 `bot.api` 访问 API 实例：

- `msg.api`：在消息事件处理器（`@bot.on_xxx`、`@bot.on_command` 等）中可用，两者等价
- `bot.api`：在任意上下文中可用，包括生命周期事件（`@bot.on_startup`、`@bot.on_shutdown`、`@bot.on_timer` 等）；**在生命周期回调中必须使用 `bot.api`，因为此时没有消息模型**

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

    # 复杂场景：通过 msg.api 或 bot.api 主动调用接口（两者等价）
    await msg.api.send_guild_message(
        channel_id="其他子频道ID",
        content="主动消息"
    )
    # 或
    await bot.api.send_guild_message(
        channel_id="其他子频道ID",
        content="主动消息"
    )

# 生命周期回调中必须使用 bot.api（此时没有 msg 对象）
@bot.on_startup
async def on_startup(event: Model.StartupEvent):
    # 机器人启动时主动发送消息
    await bot.api.send_c2c_message(openid="用户ID", content="机器人已上线")
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

# 多场景或全部场景 -> 使用 Union 类型
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

# 全部场景 -> 使用 Union 类型
@bot.on_command(
    command="全局命令",
    valid_scenes=CommandValidScenes.ALL,
)
async def global_cmd(msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage):
    # 四种场景都可能，需判断类型
    if isinstance(msg, Model.GuildMessage):
        print(f"频道: {msg.channel_id}")
    elif isinstance(msg, Model.GroupMessage):
        print(f"群聊: {msg.group_openid}")
    elif isinstance(msg, Model.C2CMessage):
        print(f"单聊: {msg.author.user_openid}")
    else:
        print(f"私信: {msg.author.id}")
    await msg.reply("全局命令执行")
```

### 5. 会话管理

使用 `session.bind()` 实现多轮对话。**重要：所有会话操作方法都是异步的，必须使用 `await` 调用。**

```python
from easybot import Scope, WaitTimeoutError, Model

@bot.on_command(command="猜数字", valid_scenes=CommandValidScenes.ALL)
async def guess_game(msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage):
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

## 大文件分片上传

EasyBot 支持上传超过 10MB 的大文件，适用于视频、大文档等场景。

### 文件大小限制

| 文件类型 | 大小限制 | file_type |
|---------|---------|-----------|
| 图片 | 10MB | 1 |
| 视频 | 100MB | 2 |
| 语音 | 10MB | 3 |
| 文件 | 100MB | 4 |

### 一键上传（推荐）

```python
# 一键上传大文件
result = await bot.api.upload_large_file(
    file_path="./videos/large_video.mp4",
    file_type=2,  # 1=图片, 2=视频, 3=语音, 4=文件
    user_openid="user_xxx",  # 单聊场景
    # group_openid="group_xxx",  # 群聊场景（二选一）
)

# 使用 file_info 发送消息
await bot.api.send_c2c_message(
    openid="user_xxx",
    content="视频已上传",
    media_file_info=result.file_info,
)
```

### 手动控制流程

```python
import hashlib

# 步骤1：计算文件哈希
with open("large_file.mp4", "rb") as f:
    file_data = f.read()
    file_md5 = hashlib.md5(file_data).hexdigest()
    file_sha1 = hashlib.sha1(file_data).hexdigest()
    md5_10m = (
        hashlib.md5(file_data[:10002432]).hexdigest()
        if len(file_data) >= 10002432
        else file_md5
    )

# 步骤2：申请上传
prepare = await bot.api.upload_prepare(
    file_type=2,
    file_name="large_file.mp4",
    file_size=len(file_data),
    md5=file_md5,
    sha1=file_sha1,
    md5_10m=md5_10m,
    user_openid="user_xxx",
)

# 步骤3：上传分片
for part in prepare.parts:
    offset = (part.index - 1) * prepare.block_size
    chunk_data = file_data[offset:offset + prepare.block_size]
    
    await bot.api.upload_part(
        presigned_url=part.presigned_url,
        part_data=chunk_data,
        upload_id=prepare.upload_id,
        part_index=part.index,
        user_openid="user_xxx",
    )

# 步骤4：完成上传
result = await bot.api.upload_complete(
    upload_id=prepare.upload_id,
    user_openid="user_xxx",
)
```

### 注意事项

1. **文件名限制**：文件名不能包含敏感关键词（如 `url`、`http`、`www` 等）
2. **场景选择**：`user_openid` 和 `group_openid` 必须提供其中之一
3. **有效期**：`file_info` 有有效期（`ttl` 秒），过期后需重新上传

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

# 预处理器：多场景使用 Union 类型
@bot.before_command(valid_scenes=CommandValidScenes.ALL)
async def log_message(msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage):
    bot.logger.info(f"收到消息: {msg.treated_msg}")

# 事件处理器：使用具体类型
@bot.on_guild_message
async def on_guild(msg: Model.GuildMessage):
    await msg.reply(f"收到: {msg.treated_msg}")

# 命令处理器：根据 valid_scenes 选择类型
@bot.on_command(command="ping", valid_scenes=CommandValidScenes.ALL)
async def ping(msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage):
    await msg.reply("pong!")

bot.start()
```

### 插件开发模板

使用 `@Plugins` 装饰器直接在模块顶层注册命令/预处理器：

```python
from easybot import Plugins, CommandValidScenes, Model

@Plugins.before_command(valid_scenes=CommandValidScenes.ALL)
async def preprocessor(msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage):
    print(f"预处理: {msg.treated_msg}")

@Plugins.on_command(
    command=["help", "帮助"],
    valid_scenes=CommandValidScenes.ALL
)
async def help_command(msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage):
    await msg.reply("这是帮助信息")
```

> **说明**：插件被自动加载时，SDK 会扫描模块中所有 `@Plugins.on_command` 和 `@Plugins.before_command` 装饰的函数并自动注册。

### 插件热重载

EasyBot 支持插件热重载，无需重启机器人即可更新插件代码：

```python
# 热重载单个插件（通过插件名或命令名）
result = bot.reload_plugin("admin")  # 插件名
result = bot.reload_plugin("help")   # 命令名

# 热重载所有插件
results = bot.reload_all_plugins()

# 卸载插件
bot.unload_plugin("admin")

# 获取已加载的插件列表
plugins = bot.get_loaded_plugins()
```

**重载结果示例：**

```python
{
    "module": "admin",
    "success": True,
    "unloaded": {"commands": 3, "preprocessors": 1},
    "loaded": {"commands": 4, "preprocessors": 1}
}
```

**注意事项：**
- 热重载仅支持通过 `@Plugins.on_command` 注册的插件
- 不支持 `@bot.on_command` 注册的命令
- 修改插件后调用 `reload_plugin()` 即可生效

## 权限控制

### 频道管理员权限

```python
@bot.on_command(
    command="管理",
    is_require_admin=True,
    admin_error_msg="此命令仅频道管理员可用"
)
async def admin_cmd(msg: Model.GuildMessage):
    await msg.reply("管理员命令执行")
```

**注意**：`is_require_admin` 仅在频道场景生效，群聊和单聊中不生效。

### 机器人管理员权限

机器人管理员是全局的超管，通过 `BotAdminManager` 管理：

```python
# 添加机器人管理员（支持多个参数）- 异步方法
await bot.bot_admin_manager.add_admin("user_id_1", "user_id_2")

# 批量设置管理员列表（合并式，与现有数据取并集）- 异步方法
await bot.bot_admin_manager.set_bot_admins(["user_id_1", "user_id_2", "user_id_3"])

# 移除管理员（支持多个参数）- 异步方法
await bot.bot_admin_manager.remove_admin("user_id_1")

# 检查是否为管理员 - 同步方法
if bot.bot_admin_manager.is_admin("user_id"):
    print("是机器人管理员")

# 获取所有管理员（返回列表）- 同步方法
admins = bot.bot_admin_manager.bot_admins

# 获取所有管理员（返回集合）- 同步方法
admin_set = bot.bot_admin_manager.get_all_admins()

# 清空所有管理员 - 异步方法
await bot.bot_admin_manager.clear_admins()

# 使用命令装饰器
@bot.on_command(
    command="超管命令",
    is_require_bot_admin=True,
    bot_admin_error_msg="此命令仅机器人管理员可用"
)
async def super_admin_cmd(msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage):
    await msg.reply("超管命令执行")
```

> **注意**: `add_admin()`, `set_bot_admins()`, `remove_admin()`, `clear_admins()` 都是异步方法，需要使用 `await` 调用。`is_admin()`, `bot_admins`, `get_all_admins()` 是同步方法。

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
| `CommandValidScenes.ALL` | `GuildMessage \| GroupMessage \| C2CMessage \| DirectMessage` | 四种场景都可能 |

### 多场景类型提示示例

```python
from typing import Union
from easybot import CommandValidScenes, Model

# 方式1：使用 Union（Python 3.9 及以下）
@bot.on_command(
    command="测试",
    valid_scenes=CommandValidScenes.GUILD | CommandValidScenes.GROUP,
)
async def test_cmd(msg: Model.GuildMessage | Model.GroupMessage):
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

## 外部资源

当需要更详细的 API 文档或模型字段时，请使用以下资源：

### Context7 文档查询

使用 Context7 查询最新的 SDK 文档：

```
Library ID: /SaucePlum/easybot
```

查询示例：
- "如何使用 wait_for 实现多轮对话"
- "MessageEmbed 的所有参数"
- "如何获取频道成员列表"

### 官方链接

| 资源 | 链接 |
|------|------|
| GitHub 仓库 | https://github.com/SaucePlum/easybot |
| 文档网站 | https://sauceplum.github.io/easybot/ |
| PyPI 包 | https://pypi.org/project/easybot-qq/ |

---

**注意：** 本技能基于 EasyBot SDK 最新版本，如遇 API 变更请参考官方文档或使用 Context7 查询。
