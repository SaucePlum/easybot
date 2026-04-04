# SDK 组件

本章介绍 EasyBot SDK 的核心组件，包括 Bot 主类、协议层、沙箱配置和事件装饰器系统。

---

## Bot 类

**模块**: `easybot.bot`
**导入**: `from easybot import Bot`

Bot 是整个 SDK 的核心入口，负责机器人生命周期管理、事件注册和组件协调。

### 构造函数

```python
Bot(
    app_id: str,                              # 必填: 机器人 AppID
    app_secret: str,                          # 必填: 机器人 AppSecret
    is_private: bool = False,                 # 是否私域机器人，默认公域
    is_sandbox: bool = False,                 # 是否沙箱模式
    sandbox: SandBox | None = None,           # 沙箱过滤配置
    protocol: Protocol | None = None,         # 连接协议，默认 WebSocket
    is_retry: int = 3,                        # API 重试次数，默认 3 次
    is_log_error: bool = True,                # 自动记录 API 错误日志
    no_permission_warning: bool = True,       # 权限不足警告，默认开启
    api_timeout: int = 20,                    # API 超时时间（秒），默认 20 秒
    is_debug: bool = False,                   # 调试模式
    auto_load_plugins: bool = False,          # 自动加载插件目录
    plugins_dir: str = "plugins",              # 插件目录路径
    plugins_recursive: bool = False,          # 递归扫描子目录
    bot_admins: list[str] | None = None,      # 机器人管理员列表
) -> Bot
```

**示例**:
```python
from easybot import Bot, Proto, SandBox

# 最简配置
bot = Bot(app_id="xxx", app_secret="xxx")

# 完整配置
bot = Bot(
    app_id="xxx",
    app_secret="xxx",
    is_private=False,
    is_sandbox=True,
    sandbox=SandBox(guilds=["guild_123"]),
    protocol=Proto.websocket(),
    is_debug=True,
)

# 管理员独立管理（支持持久化到 sdk_data/bot_admins.yaml）
bot.bot_admin_manager.bot_admins = ["user_id_001"]
```

### 生命周期方法

#### start() / start_async()

`start()` 是同步启动方法，内部调用 `asyncio.run(self.start_async())`：

```python
def start(self) -> None
async def start_async(self) -> None
```

执行流程：设置运行标志 → 启动会话管理器 → 运行协议连接。

#### stop() / stop_async()

`stop()` 仅设置停止标志；`stop_async()` 执行完整资源清理：

```python
def stop(self) -> None
async def stop_async(self) -> None
```

清理内容：触发关闭事件 → 关闭 HTTP 客户端 → 停止协议连接。

#### 异步上下文管理器

```python
async with bot:
    await bot.start_async()
    # ... 业务逻辑 ...
# 自动调用 stop_async()
```

### 属性访问器

| 属性 | 类型 | 说明 |
|------|------|------|
| `bot.bot_id` | `str \| None` | 机器人实际 ID（启动后获取） |
| `bot.api` | `API` | API 调用实例 |
| `bot.session` | `SessionManager` | 会话管理器 |
| `bot.bot_admin_manager` | `BotAdminManager` | 机器人管理员管理器 |
| `bot.protocol` | `Protocol` | 连接协议实例 |
| `bot.logger` | `Logger` | 日志记录器 |
| `bot.sandbox` | `SandBox \| None` | 沙箱配置 |

---

## Protocol 协议类

**模块**: `easybot.protocol`
**导入**: `from easybot import Proto`

Protocol 负责与 QQ 开放平台建立连接，支持三种协议模式。

### Proto 工厂方法

| 方法 | 返回类型 | 说明 |
|------|---------|------|
| `Proto.websocket()` | `WebSocketProtocol` | WebSocket 模式（SDK 主动连接） |
| `Proto.webhook(port, path)` | `WebhookProtocol` | Webhook 模式（平台回调） |
| `Proto.remote_webhook(url)` | `RemoteWebhookProtocol` | 远程 Webhook 模式 |

### WebSocketProtocol

```python
Proto.websocket(
    shard_no: int = 0,                           # 当前分片编号
    total_shard: int = 1,                        # 总分片数
    disable_reconnect_on_not_recv_msg: float = 1000,  # 断线重连时间（秒）
    connect_timeout: float = 30.0,                # 连接超时时间（秒）
)
```

### WebhookProtocol

```python
Proto.webhook(
    port: int,                                   # 必填: 本机端口
    path: str = "/",                             # 挂载路径
    path_to_ssl_cert: str | None = None,        # SSL 证书路径
    path_to_ssl_cert_key: str | None = None,    # SSL 证书密钥路径
)
```

