# SDK 组件

本章介绍 EasyBot SDK 的核心组件，包括 Bot 主类、协议层、沙箱配置和事件装饰器系统。

---

## 一、Bot 主类

**模块**: `easybot.bot`  
**导入**: `from easybot import Bot`

Bot 是整个 SDK 的核心入口，负责机器人生命周期管理、事件注册和组件协调。

### 1.1 构造函数

```python
Bot(
    app_id: str,                              # 必填: 机器人 AppID
    app_secret: str,                          # 必填: 机器人 AppSecret
    is_private: bool = False,                 # 是否私域机器人
    is_sandbox: bool = False,                 # 是否沙箱模式
    sandbox: SandBox | None = None,           # 沙箱过滤配置
    protocol: Protocol | None = None,         # 连接协议
    is_retry: int = 3,                        # API 重试次数
    is_log_error: bool = True,                # 自动记录 API 错误日志
    no_permission_warning: bool = True,       # 权限不足警告
    api_timeout: int = 20,                    # API 超时时间（秒）
    is_debug: bool = False,                   # 调试模式
    auto_load_plugins: bool = False,          # 自动加载插件目录
    plugins_dir: str = "plugins",              # 插件目录路径
    plugins_recursive: bool = False,          # 递归扫描子目录
    max_concurrency: int = 64,                # 事件处理器/命令最大并发数
) -> Bot
```

### 1.2 基本使用

**最简配置**：

```python
from easybot import Bot

bot = Bot(app_id="xxx", app_secret="xxx")
```

**完整配置**：

```python
from easybot import Bot, Proto, SandBox

bot = Bot(
    app_id="xxx",
    app_secret="xxx",
    is_private=False,              # 公域机器人
    is_sandbox=True,               # 沙箱环境
    sandbox=SandBox(guilds=["guild_123"]),
    protocol=Proto.websocket(),
    is_debug=True,
    is_retry=5,
    api_timeout=30,
)
```

**管理员配置**：

```python
# 通过 bot_admin_manager 设置（支持持久化到 sdk_data/bot_admins.yaml）
# 注意：以下方法都是异步的，需要在异步上下文中使用
await bot.bot_admin_manager.set_bot_admins(["user_id_001", "user_id_002"])

# 或增量添加
await bot.bot_admin_manager.add_admin("user_id_003")
```

### 1.3 生命周期方法

#### start() / start_async()

启动机器人：

```python
# 同步启动（阻塞主线程）
bot.start()

# 异步启动（自行管理事件循环）
await bot.start_async()
```

执行流程：设置运行标志 → 初始化机器人管理员管理器 → 启动会话管理器 → 运行协议连接。

#### stop() / stop_async()

停止机器人：

```python
# 仅设置停止标志
bot.stop()

# 执行完整资源清理
await bot.stop_async()
```

清理内容：触发关闭事件 → 停止会话管理器后台任务 → 关闭 HTTP 客户端 → 停止协议连接。

#### 异步上下文管理器

自动管理资源：

```python
async with bot:
    await bot.start_async()
    # ... 业务逻辑 ...
# 自动调用 stop_async()
```

### 1.4 公共属性

Bot 同时提供公开实例属性和 `@property` 属性访问器：

| 属性 | 类型 | 说明 | 形式 |
|------|------|------|------|
| `bot.bot_id` | `str \| None` | 机器人实际 ID（启动后获取） | `@property` |
| `bot.api` | `API` | API 调用实例 | 公开实例属性 |
| `bot.session` | `SessionManager` | 会话管理器 | `@property` |
| `bot.bot_admin_manager` | `BotAdminManager` | 机器人管理员管理器 | `@property` |
| `bot.protocol` | `Protocol` | 连接协议实例 | 公开实例属性 |
| `bot.logger` | `Logger` | 日志记录器 | 公开实例属性 |
| `bot.sandbox` | `SandBox \| None` | 沙箱配置 | 公开实例属性 |

### 1.5 命令相关方法

| 方法 | 说明 |
|------|------|
| `before_command(valid_scenes=...)` | 注册命令预处理器，在所有命令检查前执行 |
| `on_command(...)` | 注册命令处理器，支持命令名、正则、权限、场景和启停控制 |

