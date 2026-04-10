# API 参考

本章提供 EasyBot SDK 中 `API` 类的完整参考文档。API 类封装了所有与 QQ 开放平台的 HTTP 交互。

---

## 一、API 概述

**模块**: `easybot.api`  
**访问方式**: `bot.api`（通过 Bot 实例访问）

### 1.1 推荐使用 reply()

在事件处理器中，**强烈推荐使用 `msg.reply()` 方法**而不是直接调用 API。`reply()` 方法会自动处理消息 ID、事件 ID 等被动消息参数，让代码更简洁。

#### 为什么推荐 reply()

| 特性 | reply() | 直接调用 API |
|------|---------|-------------|
| **代码简洁性** | ✅ 一行代码完成回复 | ❌ 需要手动传递多个参数 |
| **自动参数处理** | ✅ 自动处理 msg_id/event_id | ❌ 需要手动指定 |
| **类型安全** | ✅ 自动选择正确的 API | ❌ 需要记住不同场景的 API |
| **可读性** | ✅ 语义清晰 | ❌ 需要理解 API 细节 |

#### reply() 方法签名

```python
async def reply(
    self,
    content: str | MessagesModel,
    reference: bool = False,
)
```

**参数说明**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `content` | `str \| MessagesModel` | — | 回复内容，支持文本或任意消息构建器 |
| `reference` | `bool` | `False` | 是否引用原消息 |

#### 使用示例

**文本回复**：

```python
@bot.on_guild_message
async def handle(msg: Model.GuildMessage):
    await msg.reply("收到！")
```

**Embed 消息回复**：

```python
@bot.on_guild_message
async def handle(msg: Model.GuildMessage):
    embed = MessagesModel.MessageEmbed(
        title="标题",
        content=["第一行", "第二行"],
    )
    await msg.reply(embed)
```

**引用回复**：

```python
@bot.on_guild_message
async def handle(msg: Model.GuildMessage):
    await msg.reply("回复你", reference=True)
```

**Markdown 回复**：

```python
@bot.on_guild_message
async def handle(msg: Model.GuildMessage):
    md = MessagesModel.MessageMarkdown(content="# 标题\n\n**粗体文字**")
    await msg.reply(md)
```

#### 支持的事件模型

`reply()` 方法在以下事件模型中可用：

| 模型 | 事件 | 底层 API |
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

#### 何时使用 API 方法

只有在以下场景才需要直接调用 API：

1. **主动发送消息**：向其他频道/群聊发送消息（不是回复）
2. **获取消息详情**：查询特定消息的内容
3. **撤回消息**：撤回已发送的消息
4. **修改消息**：修改已发送的 Markdown 消息

```python
# 主动发送消息到其他频道
await bot.api.send_guild_message(
    channel_id="其他频道ID",
    content="主动消息",
)

# 获取消息详情
msg_detail = await bot.api.get_guild_message(channel_id, message_id)

# 撤回消息
await bot.api.recall_guild_message(channel_id, message_id)
```

### 1.2 消息内容类型

API 方法中的 `content` 参数支持以下类型：

| 类型 | 说明 |
|------|------|
| `str` | 文本消息 |
| `MessagesModel.Message` | 普通消息构建器 |
| `MessagesModel.MessageEmbed` | Embed 消息 |
| `MessagesModel.MessageArk23/24/37` | Ark 模板消息 |
| `MessagesModel.MessageMarkdown` | Markdown 消息 |

补充说明：

- 普通消息既可直接平铺参数发送，也可显式使用 `MessagesModel.Message`
- 频道消息 / 频道私信使用 `image`、`file_image`
- 群聊 / QQ 单聊 v2 使用 `media_file_info`
- `is_wakeup` 为 QQ 单聊 v2 的接口级参数

### 1.3 被动消息参数

发送被动消息时，需要提供以下参数之一：

| 参数 | 说明 |
|------|------|
| `msg_id` | 要回复的消息 ID |
| `event_id` | 要回复的事件 ID |

### 1.4 引用回复

部分发送接口支持引用回复参数：

| 参数 | 说明 |
|------|------|
| `message_reference_id` | 引用的消息 ID |
| `ignore_message_reference_error` | 是否忽略引用消息错误 |

---