### RemoteWebhookProtocol

```python
Proto.remote_webhook(
    url: str,                                    # 必填: 远程服务器地址
    connect_timeout: float = 15.0,              # 连接超时时间（秒）
    heartbeat_interval: float = 40.0,           # 心跳间隔（秒）
    no_msg_timeout: float = 180.0,              # 断线重连时间（秒）
)
```

---

## SandBox 沙箱类

**模块**: `easybot.sandbox`
**导入**: `from easybot import SandBox`

SandBox 用于限制或过滤消息接收范围。

### 构造函数

```python
SandBox(
    guilds: list[str] | None = None,            # 频道 ID 列表
    guild_users: list[str] | None = None,       # 频道私信用户 ID 列表
    groups: list[str] | None = None,             # 群 ID 列表
    q_users: list[str] | None = None,           # QQ 私信用户 ID 列表
    sandbox_fail_action: bool = True,           # 默认行为（无匹配时）
)
```

### 行为模式

| 模式 | 配置 | 行为 |
|------|------|------|
| **沙箱模式** | `Bot(is_sandbox=True)` | 只接收列表中的消息 |
| **过滤模式** | `Bot(is_sandbox=False)` | 过滤掉列表中的消息 |

### 检查方法

```python
sandbox.check_guild(guild_id: str, is_sandbox: bool) -> bool
sandbox.check_group(group_openid: str, is_sandbox: bool) -> bool
sandbox.check_user(user_id: str, is_sandbox: bool, is_qq: bool = False) -> bool
```

**示例**:
```python
from easybot import Bot, SandBox

# 沙箱模式：只接收指定频道的消息
bot = Bot(
    app_id="xxx",
    app_secret="xxx",
    is_sandbox=True,
    sandbox=SandBox(guilds=["123456789", "987654321"]),
)

# 过滤模式：过滤掉指定频道的消息
bot = Bot(
    app_id="xxx",
    app_secret="xxx",
    is_sandbox=False,
    sandbox=SandBox(guilds=["123456789"]),
)
```

---

## 事件注册装饰器

事件装饰器用于注册事件处理器，接收对应的 Model 对象作为参数。

### 消息类装饰器

| 装饰器 | 事件类型 | Intent | 说明 |
|--------|---------|--------|------|
| `@bot.on_guild_message` | `AT_MESSAGE_CREATE` | PUBLIC_GUILD_MESSAGES | 频道 @机器人消息（公域） |
| `@bot.on_guild_full_message` | `MESSAGE_CREATE` | GUILD_MESSAGES | 频道全量消息（**仅私域**） |
| `@bot.on_group_message` | `GROUP_AT_MESSAGE_CREATE` | GROUP_AND_C2C_EVENT | 群聊 @机器人消息 |
| `@bot.on_c2c_message` | `C2C_MESSAGE_CREATE` | GROUP_AND_C2C_EVENT | QQ 单聊消息 |
| `@bot.on_direct_message` | `DIRECT_MESSAGE_CREATE` | DIRECT_MESSAGE | 频道私信消息 |

**消息删除事件**:

| 装饰器 | 事件类型 | 说明 |
|--------|---------|------|
| `@bot.on_message_delete` | `MESSAGE_DELETE` | 消息删除（**仅私域**） |
| `@bot.on_public_message_delete` | `PUBLIC_MESSAGE_DELETE` | 公域消息删除 |
| `@bot.on_direct_message_delete` | `DIRECT_MESSAGE_DELETE` | 私信消息删除 |

**示例**:
```python
@bot.on_guild_message
async def handle_guild_message(msg: Model.GuildMessage):
    await msg.reply("收到消息！")
    await bot.api.send_guild_message(
        channel_id=msg.channel_id,
        content=f"收到：{msg.content}"
    )
```

### 频道/成员类装饰器

| 装饰器 | 事件类型 | 说明 |
|--------|---------|------|
| `@bot.on_guild_create` | `GUILD_CREATE` | 加入频道 |
| `@bot.on_guild_update` | `GUILD_UPDATE` | 频道信息更新 |
| `@bot.on_guild_delete` | `GUILD_DELETE` | 退出频道 |
| `@bot.on_channel_create` | `CHANNEL_CREATE` | 子频道创建 |
| `@bot.on_channel_update` | `CHANNEL_UPDATE` | 子频道更新 |
| `@bot.on_channel_delete` | `CHANNEL_DELETE` | 子频道删除 |
| `@bot.on_guild_member_add` | `GUILD_MEMBER_ADD` | 成员加入 |
| `@bot.on_guild_member_update` | `GUILD_MEMBER_UPDATE` | 成员信息变更 |
| `@bot.on_guild_member_remove` | `GUILD_MEMBER_REMOVE` | 成员退出 |