```python
@bot.before_command(valid_scenes=CommandValidScenes.ALL)
async def preprocessor(
    msg: Model.Message,
):
    bot.logger.info(f"收到消息: {msg.treated_msg}")

@bot.on_command(command=["help", "帮助"], valid_scenes=CommandValidScenes.ALL)
async def help_command(
    msg: Model.Message,
):
    await msg.reply("帮助信息")
```

### 1.6 插件管理方法

Bot 提供完整的插件与命令管理能力：

| 分类 | 方法 |
|------|------|
| 加载与热重载 | `load_plugins()`、`reload_plugin()`、`reload_all_plugins()`、`unload_plugin()` |
| 查询 | `get_loaded_plugins()`、`get_all_commands()`、`find_command()` |
| 启停控制 | `enable_command()`、`disable_command()`、`is_command_enabled()`、`remove_command()` |
| 插件明细 | `get_plugin_commands()`、`get_plugin_preprocessors()`、`clear_all_plugins()` |

---

## 二、Protocol 协议类

**模块**: `easybot.protocol`  
**导入**: `from easybot import Proto`  
**具体协议类**: `from easybot.protocol import Protocol, WebSocketProtocol, WebhookProtocol, RemoteWebhookProtocol`

Protocol 负责与 QQ 开放平台建立连接，支持三种协议模式。

### 2.1 协议选择指南

| 协议 | 适用场景 | 特点 |
|------|---------|------|
| **WebSocket** | 本地/服务器直连 | 默认模式，自动重连，支持分片 |
| **Webhook** | 需要公网 IP 或反向代理 | HTTP 推送模式，适合云函数部署 |
| **Remote Webhook** | 内网穿透 / 远程中转 | 通过中间服务器转发事件 |

### 2.2 WebSocket 模式

SDK 主动连接 QQ 平台的 WebSocket Gateway：

```python
from easybot import Bot, Proto

bot = Bot(
    app_id="xxx",
    app_secret="xxx",
    protocol=Proto.websocket(
        shard_no=0,                           # 当前分片编号（从0开始）
        total_shard=1,                        # 总分片数
        disable_reconnect_on_not_recv_msg=1000, # 无消息重连间隔/秒
        connect_timeout=30.0,                 # 连接超时/秒
    ),
)
```

### 2.3 Webhook 模式

SDK 启动 HTTP 服务端，QQ 平台主动推送事件：

```python
from easybot import Bot, Proto

bot = Bot(
    app_id="xxx",
    app_secret="xxx",
    protocol=Proto.webhook(
        port=8080,                        # 监听端口
        path="/",                         # Webhook 路径前缀
        path_to_ssl_cert=None,            # SSL 证书路径
        path_to_ssl_cert_key=None,        # SSL 证书密钥路径
    ),
)
```

### 2.4 Remote Webhook 模式

通过远程中转服务器连接：

```python
from easybot import Bot, Proto

bot = Bot(
    app_id="xxx",
    app_secret="xxx",
    protocol=Proto.remote_webhook(
        url="wss://your-server.com",      # 中转服务器地址
        connect_timeout=15.0,             # 连接超时
        heartbeat_interval=40.0,          # 心跳间隔
        no_msg_timeout=180.0,             # 无消息断线重连
    ),
)
```

### 2.5 公开协议类与常用属性

| 项目 | 说明 |
|------|------|
| `Protocol` | 协议基类，定义 `run()` / `stop()` 生命周期 |
| `WebSocketProtocol` | WebSocket 协议配置对象 |
| `WebhookProtocol` | Webhook 协议配置对象，常用属性：`webhook_path`、`ws_path` |
| `RemoteWebhookProtocol` | 远程 Webhook 协议配置对象，常用属性：`ws_url` |

```python
webhook_proto = Proto.webhook(port=8080, path="/bot")
print(webhook_proto.webhook_path)  # /bot
print(webhook_proto.ws_path)       # /bot/ws

remote_proto = Proto.remote_webhook(url="https://example.com")
print(remote_proto.ws_url)         # wss://example.com/ws
```

---

## 三、SandBox 沙箱类

**模块**: `easybot.sandbox`  
**导入**: `from easybot import SandBox`

SandBox 用于限制或过滤消息接收范围。

### 3.1 构造函数

```python
SandBox(
    guilds: list[str] | None = None,            # 频道 ID 列表
    guild_users: list[str] | None = None,       # 频道私信用户 ID 列表
    groups: list[str] | None = None,             # 群 ID 列表
    q_users: list[str] | None = None,           # QQ 私信用户 ID 列表
    sandbox_fail_action: bool = True,           # 默认行为（无匹配时）
)
```