## 二、消息发送 API

### 2.1 频道消息

#### 发送频道消息

```python
await bot.api.send_guild_message(
    channel_id: str,                          # 子频道 ID
    content: str | MessagesModel.Message | MessagesModel.MessageEmbed | MessagesModel.MessageArk23 | MessagesModel.MessageArk24 | MessagesModel.MessageArk37 | MessagesModel.MessageMarkdown | None = None,  # 消息内容
    image: str | None = None,                 # 图片 URL
    file_image: bytes | BinaryIO | str | None = None,    # 图片数据
    msg_id: str | None = None,                # 要回复的消息 ID
    event_id: str | None = None,              # 要回复的事件 ID
    message_reference_id: str | None = None,  # 引用消息 ID
    ignore_message_reference_error: bool = False,  # 是否忽略引用错误
) -> Model.GuildMessage
```

**说明**：

- 支持 `image` 或 `file_image` 发送图片
- `file_image` 走 multipart/form-data 上传
- 支持 `message_reference_id` 引用回复
- 不支持 `media_file_info`

**使用示例**：

```python
# 文本消息
await bot.api.send_guild_message(channel_id, "Hello")

# 普通消息构建器
await bot.api.send_guild_message(
    channel_id,
    MessagesModel.Message(content="Hello", image="https://example.com/image.png"),
)

# Embed 消息
await bot.api.send_guild_message(
    channel_id,
    MessagesModel.MessageEmbed(title="标题", content=["内容"]),
)

# 被动消息（回复）
await bot.api.send_guild_message(
    channel_id,
    "回复内容",
    msg_id=msg.id,
)

# 引用回复
await bot.api.send_guild_message(
    channel_id,
    "回复内容",
    message_reference_id=msg.id,
)
```

#### 获取指定消息

```python
await bot.api.get_guild_message(
    channel_id: str,      # 子频道 ID
    message_id: str,      # 消息 ID
) -> Model.GuildMessage
```

#### 撤回频道消息

```python
await bot.api.recall_guild_message(
    channel_id: str,      # 子频道 ID
    message_id: str,      # 消息 ID
    hidetip: bool = False, # 是否隐藏提示小灰条
) -> bool
```

#### 修改频道消息（仅支持 Markdown）

```python
await bot.api.patch_guild_message(
    channel_id: str,                          # 子频道 ID
    patch_msg_id: str,                        # 需要修改的消息 ID
    content: str | MessagesModel.Message | MessagesModel.MessageEmbed | MessagesModel.MessageArk23 | MessagesModel.MessageArk24 | MessagesModel.MessageArk37 | MessagesModel.MessageMarkdown | None = None,    # 消息内容
    msg_id: str | None = None,                # 要回复的消息 ID
    event_id: str | None = None,              # 要回复的事件 ID
) -> Model.GuildMessage
```

### 2.2 群聊消息

#### 发送群聊消息

```python
await bot.api.send_group_message(
    group_openid: str,                        # 群 openid
    content: str | MessagesModel.Message | MessagesModel.MessageEmbed | MessagesModel.MessageArk23 | MessagesModel.MessageArk24 | MessagesModel.MessageArk37 | MessagesModel.MessageMarkdown | None = None,    # 消息内容
    media_file_info: str | None = None,       # 富媒体 file_info
    event_id: str | None = None,              # 前置收到的事件 ID
    msg_id: str | None = None,                # 要回复的消息 ID
    msg_type: int | None = None,              # 消息类型，默认自动推断
    msg_seq: int | None = None,               # 回复消息的序号
    message_reference_id: str | None = None,  # 引用消息 ID
    ignore_message_reference_error: bool = False,  # 是否忽略引用错误
) -> Model.GroupSendMessageResponse
```

**注意**: 群聊消息必须有文本内容（content）。

**说明**：

- 群聊走 v2 接口，SDK 会自动根据消息内容补充 `msg_type`
- 群聊不支持 `image` / `file_image`
- 群聊富媒体应先调用 `upload_media()`，再通过 `media_file_info` 发送
- 支持 `message_reference_id` 引用回复
- 普通消息路径下必须有文本内容；结构化消息对象沿用原有 payload

#### 撤回群聊消息

