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
| `Interaction` | 互动按钮 | 被动消息 |
| `AudioAction` | 音频事件 | 被动消息 |

> **注意**: `reply()` 会自动选择正确的 API 端点和参数，无需用户关心底层实现。

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
| `MessagesModel.Message` | 普通消息（可包含图片） |
| `MessagesModel.MessageEmbed` | Embed 消息 |
| `MessagesModel.MessageArk23/24/37` | Ark 模板消息 |
| `MessagesModel.MessageMarkdown` | Markdown 消息 |

### 1.3 被动消息参数

发送被动消息时，需要提供以下参数之一：

| 参数 | 说明 |
|------|------|
| `msg_id` | 要回复的消息 ID |
| `event_id` | 要回复的事件 ID |

---

## 二、消息发送 API

### 2.1 频道消息

#### 发送频道消息

```python
await bot.api.send_guild_message(
    channel_id: str,                          # 子频道 ID
    content: MessageContent | None = None,    # 消息内容
    image: str | None = None,                 # 图片 URL
    file_image: bytes | str | None = None,    # 图片数据
    msg_id: str | None = None,                # 要回复的消息 ID
    event_id: str | None = None,              # 要回复的事件 ID
) -> Model.GuildMessage
```

**使用示例**：

```python
# 文本消息
await bot.api.send_guild_message(channel_id, "Hello")

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
    content: MessageContent | None = None,    # 消息内容
    msg_id: str | None = None,                # 要回复的消息 ID
    event_id: str | None = None,              # 要回复的事件 ID
) -> Model.GuildMessage
```

### 2.2 群聊消息

#### 发送群聊消息

```python
await bot.api.send_group_message(
    group_openid: str,                        # 群 openid
    content: MessageContent | None = None,    # 消息内容
    event_id: str | None = None,              # 前置收到的事件 ID
    msg_id: str | None = None,                # 要回复的消息 ID
    msg_seq: int | None = None,               # 回复消息的序号
) -> Model.GroupSendMessageResponse
```

**注意**: 群聊消息必须有文本内容（content）。

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
    content: MessageContent | None = None,    # 消息内容
    event_id: str | None = None,              # 前置收到的事件 ID
    msg_id: str | None = None,                # 要回复的消息 ID
    msg_seq: int | None = None,               # 回复消息的序号
) -> Model.C2CSendMessageResponse
```

#### 撤回 QQ 单聊消息

```python
await bot.api.recall_c2c_message(
    openid: str,          # 用户 openid
    message_id: str,      # 消息 ID
) -> bool
```

### 2.4 频道私信

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
    content: MessageContent | None = None,    # 消息内容
    image: str | None = None,                 # 图片 URL
    file_image: bytes | str | None = None,    # 图片数据
    msg_id: str | None = None,                # 要回复的消息 ID
    event_id: str | None = None,              # 要回复的事件 ID
) -> Model.GuildMessage
```

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

---

## 九、表情表态 API

### 9.1 表情表态管理

#### 创建表情表态

```python
await bot.api.create_reaction(
    channel_id: str,    # 子频道 ID
    message_id: str,    # 消息 ID
    emoji: str,         # 表情 ID
) -> bool
```

#### 删除表情表态

```python
await bot.api.delete_reaction(
    channel_id: str,    # 子频道 ID
    message_id: str,    # 消息 ID
    emoji: str,         # 表情 ID
) -> bool
```

---

## 十、机器人信息 API

### 10.1 机器人信息

#### 获取机器人信息

```python
await bot.api.get_me() -> Model.User
```

---

## 十一、使用建议

### 11.1 错误处理

API 调用可能失败，建议使用 try-except 处理：

```python
from easybot.exceptions import APIError

try:
    await bot.api.send_guild_message(channel_id, "消息")
except APIError as e:
    bot.logger.error(f"发送消息失败: {e}")
```

### 11.2 批量操作

对于批量操作（如批量禁言），使用批量 API 而不是循环调用单个 API：

```python
# ✅ 推荐
await bot.api.mute_guild_members(guild_id, user_ids, mute_seconds=60)

# ❌ 不推荐
for user_id in user_ids:
    await bot.api.mute_guild_member(guild_id, user_id, mute_seconds=60)
```

---

## 十二、下一步

- [Messages Model](./05_Messages_Model.md) — 掌握各种消息类型的构建方法
- [插件与权限](./07_插件与权限.md) — 学习插件开发和命令注册
- [Session 会话管理器](./08_Session会话管理器.md) — 实现多轮对话交互