### 3.2 行为模式

| 模式 | 配置 | 行为 |
|------|------|------|
| **沙箱模式** | `Bot(is_sandbox=True)` | 只接收列表中的消息 |
| **过滤模式** | `Bot(is_sandbox=False)` | 过滤掉列表中的消息 |

### 3.3 使用示例

**沙箱模式**：只接收指定频道的消息

```python
from easybot import Bot, SandBox

bot = Bot(
    app_id="xxx",
    app_secret="xxx",
    is_sandbox=True,
    sandbox=SandBox(guilds=["123456789", "987654321"]),
)
```

**过滤模式**：过滤掉指定频道的消息

```python
from easybot import Bot, SandBox

bot = Bot(
    app_id="xxx",
    app_secret="xxx",
    is_sandbox=False,
    sandbox=SandBox(guilds=["123456789"]),
)
```

### 3.4 检查方法

SandBox 还提供三个检查方法，用于手动判断目标是否通过沙箱规则：

```python
sandbox.check_guild("guild_id", is_sandbox=True)
sandbox.check_group("group_openid", is_sandbox=True)
sandbox.check_user("user_id", is_sandbox=True, is_qq=False)
```

---

## 四、事件装饰器

事件装饰器用于注册事件处理器，接收对应的 Model 对象作为参数。

### 4.1 消息类事件

#### 频道消息

| 装饰器 | 事件类型 | Callback 类型 | 说明 |
|--------|---------|--------------|------|
| `@bot.on_guild_message` | `AT_MESSAGE_CREATE` | `Model.GuildMessage` | 频道 @机器人消息（公域） |
| `@bot.on_guild_full_message` | `MESSAGE_CREATE` | `Model.GuildMessage` | 频道全量消息（**仅私域**） |

#### 群聊/单聊/私信

| 装饰器 | 事件类型 | Callback 类型 | 说明 |
|--------|---------|--------------|------|
| `@bot.on_group_message` | `GROUP_AT_MESSAGE_CREATE` | `Model.GroupMessage` | 群聊 @机器人消息 |
| `@bot.on_c2c_message` | `C2C_MESSAGE_CREATE` | `Model.C2CMessage` | QQ 单聊消息 |
| `@bot.on_direct_message` | `DIRECT_MESSAGE_CREATE` | `Model.DirectMessage` | 频道私信消息 |

#### 消息删除事件

| 装饰器 | 事件类型 | Callback 类型 | 说明 |
|--------|---------|--------------|------|
| `@bot.on_message_delete` | `MESSAGE_DELETE` | `Model.MessageDelete` | 消息删除（**仅私域**） |
| `@bot.on_public_message_delete` | `PUBLIC_MESSAGE_DELETE` | `Model.MessageDelete` | 公域消息删除 |
| `@bot.on_direct_message_delete` | `DIRECT_MESSAGE_DELETE` | `Model.MessageDelete` | 私信消息删除 |

**使用示例**：

```python
from easybot import Bot, Model

bot = Bot(app_id="...", app_secret="...")

@bot.on_guild_message
async def handle_guild(msg: Model.GuildMessage):
    await msg.reply("收到频道消息！")

@bot.on_group_message
async def handle_group(msg: Model.GroupMessage):
    await msg.reply("收到群聊消息！")

bot.start()
```

### 4.2 频道/成员事件

| 装饰器 | 事件类型 | Callback 类型 | 说明 |
|--------|---------|--------------|------|
| `@bot.on_guild_create` | `GUILD_CREATE` | `Model.Guild` | 加入频道 |
| `@bot.on_guild_update` | `GUILD_UPDATE` | `Model.Guild` | 频道信息更新 |
| `@bot.on_guild_delete` | `GUILD_DELETE` | `Model.Guild` | 退出频道 |
| `@bot.on_channel_create` | `CHANNEL_CREATE` | `Model.Channel` | 子频道创建 |
| `@bot.on_channel_update` | `CHANNEL_UPDATE` | `Model.Channel` | 子频道更新 |
| `@bot.on_channel_delete` | `CHANNEL_DELETE` | `Model.Channel` | 子频道删除 |
| `@bot.on_guild_member_add` | `GUILD_MEMBER_ADD` | `Model.MemberWithGuildID` | 成员加入 |
| `@bot.on_guild_member_update` | `GUILD_MEMBER_UPDATE` | `Model.MemberWithGuildID` | 成员信息变更 |
| `@bot.on_guild_member_remove` | `GUILD_MEMBER_REMOVE` | `Model.MemberWithGuildID` | 成员退出 |