```python
await bot.api.recall_group_message(
    group_openid: str,    # 群 openid
    message_id: str,      # 消息 ID
) -> bool
```

### 2.3 QQ 单聊消息

#### 发送 QQ 单聊消息

```python
await bot.api.send_c2c_message(
    openid: str,                              # 用户 openid
    content: str | MessagesModel.Message | MessagesModel.MessageEmbed | MessagesModel.MessageArk23 | MessagesModel.MessageArk24 | MessagesModel.MessageArk37 | MessagesModel.MessageMarkdown | None = None,    # 消息内容
    media_file_info: str | None = None,       # 富媒体 file_info
    event_id: str | None = None,              # 前置收到的事件 ID
    msg_id: str | None = None,                # 要回复的消息 ID
    msg_type: int | None = None,              # 消息类型，默认自动推断
    msg_seq: int | None = None,               # 回复消息的序号
    is_wakeup: bool = False,                  # 是否发送互动召回消息
    message_reference_id: str | None = None,  # 引用消息 ID
    ignore_message_reference_error: bool = False,  # 是否忽略引用错误
) -> Model.C2CSendMessageResponse
```

**说明**：

- QQ 单聊走 v2 接口，SDK 会自动根据消息内容补充 `msg_type`
- QQ 单聊不支持 `image` / `file_image`
- QQ 单聊富媒体应先调用 `upload_media()`，再通过 `media_file_info` 发送
- 支持 `message_reference_id` 引用回复
- `is_wakeup` 仅适用于 QQ 单聊 v2，且与 `msg_id`、`event_id` 互斥

#### 撤回 QQ 单聊消息

```python
await bot.api.recall_c2c_message(
    openid: str,          # 用户 openid
    message_id: str,      # 消息 ID
) -> bool
```

#### 发送流式消息（AI 对话场景）

```python
await bot.api.send_c2c_stream_message(
    openid: str,                           # 用户 openid
    content_raw: str,                      # Markdown 内容
    event_id: str,                         # 事件 ID
    msg_id: str,                           # 原始消息 ID
    msg_seq: int,                          # 递增序号
    index: int,                            # 会话内发送索引
    input_mode: str = "replace",           # 输入模式
    input_state: int = 1,                  # 输入状态，1=生成中，10=结束
    content_type: str = "markdown",        # 内容类型
    stream_msg_id: str | None = None,      # 流式消息 ID
) -> Model.StreamMessageResponse
```

### 2.4 群聊与 QQ 单聊富媒体上传

#### 上传富媒体文件

```python
await bot.api.upload_media(
    file_type: int,                      # 媒体类型（1 图片、2 视频、3 语音、4 文件）
    url: str | None = None,              # 媒体资源 URL
    file_data: bytes | str | None = None, # 文件数据或本地文件路径
    srv_send_msg: bool = False,          # 是否直接发送消息到目标端
    user_openid: str | None = None,      # 用户 openid
    group_openid: str | None = None,     # 群 openid
    file_name: str | None = None,        # 文件名（含扩展名），**file_type=4 时必填**
) -> Model.FileInfo
```

**说明**：

- 该接口用于群聊与 QQ 单聊 v2 的富媒体发送前置上传
- 上传成功后，将返回的 `file_info` 传入 `media_file_info`
- 不能替代频道消息里的 `image` / `file_image`
- 当 `file_type=4`（文件类型）时，**必须提供 `file_name` 参数**且需包含扩展名

### 2.5 频道私信

#### 创建私信会话

```python
await bot.api.create_dms(
    recipient_id: str,        # 接收者 ID
    source_guild_id: str,     # 源频道 ID
) -> Model.DMS
```

#### 发送频道私信消息

```python
await bot.api.send_direct_message(
    guild_id: str,                            # 私信频道 ID
    content: str | MessagesModel.Message | MessagesModel.MessageEmbed | MessagesModel.MessageArk23 | MessagesModel.MessageArk24 | MessagesModel.MessageArk37 | MessagesModel.MessageMarkdown | None = None,    # 消息内容
    image: str | None = None,                 # 图片 URL
    file_image: bytes | BinaryIO | str | None = None,    # 图片数据
    msg_id: str | None = None,                # 要回复的消息 ID
    event_id: str | None = None,              # 要回复的事件 ID
    message_reference_id: str | None = None,  # 引用消息 ID
    ignore_message_reference_error: bool = False,  # 是否忽略引用错误
) -> Model.GuildMessage
```