### 群聊/好友类装饰器

| 装饰器 | 事件类型 | 说明 |
|--------|---------|------|
| `@bot.on_group_add` | `GROUP_ADD_ROBOT` | 加入群聊 |
| `@bot.on_group_delete` | `GROUP_DEL_ROBOT` | 退出群聊 |
| `@bot.on_group_msg_reject` | `GROUP_MSG_REJECT` | 群消息被拒 |
| `@bot.on_group_msg_receive` | `GROUP_MSG_RECEIVE` | 群消息被接收 |
| `@bot.on_friend_add` | `FRIEND_ADD` | 添加好友 |
| `@bot.on_friend_delete` | `FRIEND_DEL` | 删除好友 |
| `@bot.on_c2c_msg_reject` | `C2C_MSG_REJECT` | 私聊被拒 |
| `@bot.on_c2c_msg_receive` | `C2C_MSG_RECEIVE` | 私聊被接收 |

### 论坛类装饰器

| 装饰器 | 事件类型 | 说明 |
|--------|---------|------|
| `@bot.on_forum_thread_create` | `FORUM_THREAD_CREATE` | 帖子创建（**仅私域**） |
| `@bot.on_forum_thread_update` | `FORUM_THREAD_UPDATE` | 帖子更新 |
| `@bot.on_forum_thread_delete` | `FORUM_THREAD_DELETE` | 帖子删除 |
| `@bot.on_forum_post_create` | `FORUM_POST_CREATE` | 评论创建 |
| `@bot.on_forum_post_delete` | `FORUM_POST_DELETE` | 评论删除 |
| `@bot.on_forum_reply_create` | `FORUM_REPLY_CREATE` | 回复创建 |
| `@bot.on_forum_reply_delete` | `FORUM_REPLY_DELETE` | 回复删除 |
| `@bot.on_forum_publish_audit_result` | `FORUM_PUBLISH_AUDIT_RESULT` | 帖子审核结果 |
| `@bot.on_open_forum_thread_create` | `OPEN_FORUM_THREAD_CREATE` | 开放论坛主题创建 |
| `@bot.on_open_forum_thread_update` | `OPEN_FORUM_THREAD_UPDATE` | 开放论坛主题更新 |
| `@bot.on_open_forum_thread_delete` | `OPEN_FORUM_THREAD_DELETE` | 开放论坛主题删除 |
| `@bot.on_open_forum_post_create` | `OPEN_FORUM_POST_CREATE` | 开放论坛帖子创建 |
| `@bot.on_open_forum_post_delete` | `OPEN_FORUM_POST_DELETE` | 开放论坛帖子删除 |
| `@bot.on_open_forum_reply_create` | `OPEN_FORUM_REPLY_CREATE` | 开放论坛回复创建 |
| `@bot.on_open_forum_reply_delete` | `OPEN_FORUM_REPLY_DELETE` | 开放论坛回复删除 |

### 音频/互动类装饰器

| 装饰器 | 事件类型 | 说明 |
|--------|---------|------|
| `@bot.on_audio_start` | `AUDIO_START` | 音频开始播放 |
| `@bot.on_audio_finish` | `AUDIO_FINISH` | 音频播放结束 |
| `@bot.on_audio_on_mic` | `AUDIO_ON_MIC` | 上麦事件 |
| `@bot.on_audio_off_mic` | `AUDIO_OFF_MIC` | 下麦事件 |
| `@bot.on_audio_or_live_channel_member_enter` | `AUDIO_OR_LIVE_CHANNEL_MEMBER_ENTER` | 进入音视频/直播频道 |
| `@bot.on_audio_or_live_channel_member_exit` | `AUDIO_OR_LIVE_CHANNEL_MEMBER_EXIT` | 离开音视频/直播频道 |
| `@bot.on_interaction` | `INTERACTION_CREATE` | 互动按钮回调 |
| `@bot.on_reaction_add` | `MESSAGE_REACTION_ADD` | 表情表态添加 |
| `@bot.on_reaction_remove` | `MESSAGE_REACTION_REMOVE` | 表情表态移除 |

### 审核类装饰器