### 4.3 群聊/好友事件

| 装饰器 | 事件类型 | Callback 类型 | 说明 |
|--------|---------|--------------|------|
| `@bot.on_group_add` | `GROUP_ADD_ROBOT` | `Model.GroupEvent` | 加入群聊 |
| `@bot.on_group_delete` | `GROUP_DEL_ROBOT` | `Model.GroupEvent` | 退出群聊 |
| `@bot.on_group_msg_reject` | `GROUP_MSG_REJECT` | `Model.GroupEvent` | 群消息被拒 |
| `@bot.on_group_msg_receive` | `GROUP_MSG_RECEIVE` | `Model.GroupEvent` | 群消息被接收 |
| `@bot.on_friend_add` | `FRIEND_ADD` | `Model.FriendEvent` | 添加好友 |
| `@bot.on_friend_delete` | `FRIEND_DEL` | `Model.FriendEvent` | 删除好友 |
| `@bot.on_c2c_msg_reject` | `C2C_MSG_REJECT` | `Model.FriendEvent` | 私聊被拒 |
| `@bot.on_c2c_msg_receive` | `C2C_MSG_RECEIVE` | `Model.FriendEvent` | 私聊被接收 |

### 4.4 论坛事件

| 装饰器 | 事件类型 | Callback 类型 | 说明 |
|--------|---------|--------------|------|
| `@bot.on_forum_thread_create` | `FORUM_THREAD_CREATE` | `Model.Thread` | 帖子创建（**仅私域**） |
| `@bot.on_forum_thread_update` | `FORUM_THREAD_UPDATE` | `Model.Thread` | 帖子更新 |
| `@bot.on_forum_thread_delete` | `FORUM_THREAD_DELETE` | `Model.Thread` | 帖子删除 |
| `@bot.on_forum_post_create` | `FORUM_POST_CREATE` | `Model.Post` | 评论创建 |
| `@bot.on_forum_post_delete` | `FORUM_POST_DELETE` | `Model.Post` | 评论删除 |
| `@bot.on_forum_reply_create` | `FORUM_REPLY_CREATE` | `Model.Reply` | 回复创建 |
| `@bot.on_forum_reply_delete` | `FORUM_REPLY_DELETE` | `Model.Reply` | 回复删除 |
| `@bot.on_forum_publish_audit_result` | `FORUM_PUBLISH_AUDIT_RESULT` | `Model.AuditResult` | 帖子审核结果 |

### 4.5 开放论坛事件

| 装饰器 | 事件类型 | Callback 类型 | 说明 |
|--------|---------|--------------|------|
| `@bot.on_open_forum_thread_create` | `OPEN_FORUM_THREAD_CREATE` | `Model.OpenForumEvent` | 开放论坛帖子创建 |
| `@bot.on_open_forum_thread_update` | `OPEN_FORUM_THREAD_UPDATE` | `Model.OpenForumEvent` | 开放论坛帖子更新 |
| `@bot.on_open_forum_thread_delete` | `OPEN_FORUM_THREAD_DELETE` | `Model.OpenForumEvent` | 开放论坛帖子删除 |
| `@bot.on_open_forum_post_create` | `OPEN_FORUM_POST_CREATE` | `Model.OpenForumEvent` | 开放论坛评论创建 |
| `@bot.on_open_forum_post_delete` | `OPEN_FORUM_POST_DELETE` | `Model.OpenForumEvent` | 开放论坛评论删除 |
| `@bot.on_open_forum_reply_create` | `OPEN_FORUM_REPLY_CREATE` | `Model.OpenForumEvent` | 开放论坛回复创建 |
| `@bot.on_open_forum_reply_delete` | `OPEN_FORUM_REPLY_DELETE` | `Model.OpenForumEvent` | 开放论坛回复删除 |

### 4.6 音频/互动事件