**说明**：

- 支持 `image` 或 `file_image` 发送图片
- `file_image` 走 multipart/form-data 上传
- 支持 `message_reference_id` 引用回复
- 不支持 `media_file_info`

#### 撤回频道私信消息

```python
await bot.api.recall_direct_message(
    guild_id: str,          # 私信频道 ID
    message_id: str,        # 消息 ID
    hidetip: bool = False,  # 是否隐藏提示小灰条
) -> bool
```

---

## 三、频道管理 API

### 3.1 频道信息

#### 获取频道详情

```python
await bot.api.get_guild(guild_id: str) -> Model.Guild
```

#### 获取机器人所在频道列表

```python
await bot.api.get_guild_list(
    before: str | None = None,   # 读此 guild id 之前的数据
    after: str | None = None,    # 读此 guild id 之后的数据
    limit: int = 100,            # 每次拉取数量，默认 100，最大 100
) -> list[Model.Guild]
```

#### 获取频道消息频率设置

```python
await bot.api.get_guild_message_setting(
    guild_id: str,    # 频道 ID
) -> Model.MessageSetting
```

### 3.2 子频道管理

#### 获取频道子频道列表

```python
await bot.api.get_guild_channels(guild_id: str) -> list[Model.Channel]
```

#### 获取子频道详情

```python
await bot.api.get_channel(channel_id: str) -> Model.Channel
```

#### 创建子频道

```python
await bot.api.create_channel(
    guild_id: str,                        # 频道 ID
    name: str,                            # 子频道名称
    channel_type: int,                    # 子频道类型
    position: int,                        # 排序值
    parent_id: str | None = None,         # 所属分组 ID
    sub_type: int = 0,                    # 子频道子类型
    private_type: int = 0,                # 子频道私密类型
    private_user_ids: list[str] | None = None,  # 子频道私密成员 ID 列表
    speak_permission: int = 0,            # 子频道发言权限
    application_id: str | None = None,    # 应用类型子频道 AppID
) -> Model.Channel
```

#### 修改子频道

```python
await bot.api.update_channel(
    channel_id: str,                  # 子频道 ID
    name: str | None = None,          # 子频道名称
    position: int | None = None,      # 排序值
    parent_id: str | None = None,     # 所属分组 ID
    private_type: int | None = None,  # 子频道私密类型
    speak_permission: int | None = None,  # 子频道发言权限
) -> Model.Channel
```

#### 删除子频道

```python
await bot.api.delete_channel(channel_id: str) -> bool
```

---

## 四、成员管理 API

### 4.1 成员信息

#### 获取频道成员列表

```python
await bot.api.get_guild_members(
    guild_id: str,        # 频道 ID
    after: str = "0",     # 上一次回包中最后一个 member 的 user id
    limit: int = 100,     # 分页大小，默认 100，最大 1000
) -> list[Model.Member]
```

#### 获取频道成员详情

```python
await bot.api.get_guild_member(
    guild_id: str,    # 频道 ID
    user_id: str,     # 用户 ID
) -> Model.Member
```

#### 删除频道成员

```python
await bot.api.delete_guild_member(
    guild_id: str,                    # 频道 ID
    user_id: str,                     # 用户 ID
    add_blacklist: bool = False,      # 是否同时添加到黑名单
    delete_history_msg_days: int = 0, # 撤回消息天数（3, 7, 15, 30, -1 全部）
) -> bool
```

### 4.2 在线成员

#### 获取子频道在线成员数

```python
await bot.api.get_channel_online_nums(channel_id: str) -> Model.OnlineNumsResponse
```

---

## 五、身份组 API

### 5.1 身份组管理

#### 获取频道身份组列表

```python
await bot.api.get_guild_roles(guild_id: str) -> Model.GuildRolesResponse
```

#### 创建频道身份组

```python
await bot.api.create_guild_role(
    guild_id: str,            # 频道 ID
    name: str = "新的身份组", # 身份组名称
    color: int = 0,           # 颜色值
    hoist: int = 0,           # 是否在成员列表中单独展示
) -> Model.CreateRoleResponse
```