| 装饰器 | 事件类型 | 说明 |
|--------|---------|------|
| `@bot.on_message_audit_pass` | `MESSAGE_AUDIT_PASS` | 消息审核通过 |
| `@bot.on_message_audit_reject` | `MESSAGE_AUDIT_REJECT` | 消息审核拒绝 |

---

## 批量订阅装饰器

SDK 提供三个批量订阅装饰器，用于一次性订阅多个事件：

| 装饰器 | 说明 | 适用场景 |
|--------|------|---------|
| `@bot.on_all_intent_events` | 订阅所有机器人事件 | 全量事件监控 |
| `@bot.on_default_public_events` | 订阅公域机器人默认事件 | 公域机器人 |
| `@bot.on_default_private_events` | 订阅私域机器人默认事件 | 私域机器人 |

**示例**:
```python
@bot.on_default_public_events
async def handle_all_events(event):
    """接收所有公域默认事件"""
    bot.logger.info(f"收到事件: {event.__class__.__name__}")
```

---

## 生命周期装饰器

生命周期装饰器用于注册机器人启动、关闭和定时任务。

### @bot.on_startup

在机器人启动完成后执行：

```python
@bot.on_startup
async def on_startup(event: StartupEvent):
    bot.logger.info("机器人已启动")
```

### @bot.on_shutdown

在机器人关闭时执行：

```python
@bot.on_shutdown
async def on_shutdown(event: ShutdownEvent):
    bot.logger.info("机器人正在关闭")
```

### @bot.on_timer(interval)

定期执行的定时任务：

```python
@bot.on_timer(interval=60.0)  # 每 60 秒执行一次
async def on_timer(event: TimerEvent):
    bot.logger.info(f"定时任务执行: 第 {event.tick_count} 次")
```

**参数说明**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `interval` | `float` | 间隔时间（秒） |

**TimerEvent 属性**:

| 属性 | 类型 | 说明 |
|------|------|------|
| `event.bot` | `Bot` | Bot 实例 |
| `event.timestamp` | `float` | 触发时间戳 |
| `event.tick_count` | `int` | 第几次触发（从1开始） |

**示例 — 定期数据统计**:
```python
@bot.on_timer(interval=3600)
async def hourly_report(event: TimerEvent):
    """每小时发送数据报告"""
    await bot.api.send_guild_message(
        channel_id="channel_id",
        content=f"📊 整点报告 | 第 {event.tick_count} 次执行"
    )
```

---

## reply() 快速回复

所有消息事件模型（如 `GuildMessage`、`GroupMessage`、`DirectMessage` 等）都支持 `.reply()` 方法，可以快速回复消息，无需手动调用 API。

### 方法签名

```python
async def reply(
    self,
    content: "str | Message | MessageEmbed | MessageArk23 | MessageArk24 | MessageArk37 | MessageMarkdown",
    reference: bool = False,
)
```

### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `content` | `str \| MessagesModel` | — | 回复内容，支持文本或任意消息构建器 |
| `reference` | `bool` | `False` | 是否引用原消息 |

### 使用示例

```python
# 文本回复
await msg.reply("收到！")

# Embed 消息回复
await msg.reply(MessagesModel.MessageEmbed(title="标题", content=["内容"]))

# 引用回复
await msg.reply("回复你", reference=True)

# Markdown 回复
await msg.reply(MessagesModel.MessageMarkdown(content="# 标题\n\n内容"))
```

### 支持的事件模型

`reply()` 方法在以下事件模型中可用：

| 模型 | 事件 | 回复 API |
|------|------|---------|
| `GuildMessage` | 频道消息 | `send_guild_message` |
| `GroupMessage` | 群聊消息 | `send_group_message` |
| `C2CMessage` | 单聊消息 | `send_c2c_message` |
| `DirectMessage` | 频道私信 | `send_direct_message` |
| `GroupEvent` | 群聊事件 | 被动消息 |
| `FriendEvent` | 好友事件 | 被动消息 |
| `Interaction` | 互动按钮 | 被动消息 |
| `AudioAction` | 音频事件 | 被动消息 |
| `LiveChannelMember` | 频道进出 | 被动消息 |
| `Thread` / `Post` / `Reply` | 论坛事件 | 被动消息 |
| `MessageDelete` / `MessageReaction` | 消息事件 | 被动消息 |

> **注意**: `reply()` 会自动选择正确的 API 端点和参数，无需用户关心底层实现。

---

## 下一步

- [API参考](./04_API参考.md) — 完整接口文档，消息发送、频道管理等
- [Messages Model](./05_Messages_Model.md) — 掌握各种消息类型的构建方法
- [Model 库](./06_Model库.md) — 了解接收事件时的数据模型定义