| 装饰器 | 事件类型 | Callback 类型 | 说明 |
|--------|---------|--------------|------|
| `@bot.on_audio_start` | `AUDIO_START` | `Model.AudioAction` | 音频开始播放 |
| `@bot.on_audio_finish` | `AUDIO_FINISH` | `Model.AudioAction` | 音频播放结束 |
| `@bot.on_audio_on_mic` | `AUDIO_ON_MIC` | `Model.AudioAction` | 上麦事件 |
| `@bot.on_audio_off_mic` | `AUDIO_OFF_MIC` | `Model.AudioAction` | 下麦事件 |
| `@bot.on_audio_or_live_channel_member_enter` | `AUDIO_OR_LIVE_CHANNEL_MEMBER_ENTER` | `Model.LiveChannelMember` | 进入音视频/直播频道 |
| `@bot.on_audio_or_live_channel_member_exit` | `AUDIO_OR_LIVE_CHANNEL_MEMBER_EXIT` | `Model.LiveChannelMember` | 离开音视频/直播频道 |
| `@bot.on_interaction` | `INTERACTION_CREATE` | `Model.Interaction` | 互动按钮回调 |
| `@bot.on_reaction_add` | `MESSAGE_REACTION_ADD` | `Model.MessageReaction` | 表情表态添加 |
| `@bot.on_reaction_remove` | `MESSAGE_REACTION_REMOVE` | `Model.MessageReaction` | 表情表态移除 |

### 4.7 审核事件

| 装饰器 | 事件类型 | Callback 类型 | 说明 |
|--------|---------|--------------|------|
| `@bot.on_message_audit_pass` | `MESSAGE_AUDIT_PASS` | `Model.MessageAudited` | 消息审核通过 |
| `@bot.on_message_audit_reject` | `MESSAGE_AUDIT_REJECT` | `Model.MessageAudited` | 消息审核拒绝 |

---

## 五、批量订阅装饰器

SDK 提供三个批量订阅装饰器，用于一次性订阅多个事件：

| 装饰器 | Callback 类型 | 说明 | 适用场景 |
|--------|--------------|------|---------|
| `@bot.on_all_intent_events` | `Model.BaseModel` | 订阅所有机器人事件 | 全量事件监控 |
| `@bot.on_default_public_events` | `Model.BaseModel` | 订阅公域机器人默认事件 | 公域机器人 |
| `@bot.on_default_private_events` | `Model.BaseModel` | 订阅私域机器人默认事件 | 私域机器人 |

**使用示例**：

```python
from easybot import Model

@bot.on_default_public_events
async def handle_all_events(event: Model.BaseModel) -> None:
    """接收所有公域默认事件"""
    bot.logger.info(f"收到事件: {event.__class__.__name__}")
```

---

## 六、生命周期装饰器

生命周期装饰器用于注册机器人启动、关闭和定时任务。

### 6.1 装饰器概览

| 装饰器 | Callback 类型 | 说明 |
|--------|--------------|------|
| `@bot.on_startup` | `Model.StartupEvent` | 机器人启动事件 |
| `@bot.on_shutdown` | `Model.ShutdownEvent` | 机器人关闭事件 |
| `@bot.on_timer(interval)` | `Model.TimerEvent` | 周期定时任务 |

### 6.2 启动事件

在机器人启动完成后执行：

```python
@bot.on_startup
async def on_startup(event: Model.StartupEvent):
    bot.logger.info("机器人已启动")
    me = await bot.api.get_me()
    bot.logger.info(f"机器人名称: {me.username}")
```

### 6.3 关闭事件

在机器人关闭时执行：

```python
@bot.on_shutdown
async def on_shutdown(event: Model.ShutdownEvent):
    bot.logger.info("机器人正在关闭")
```

### 6.4 定时任务

定期执行的定时任务：

```python
@bot.on_timer(interval=60.0)  # 每 60 秒执行一次
async def on_timer(event: Model.TimerEvent):
    bot.logger.info(f"定时任务执行: 第 {event.tick_count} 次")
```

**TimerEvent 属性**：

| 属性 | 类型 | 说明 |
|------|------|------|
| `event.bot` | `Bot` | Bot 实例 |
| `event.timestamp` | `float` | 触发时间戳 |
| `event.tick_count` | `int` | 第几次触发（从1开始） |

---

## 七、reply() 快速回复

所有消息事件模型都支持 `.reply()` 方法，可以快速回复消息，无需手动调用 API。

### 7.1 方法签名