#### 修改频道身份组

```python
await bot.api.update_guild_role(
    guild_id: str,            # 频道 ID
    role_id: str,             # 身份组 ID
    name: str | None = None,  # 身份组名称
    color: int | None = None, # 颜色值
    hoist: int | None = None, # 是否在成员列表中单独展示
) -> Model.CreateRoleResponse
```

#### 删除频道身份组

```python
await bot.api.delete_guild_role(
    guild_id: str,    # 频道 ID
    role_id: str,     # 身份组 ID
) -> bool
```

### 5.2 身份组成员

#### 添加成员到身份组

```python
await bot.api.add_guild_member_role(
    guild_id: str,                  # 频道 ID
    user_id: str,                   # 用户 ID
    role_id: str,                   # 身份组 ID
    channel_id: str | None = None,  # 子频道 ID（子频道管理员时需要）
) -> bool
```

#### 从身份组移除成员

```python
await bot.api.remove_guild_member_role(
    guild_id: str,                  # 频道 ID
    user_id: str,                   # 用户 ID
    role_id: str,                   # 身份组 ID
    channel_id: str | None = None,  # 子频道 ID（子频道管理员时需要）
) -> bool
```

#### 获取频道身份组成员列表

```python
await bot.api.get_guild_role_members(
    guild_id: str,          # 频道 ID
    role_id: str,           # 身份组 ID
    start_index: str = "0", # 分页起始位置
    limit: int = 20,        # 分页大小
) -> Model.RoleMembersResponse
```

---

## 六、权限管理 API

### 6.1 禁言管理

#### 频道全员禁言

```python
await bot.api.mute_guild(
    guild_id: str,                      # 频道 ID
    mute_seconds: int | None = None,    # 禁言秒数
    mute_end_timestamp: int | None = None,  # 禁言结束时间戳
) -> bool
```

#### 频道指定成员禁言

```python
await bot.api.mute_guild_member(
    guild_id: str,                      # 频道 ID
    user_id: str,                       # 用户 ID
    mute_seconds: int | None = None,    # 禁言秒数
    mute_end_timestamp: int | None = None,  # 禁言结束时间戳
) -> bool
```

#### 频道批量成员禁言

```python
await bot.api.mute_guild_members(
    guild_id: str,                      # 频道 ID
    user_ids: list[str],                # 用户 ID 列表
    mute_seconds: int | None = None,    # 禁言秒数
    mute_end_timestamp: int | None = None,  # 禁言结束时间戳
) -> Model.MuteBatchResponse
```

#### 取消频道全员禁言

```python
await bot.api.cancel_mute_all(guild_id: str) -> bool
```

#### 取消频道批量成员禁言

```python
await bot.api.cancel_mute_multi_member(
    guild_id: str,        # 频道 ID
    user_ids: list[str],  # 用户 ID 列表
) -> Model.MuteBatchResponse
```

### 6.2 子频道权限

#### 获取子频道用户权限

```python
await bot.api.get_channel_user_permissions(
    channel_id: str,  # 子频道 ID
    user_id: str,     # 用户 ID
) -> Model.ChannelPermissions
```

#### 获取子频道身份组权限

```python
await bot.api.get_channel_role_permissions(
    channel_id: str,  # 子频道 ID
    role_id: str,     # 身份组 ID
) -> Model.ChannelPermissions
```

#### 修改子频道用户权限

```python
await bot.api.update_channel_user_permissions(
    channel_id: str,          # 子频道 ID
    user_id: str,             # 用户 ID
    add: str | None = None,   # 赋予的权限
    remove: str | None = None, # 删除的权限
) -> bool
```

#### 修改子频道身份组权限

```python
await bot.api.update_channel_role_permissions(
    channel_id: str,          # 子频道 ID
    role_id: str,             # 身份组 ID
    add: str | None = None,   # 赋予的权限
    remove: str | None = None, # 删除的权限
) -> bool
```

### 6.3 API 权限

#### 获取机器人在频道可用权限列表

```python
await bot.api.get_guild_api_permissions(
    guild_id: str,    # 频道 ID
) -> Model.APIPermissionListResponse
```

#### 发送机器人在频道接口权限的授权链接