```python
async def reply(
    self,
    content: str
    | MessagesModel.Message
    | MessagesModel.MessageEmbed
    | MessagesModel.MessageArk23
    | MessagesModel.MessageArk24
    | MessagesModel.MessageArk37
    | MessagesModel.MessageMarkdown
    | None = None,
    reference: bool = False,
    image: str | None = None,
    file_image: bytes | BinaryIO | str | None = None,
    media_file_info: str | None = None,
    msg_type: int | None = None,
    is_wakeup: bool = False,
    channel_id: str | None = None,
)
```

**参数说明**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `content` | `str \| MessagesModel.Message/MessageEmbed/MessageArk23/24/37/MessageMarkdown \| None` | — | 回复内容，支持文本、普通消息构建器或结构化消息构建器 |
| `reference` | `bool` | `False` | 是否引用原消息 |
| `image` | `str \| None` | `None` | 普通消息图片 URL，仅频道/频道私信支持 |
| `file_image` | `bytes \| BinaryIO \| str \| None` | `None` | 普通消息本地图片，仅频道/频道私信支持 |
| `media_file_info` | `str \| None` | `None` | 富媒体 file_info，仅群聊/QQ 单聊 v2 支持 |
| `msg_type` | `int \| None` | `None` | 群聊/QQ 单聊 v2 消息类型，默认自动推断 |
| `is_wakeup` | `bool` | `False` | 互动召回消息，仅 QQ 单聊 v2 支持 |
| `channel_id` | `str \| None` | `None` | 子频道 ID。仅频道类被动事件在缺少默认目标时需要显式传入 |

### 7.2 使用示例

```python
from easybot import Bot, Model, MessagesModel

bot = Bot(app_id="...", app_secret="...")

@bot.on_guild_message
async def handle(msg: Model.GuildMessage):
    # 文本回复
    await msg.reply("收到！")
    
    # Embed 消息回复
    await msg.reply(MessagesModel.MessageEmbed(title="标题", content=["内容"]))

    # 普通消息构建器回复
    await msg.reply(MessagesModel.Message(content="图片", image="https://example.com/image.png"))

    # 频道图片回复
    await msg.reply("这是一张图片", image="https://example.com/image.png")
    
    # 引用回复
    await msg.reply("回复你", reference=True)
    
    # Markdown 回复
    await msg.reply(MessagesModel.MessageMarkdown(content="# 标题\n\n内容"))

bot.start()
```

### 7.3 支持的事件模型

`reply()` 方法在以下事件模型中可用：

| 模型 | 事件 | 回复 API |
|------|------|---------|
| `GuildMessage` | 频道消息 | `send_guild_message` |
| `GroupMessage` | 群聊消息 | `send_group_message` |
| `C2CMessage` | 单聊消息 | `send_c2c_message` |
| `DirectMessage` | 频道私信 | `send_direct_message` |
| `MemberWithGuildID` | `GUILD_MEMBER_ADD / UPDATE / REMOVE` | 被动消息 |
| `MessageReaction` | `MESSAGE_REACTION_ADD / REMOVE` | 被动消息 |
| `Thread` | `FORUM_THREAD_CREATE / UPDATE / DELETE` | 被动消息 |
| `Post` | `FORUM_POST_CREATE / DELETE` | 被动消息 |
| `Reply` | `FORUM_REPLY_CREATE / DELETE` | 被动消息 |
| `GroupEvent` | `GROUP_ADD_ROBOT / GROUP_MSG_RECEIVE` | 被动消息 |
| `FriendEvent` | `FRIEND_ADD / C2C_MSG_RECEIVE` | 被动消息 |
| `Interaction` | 互动按钮 | 被动消息 |
| `AudioAction` | 音频事件 | 被动消息 |

> **注意**: `reply()` 会自动选择正确的 API 端点和参数，无需用户关心底层实现。
> `GUILD_MEMBER_*` 这类事件没有默认子频道目标，调用 `reply()` 时需要显式传入 `channel_id`。

### 7.4 通过 msg.api / bot.api 访问 API 实例

所有支持 `reply()` 的消息模型都提供了 `api` 属性，可以直接访问 `API` 实例：

- `msg.api`：在消息事件处理器中可用（`@bot.on_xxx`、`@bot.on_command`，以及插件方式的 `@Plugins.on_command` / `@Plugins.before_command` 等）
- `bot.api`：在任意“能拿到 bot 实例”的上下文中可用（例如你的主程序、生命周期事件 `@bot.on_startup` / `@bot.on_shutdown` / `@bot.on_timer`，或 `@bot.on_xxx` / `@bot.on_command` 等闭包内）。**在生命周期回调中必须使用 `bot.api`，因为此时没有消息模型**；在仅使用 `@Plugins.xxx` 的插件模块里通常拿不到 `bot` 变量，此时应优先使用 `msg.api`