```python
await bot.api.demand_guild_api_permission(
    guild_id: str,      # 频道 ID
    channel_id: str,    # 授权链接发送的子频道 ID
    api_path: str,      # API 接口名
    api_method: str,    # 请求方法
    desc: str,          # 功能描述
) -> Model.APIPermissionDemand
```

---

## 七、日程 API

### 7.1 日程查询

#### 获取频道日程列表

```python
await bot.api.get_schedules(
    channel_id: str,              # 子频道 ID
    since: str | None = None,     # 起始时间戳（ms）
) -> list[Model.Schedule]
```

#### 获取日程详情

```python
await bot.api.get_schedule(
    channel_id: str,    # 子频道 ID
    schedule_id: str,   # 日程 ID
) -> Model.Schedule
```

### 7.2 日程管理

#### 创建日程

```python
await bot.api.create_schedule(
    channel_id: str,                        # 子频道 ID
    name: str,                              # 日程名称
    start_timestamp: str,                   # 开始时间戳
    end_timestamp: str,                     # 结束时间戳
    jump_channel_id: str | None = None,     # 跳转频道 ID
    remind_type: str = "0",                 # 提醒类型
    description: str | None = None,         # 日程描述
) -> Model.Schedule
```

#### 修改日程

```python
await bot.api.update_schedule(
    channel_id: str,                        # 子频道 ID
    schedule_id: str,                       # 日程 ID
    name: str | None = None,                # 日程名称
    start_timestamp: str | None = None,     # 开始时间戳
    end_timestamp: str | None = None,       # 结束时间戳
    jump_channel_id: str | None = None,     # 跳转频道 ID
    remind_type: str | None = None,         # 提醒类型
    description: str | None = None,         # 日程描述
) -> Model.Schedule
```

#### 删除日程

```python
await bot.api.delete_schedule(
    channel_id: str,    # 子频道 ID
    schedule_id: str,   # 日程 ID
) -> bool
```

---

## 八、音频 API

### 8.1 音频控制

#### 音频控制

```python
await bot.api.audio_control(
    channel_id: str,                # 子频道 ID
    audio_url: str | None = None,   # 音频 URL
    text: str | None = None,        # 状态文本
    status: int = 0,                # 状态码
) -> bool
```

#### 机器人上麦

```python
await bot.api.mic_up(channel_id: str) -> bool
```

#### 机器人下麦

```python
await bot.api.mic_down(channel_id: str) -> bool
```

---

## 九、表情表态 API

### 9.1 表情表态管理

#### 获取表情表态用户列表

```python
await bot.api.get_reaction_users(
    channel_id: str,          # 子频道 ID
    message_id: str,          # 消息 ID
    emoji_type: int,          # 表情类型
    emoji_id: str,            # 表情 ID
    cookie: str | None = None, # 分页 cookie
    limit: int = 20,          # 每页数量
) -> Model.ReactionUsers
```

#### 创建表情表态

```python
await bot.api.create_reaction(
    channel_id: str,    # 子频道 ID
    message_id: str,    # 消息 ID
    emoji_type: int,    # 表情类型（1 系统表情，2 emoji表情）
    emoji_id: str,      # 表情 ID
) -> bool
```

#### 删除表情表态

```python
await bot.api.delete_reaction(
    channel_id: str,    # 子频道 ID
    message_id: str,    # 消息 ID
    emoji_type: int,    # 表情类型（1 系统表情，2 emoji表情）
    emoji_id: str,      # 表情 ID
) -> bool
```

---

## 十、机器人信息 API

### 10.1 机器人信息

#### 获取机器人信息

```python
await bot.api.get_me() -> Model.Author
```

---

## 十一、公告与精华 API

### 11.1 公告管理

#### 创建频道公告

```python
await bot.api.create_announces(
    guild_id: str,                         # 频道 ID
    message_id: str | None = None,         # 消息 ID
    channel_id: str | None = None,         # 子频道 ID
    announces_type: int = 0,               # 公告类别
    recommend_channels: list[dict] | None = None,  # 推荐子频道列表
) -> Model.Announces
```

#### 删除频道公告

```python
await bot.api.delete_announces(
    guild_id: str,             # 频道 ID
    message_id: str = "all",   # 消息 ID，传 "all" 删除全部
) -> bool
```