```python
@bot.on_guild_message
async def handle(msg: Model.GuildMessage):
    # 主动发送消息到其他子频道
    await msg.api.send_guild_message(
        channel_id="其他子频道ID",
        content="主动消息"
    )

    # 创建论坛帖子
    await msg.api.create_thread(
        channel_id="论坛子频道ID",
        title="帖子标题",
        content="帖子内容"
    )

# 生命周期回调中必须使用 bot.api（此时没有 msg 对象）
@bot.on_startup
async def on_startup(event: Model.StartupEvent):
    await bot.api.send_c2c_message(openid="用户ID", content="机器人已上线")
```

> **注意**: `msg.api` 只能在支持回复的事件模型中使用。`bot.api` 在任意上下文中可用，两者等价。

### 7.5 Model 与 MessagesModel

SDK 还提供两个常用的公开命名空间组件：

| 组件 | 导入方式 | 说明 |
|------|----------|------|
| `Model` | `from easybot import Model` | 所有事件模型、数据模型和类型命名空间 |
| `MessagesModel` | `from easybot import MessagesModel` | 消息构建器命名空间，包含 `Message`、`MessageEmbed`、`MessageMarkdown` 等 |

---

## 八、Builders 构建器

**模块**: `easybot.builders`  
**导入**: `from easybot import Builders`

Builders 提供三个公开构建器：

| 构建器 | 说明 |
|--------|------|
| `Builders.ParagraphBuilder` | 构建论坛段落内容 |
| `Builders.ThreadContentBuilder` | 构建论坛帖子内容 |
| `Builders.TextChainBuilder` | 构建文本交互元素 |

### 8.1 论坛内容构建器

`ThreadContentBuilder` 用于构建整篇帖子内容，`ParagraphBuilder` 用于手动拼装单个段落：

```python
from easybot import Builders

content = (
    Builders.ThreadContentBuilder()
    .add_text_paragraph("第一段文字", bold=True)
    .add_image_paragraph("https://example.com/image.png")
    .build()
)
```

也可以单独构建段落后再组合：

```python
paragraph = (
    Builders.ParagraphBuilder()
    .add_text("正文内容", bold=True)
    .add_image("https://example.com/image.png")
    .build()
)
```

### 8.2 TextChainBuilder — 文本交互构建器

用于构建文本消息中的交互元素，如 @用户、指令操作、跳转子频道等。

### 8.3 快速示例

```python
from easybot import Bot, Builders, Model

bot = Bot(app_id="...", app_secret="...")

@bot.on_guild_message
async def handle(msg: Model.GuildMessage) -> None:
    # @用户
    await msg.reply(Builders.TextChainBuilder.at_user("123456789") + " 你好！")
    
    # 组合使用
    content = (
        Builders.TextChainBuilder.at_user(msg.author.id) +
        " 欢迎加入！\n" +
        Builders.TextChainBuilder.cmd_enter("/help") +
        " 查看帮助"
    )
    await msg.reply(content)

bot.start()
```

### 8.4 常用方法

| 方法 | 说明 | 支持场景 |
|------|------|---------|
| `at_user(user_id)` | @指定用户 | 群聊、文字子频道 |
| `at_everyone()` | @全体成员 | 仅文字子频道 |
| `cmd_enter(text)` | 回车指令（直接发送） | 仅 Markdown 消息 |
| `cmd_input(text, show, reference)` | 参数指令（插入输入框） | 仅 Markdown 消息 |
| `channel_link(channel_id)` | 跳转子频道 | 仅频道 |
| `emoji(emoji_id)` | 系统表情 | 仅频道 |

> **详细文档**: 完整的方法说明和示例请参考 [Messages Model — 文本交互构建器](./05_Messages_Model.md#九textchainbuilder--文本交互构建器)

---

## 九、下一步

- [API 参考](./04_API参考.md) — 完整接口文档，消息发送、频道管理等
- [Messages Model](./05_Messages_Model.md) — 掌握各种消息类型的构建方法
- [插件与权限](./07_插件与权限.md) — 学习插件开发和命令注册