### 11.2 精华消息

#### 获取精华消息

```python
await bot.api.get_pins(channel_id: str) -> Model.PinsMessage
```

#### 添加精华消息

```python
await bot.api.add_pin(
    channel_id: str,    # 子频道 ID
    message_id: str,    # 消息 ID
) -> Model.PinsMessage
```

#### 删除精华消息

```python
await bot.api.delete_pin(
    channel_id: str,    # 子频道 ID
    message_id: str,    # 消息 ID
) -> bool
```

---

## 十二、论坛 API

### 12.1 帖子查询

#### 获取帖子详情

```python
await bot.api.get_thread(
    channel_id: str,    # 子频道 ID
    thread_id: str,     # 帖子 ID
) -> Model.ThreadDetail
```

#### 获取帖子列表

```python
await bot.api.get_threads(
    channel_id: str,    # 子频道 ID（须为论坛子频道 type=10007）
) -> Model.ThreadListResult
```

### 12.2 帖子管理

#### 发表帖子

```python
await bot.api.create_thread(
    channel_id: str,                           # 子频道 ID
    title: str,                               # 帖子标题
    content: str | Model.ThreadContent,       # 帖子内容
    format: int | None = None,                # 帖子格式
) -> Model.CreateThreadResponse
```

#### 删除帖子

```python
await bot.api.delete_thread(
    channel_id: str,    # 子频道 ID
    thread_id: str,     # 帖子 ID
) -> bool
```

#### 发表评论

```python
await bot.api.create_thread_comment(
    channel_id: str,                      # 子频道 ID
    thread_id: str,                       # 帖子 ID
    thread_author: str,                   # 帖子作者 ID
    content: str,                         # 评论内容
    thread_create_time: str | None = None, # 帖子创建时间
    image: str | None = None,             # 图片链接
) -> Model.CreateCommentResponse
```

---

## 十三、网关、互动与媒体 API

### 13.1 网关与分享链接

#### 获取通用 WSS 接入点

```python
await bot.api.get_gateway() -> Model.GatewayResponse
```

#### 获取带分片 WSS 接入点

```python
await bot.api.get_gateway_bot() -> Model.GatewayBotResponse
```

#### 获取机器人资料页分享链接

```python
await bot.api.generate_url_link(
    callback_data: str | None = None,    # 添加好友时回传的来源参数
) -> Model.UrlLinkResponse
```

### 13.2 互动事件

#### 回应互动按钮点击事件

```python
await bot.api.respond_interaction(
    interaction_id: str,    # 互动事件 ID
    code: int = 0,          # 回应码
) -> bool
```

---

## 十四、大文件分片上传 API

大文件分片上传支持上传超过 10MB 的文件，适用于视频、大文档等场景。

### 14.1 文件大小限制

| 文件类型 | 大小限制 | file_type |
|---------|---------|-----------|
| 图片 | 10MB | 1 |
| 视频 | 100MB | 2 |
| 语音 | 10MB | 3 |
| 文件 | 100MB | 4 |

### 14.2 一键上传（推荐）

最简单的上传方式，自动完成所有步骤：

```python
result = await bot.api.upload_large_file(
    file_path="./videos/large_video.mp4",  # 本地文件路径
    file_type=2,                            # 文件类型
    user_openid="user_xxx",                 # 单聊场景
    # group_openid="group_xxx",             # 群聊场景（二选一）
    concurrency=3,                          # 并发数（可选）
)

# 使用返回的 file_info 发送消息
await bot.api.send_c2c_message(
    openid="user_xxx",
    content="视频已上传",
    media_file_info=result.file_info,
)
```

**自动完成**：
- ✅ 计算文件哈希值（MD5、SHA1、md5_10m）
- ✅ 申请上传任务
- ✅ 并行上传所有分片
- ✅ 完成上传并获取 file_info

### 14.3 手动控制流程

需要显示进度或自定义上传逻辑时使用：

#### 步骤1：申请上传

```python
import hashlib

# 读取文件并计算哈希
with open("large_file.mp4", "rb") as f:
    file_data = f.read()
    file_md5 = hashlib.md5(file_data).hexdigest()
    file_sha1 = hashlib.sha1(file_data).hexdigest()
    md5_10m = (
        hashlib.md5(file_data[:10002432]).hexdigest()
        if len(file_data) >= 10002432
        else file_md5
    )

# 申请上传
prepare = await bot.api.upload_prepare(
    file_type=2,                    # 文件类型
    file_name="large_file.mp4",     # 文件名
    file_size=len(file_data),       # 文件大小
    md5=file_md5,                   # 完整 MD5
    sha1=file_sha1,                 # 完整 SHA1
    md5_10m=md5_10m,                # 前 10MB 的 MD5
    user_openid="user_xxx",         # 单聊场景
    # group_openid="group_xxx",     # 群聊场景（二选一）
)

# 获取上传任务信息
upload_id = prepare.upload_id
block_size = prepare.block_size
parts = prepare.parts
```

#### 步骤2：上传分片

```python
# 逐个上传分片
for part in prepare.parts:
    # 读取分片数据
    offset = (part.index - 1) * block_size
    chunk_data = file_data[offset:offset + block_size]
    
    # 上传分片（自动处理对象存储和通知）
    await bot.api.upload_part(
        presigned_url=part.presigned_url,  # 预签名 URL
        part_data=chunk_data,               # 分片数据
        upload_id=upload_id,                # 上传任务 ID
        part_index=part.index,              # 分片索引
        user_openid="user_xxx",             # 单聊场景
    )
    
    # 显示进度
    progress = int((part.index / len(parts)) * 100)
    print(f"上传进度: {progress}%")
```

#### 步骤3：完成上传

```python
# 完成上传
result = await bot.api.upload_complete(
    upload_id=upload_id,
    user_openid="user_xxx",
)

# 使用 file_info 发送消息
await bot.api.send_c2c_message(
    openid="user_xxx",
    content="文件已上传",
    media_file_info=result.file_info,
)
```

### 14.4 并发上传

提高上传速度，使用并发上传：

```python
import asyncio

# 使用信号量控制并发数
semaphore = asyncio.Semaphore(3)

async def upload_single_part(part):
    async with semaphore:
        offset = (part.index - 1) * prepare.block_size
        chunk_data = file_data[offset:offset + prepare.block_size]
        
        return await bot.api.upload_part(
            presigned_url=part.presigned_url,
            part_data=chunk_data,
            upload_id=prepare.upload_id,
            part_index=part.index,
            user_openid="user_xxx",
        )

# 并发上传所有分片
tasks = [upload_single_part(part) for part in prepare.parts]
await asyncio.gather(*tasks)
```

### 14.5 API 方法列表

| 方法 | 类型 | 说明 |
|------|------|------|
| `upload_large_file()` | 封装 | 一键上传大文件 |
| `upload_prepare()` | 官方 | 申请上传任务 |
| `upload_part()` | 封装 | 上传单个分片 |
| `upload_part_finish()` | 官方 | 完成分片通知 |
| `upload_complete()` | 官方 | 完成上传 |

### 14.6 注意事项

1. **文件名限制**：文件名不能包含敏感关键词（如 `url`、`http`、`www` 等）
2. **场景选择**：`user_openid` 和 `group_openid` 必须提供其中之一
3. **分片大小**：由平台返回，通常为 2MB
4. **有效期**：`file_info` 有有效期（`ttl` 秒），过期后需重新上传

---

## 十五、使用建议

### 15.1 错误处理

API 调用可能失败，建议使用 try-except 处理：

```python
from easybot.exceptions import APIError

try:
    await bot.api.send_guild_message(channel_id, "消息")
except APIError as e:
    bot.logger.error(f"发送消息失败: {e}")
```

### 15.2 批量操作

对于批量操作（如批量禁言），使用批量 API 而不是循环调用单个 API：

```python
# ✅ 推荐
await bot.api.mute_guild_members(guild_id, user_ids, mute_seconds=60)

# ❌ 不推荐
for user_id in user_ids:
    await bot.api.mute_guild_member(guild_id, user_id, mute_seconds=60)
```

---

## 十六、下一步

- [Messages Model](./05_Messages_Model.md) — 掌握各种消息类型的构建方法
- [插件与权限](./07_插件与权限.md) — 学习插件开发和命令注册
- [Session 会话管理器](./08_Session会话管理器.md) — 实现多轮对话交互
