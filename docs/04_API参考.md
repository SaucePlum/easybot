# API 参考

本章提供 EasyBot SDK 中 `API` 类的完整参考文档。API 类封装了所有与 QQ 开放平台的 HTTP 交互，包括消息发送、频道管理、成员管理等功能。

---

## API 类

**模块**: `easybot.api`
**导入**: `from easybot import API`（通常通过 `bot.api` 访问）

### 消息内容类型

API 方法中的 `content` 参数支持以下类型：

| 类型 | 说明 |
|------|------|
| `str` | 文本消息 |
| `MessagesModel.Message` | 普通消息（可包含图片） |
| `MessagesModel.MessageEmbed` | Embed 消息 |
| `MessagesModel.MessageArk23/24/37` | Ark 模板消息 |
| `MessagesModel.MessageMarkdown` | Markdown 消息 |

---

## 频道 API

### 获取频道详情

方法名：`get_guild`

```python
async def get_guild(self, guild_id: str) -> Model.Guild
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `guild_id` | `str` | 频道 ID |

**返回**: `Model.Guild`

---

### 获取机器人所在频道列表

方法名：`get_guild_list`

```python
async def get_guild_list(
    self,
    before: str | None = None,
    after: str | None = None,
    limit: int = 100,
) -> list[Model.Guild]
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `before` | `str \| None` | 读此 guild id 之前的数据 |
| `after` | `str \| None` | 读此 guild id 之后的数据 |
| `limit` | `int` | 每次拉取数量，默认 100，最大 100 |

**返回**: `list[Model.Guild]`

---

### 获取频道子频道列表

方法名：`get_guild_channels`

```python
async def get_guild_channels(self, guild_id: str) -> list[Model.Channel]
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `guild_id` | `str` | 频道 ID |

**返回**: `list[Model.Channel]`

---

### 获取子频道详情

方法名：`get_channel`

```python
async def get_channel(self, channel_id: str) -> Model.Channel
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `channel_id` | `str` | 子频道 ID |

**返回**: `Model.Channel`

---

### 创建子频道

方法名：`create_channel`

```python
async def create_channel(
    self,
    guild_id: str,
    name: str,
    channel_type: int,
    position: int,
    parent_id: str | None = None,
    sub_type: int = 0,
    private_type: int = 0,
    private_user_ids: list[str] | None = None,
    speak_permission: int = 0,
    application_id: str | None = None,
) -> Model.Channel
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `guild_id` | `str` | 频道 ID |
| `name` | `str` | 子频道名称 |
| `channel_type` | `int` | 子频道类型 |
| `position` | `int` | 排序值 |
| `parent_id` | `str \| None` | 所属分组 ID |
| `sub_type` | `int` | 子频道子类型 |
| `private_type` | `int` | 子频道私密类型 |
| `private_user_ids` | `list[str] \| None` | 子频道私密成员 ID 列表 |
| `speak_permission` | `int` | 子频道发言权限 |
| `application_id` | `str \| None` | 应用类型子频道 AppID |

**返回**: `Model.Channel`

---

### 修改子频道

方法名：`update_channel`

```python
async def update_channel(
    self,
    channel_id: str,
    name: str | None = None,
    position: int | None = None,
    parent_id: str | None = None,
    private_type: int | None = None,
    speak_permission: int | None = None,
) -> Model.Channel
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `channel_id` | `str` | 子频道 ID |
| `name` | `str \| None` | 子频道名称 |
| `position` | `int \| None` | 排序值 |
| `parent_id` | `str \| None` | 所属分组 ID |
| `private_type` | `int \| None` | 子频道私密类型 |
| `speak_permission` | `int \| None` | 子频道发言权限 |

**返回**: `Model.Channel`

---

### 删除子频道

方法名：`delete_channel`

```python
async def delete_channel(self, channel_id: str) -> bool
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `channel_id` | `str` | 子频道 ID |

**返回**: `bool`

---

## 消息 API

### 发送频道消息

方法名：`send_guild_message`

```python
async def send_guild_message(
    self,
    channel_id: str,
    content: MessageContent | None = None,
    image: str | None = None,
    file_image: bytes | str | None = None,
    msg_id: str | None = None,
    event_id: str | None = None,
) -> Model.GuildMessage
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `channel_id` | `str` | 子频道 ID |
| `content` | `MessageContent \| None` | 消息内容 |
| `image` | `str \| None` | 图片 URL（content 为文本时使用） |
| `file_image` | `bytes \| str \| None` | 图片数据（content 为文本时使用） |
| `msg_id` | `str \| None` | 要回复的消息 ID（被动消息） |
| `event_id` | `str \| None` | 要回复的事件 ID（被动消息） |

**返回**: `Model.GuildMessage`

**示例**:
```python
await api.send_guild_message(channel_id, "Hello")
await api.send_guild_message(channel_id, MessagesModel.MessageEmbed(title="标题"), msg_id=msg.id)
```

---

### 获取指定消息

方法名：`get_guild_message`

```python
async def get_guild_message(
    self,
    channel_id: str,
    message_id: str,
) -> Model.GuildMessage
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `channel_id` | `str` | 子频道 ID |
| `message_id` | `str` | 消息 ID |

**返回**: `Model.GuildMessage`

---

### 撤回频道消息

方法名：`recall_guild_message`

```python
async def recall_guild_message(
    self,
    channel_id: str,
    message_id: str,
    hidetip: bool = False,
) -> bool
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `channel_id` | `str` | 子频道 ID |
| `message_id` | `str` | 消息 ID |
| `hidetip` | `bool` | 是否隐藏提示小灰条 |

**返回**: `bool`

---

### 修改频道消息（仅支持 Markdown）

方法名：`patch_guild_message`

```python
async def patch_guild_message(
    self,
    channel_id: str,
    patch_msg_id: str,
    content: MessageContent | None = None,
    msg_id: str | None = None,
    event_id: str | None = None,
) -> Model.GuildMessage
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `channel_id` | `str` | 子频道 ID |
| `patch_msg_id` | `str` | 需要修改的消息 ID |
| `content` | `MessageContent \| None` | 消息内容（推荐使用 MessageMarkdown） |
| `msg_id` | `str \| None` | 要回复的消息 ID（被动消息） |
| `event_id` | `str \| None` | 要回复的事件 ID（被动消息） |

**返回**: `Model.GuildMessage`

---

## 群聊 API

### 发送群聊消息

方法名：`send_group_message`

```python
async def send_group_message(
    self,
    group_openid: str,
    content: MessageContent | None = None,
    event_id: str | None = None,
    msg_id: str | None = None,
    msg_seq: int | None = None,
) -> Model.GroupSendMessageResponse
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `group_openid` | `str` | 群 openid |
| `content` | `MessageContent \| None` | 消息内容 |
| `event_id` | `str \| None` | 前置收到的事件 ID（被动消息） |
| `msg_id` | `str \| None` | 要回复的消息 ID（被动消息） |
| `msg_seq` | `int \| None` | 回复消息的序号 |

**返回**: `Model.GroupSendMessageResponse`

**注意**: 群聊消息必须有文本内容（content）。

---

### 撤回群聊消息

方法名：`recall_group_message`

```python
async def recall_group_message(
    self,
    group_openid: str,
    message_id: str,
) -> bool
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `group_openid` | `str` | 群 openid |
| `message_id` | `str` | 消息 ID |

**返回**: `bool`

---

## 私信 API

### 创建私信会话

方法名：`create_dms`

```python
async def create_dms(
    self,
    recipient_id: str,
    source_guild_id: str,
) -> Model.DMS
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `recipient_id` | `str` | 接收者 ID |
| `source_guild_id` | `str` | 源频道 ID |

**返回**: `Model.DMS`

---

### 发送 QQ 单聊消息

方法名：`send_c2c_message`

```python
async def send_c2c_message(
    self,
    openid: str,
    content: MessageContent | None = None,
    event_id: str | None = None,
    msg_id: str | None = None,
    msg_seq: int | None = None,
) -> Model.C2CSendMessageResponse
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `openid` | `str` | 用户 openid |
| `content` | `MessageContent \| None` | 消息内容 |
| `event_id` | `str \| None` | 前置收到的事件 ID（被动消息） |
| `msg_id` | `str \| None` | 要回复的消息 ID（被动消息） |
| `msg_seq` | `int \| None` | 回复消息的序号 |

**返回**: `Model.C2CSendMessageResponse`

---

### 撤回 QQ 单聊消息

方法名：`recall_c2c_message`

```python
async def recall_c2c_message(
    self,
    openid: str,
    message_id: str,
) -> bool
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `openid` | `str` | 用户 openid |
| `message_id` | `str` | 消息 ID |

**返回**: `bool`

---

### 发送频道私信消息

方法名：`send_direct_message`

```python
async def send_direct_message(
    self,
    guild_id: str,
    content: MessageContent | None = None,
    image: str | None = None,
    file_image: bytes | str | None = None,
    msg_id: str | None = None,
    event_id: str | None = None,
) -> Model.GuildMessage
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `guild_id` | `str` | 私信频道 ID |
| `content` | `MessageContent \| None` | 消息内容 |
| `image` | `str \| None` | 图片 URL |
| `file_image` | `bytes \| str \| None` | 图片数据 |
| `msg_id` | `str \| None` | 要回复的消息 ID（被动消息） |
| `event_id` | `str \| None` | 要回复的事件 ID（被动消息） |

**返回**: `Model.GuildMessage`

---

### 撤回频道私信消息

方法名：`recall_direct_message`

```python
async def recall_direct_message(
    self,
    guild_id: str,
    message_id: str,
    hidetip: bool = False,
) -> bool
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `guild_id` | `str` | 私信频道 ID |
| `message_id` | `str` | 消息 ID |
| `hidetip` | `bool` | 是否隐藏提示小灰条 |

**返回**: `bool`

---

## 成员管理 API

### 获取频道成员列表

方法名：`get_guild_members`

```python
async def get_guild_members(
    self,
    guild_id: str,
    after: str = "0",
    limit: int = 100,
) -> list[Model.Member]
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `guild_id` | `str` | 频道 ID |
| `after` | `str` | 上一次回包中最后一个 member 的 user id |
| `limit` | `int` | 分页大小，默认 100，最大 1000 |

**返回**: `list[Model.Member]`

---

### 获取频道成员详情

方法名：`get_guild_member`

```python
async def get_guild_member(
    self,
    guild_id: str,
    user_id: str,
) -> Model.Member
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `guild_id` | `str` | 频道 ID |
| `user_id` | `str` | 用户 ID |

**返回**: `Model.Member`

---

### 删除频道成员

方法名：`delete_guild_member`

```python
async def delete_guild_member(
    self,
    guild_id: str,
    user_id: str,
    add_blacklist: bool = False,
    delete_history_msg_days: int = 0,
) -> bool
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `guild_id` | `str` | 频道 ID |
| `user_id` | `str` | 用户 ID |
| `add_blacklist` | `bool` | 是否同时添加到黑名单 |
| `delete_history_msg_days` | `int` | 撤回消息天数（3, 7, 15, 30, -1 全部） |

**返回**: `bool`

---

### 获取子频道在线成员数

方法名：`get_channel_online_nums`

```python
async def get_channel_online_nums(self, channel_id: str) -> Model.OnlineNumsResponse
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `channel_id` | `str` | 子频道 ID |

**返回**: `Model.OnlineNumsResponse`

---

## 身份组 API

### 获取频道身份组列表

方法名：`get_guild_roles`

```python
async def get_guild_roles(self, guild_id: str) -> Model.GuildRolesResponse
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `guild_id` | `str` | 频道 ID |

**返回**: `Model.GuildRolesResponse`

---

### 创建频道身份组

方法名：`create_guild_role`

```python
async def create_guild_role(
    self,
    guild_id: str,
    name: str = "新的身份组",
    color: int = 0,
    hoist: int = 0,
) -> Model.CreateRoleResponse
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `guild_id` | `str` | 频道 ID |
| `name` | `str` | 身份组名称 |
| `color` | `int` | 颜色值 |
| `hoist` | `int` | 是否在成员列表中单独展示 |

**返回**: `Model.CreateRoleResponse`

---

### 修改频道身份组

方法名：`update_guild_role`

```python
async def update_guild_role(
    self,
    guild_id: str,
    role_id: str,
    name: str | None = None,
    color: int | None = None,
    hoist: int | None = None,
) -> Model.CreateRoleResponse
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `guild_id` | `str` | 频道 ID |
| `role_id` | `str` | 身份组 ID |
| `name` | `str \| None` | 身份组名称 |
| `color` | `int \| None` | 颜色值 |
| `hoist` | `int \| None` | 是否在成员列表中单独展示 |

**返回**: `Model.CreateRoleResponse`

---

### 删除频道身份组

方法名：`delete_guild_role`

```python
async def delete_guild_role(self, guild_id: str, role_id: str) -> bool
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `guild_id` | `str` | 频道 ID |
| `role_id` | `str` | 身份组 ID |

**返回**: `bool`

---

### 添加成员到身份组

方法名：`add_guild_member_role`

```python
async def add_guild_member_role(
    self,
    guild_id: str,
    user_id: str,
    role_id: str,
    channel_id: str | None = None,
) -> bool
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `guild_id` | `str` | 频道 ID |
| `user_id` | `str` | 用户 ID |
| `role_id` | `str` | 身份组 ID |
| `channel_id` | `str \| None` | 子频道 ID（子频道管理员时需要） |

**返回**: `bool`

---

### 从身份组移除成员

方法名：`remove_guild_member_role`

```python
async def remove_guild_member_role(
    self,
    guild_id: str,
    user_id: str,
    role_id: str,
    channel_id: str | None = None,
) -> bool
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `guild_id` | `str` | 频道 ID |
| `user_id` | `str` | 用户 ID |
| `role_id` | `str` | 身份组 ID |
| `channel_id` | `str \| None` | 子频道 ID（子频道管理员时需要） |

**返回**: `bool`

---

### 获取频道身份组成员列表

方法名：`get_guild_role_members`

```python
async def get_guild_role_members(
    self,
    guild_id: str,
    role_id: str,
    start_index: str = "0",
    limit: int = 20,
) -> Model.RoleMembersResponse
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `guild_id` | `str` | 频道 ID |
| `role_id` | `str` | 身份组 ID |
| `start_index` | `str` | 分页起始位置 |
| `limit` | `int` | 分页大小 |

**返回**: `Model.RoleMembersResponse`

---

## 权限 API

### 频道全员禁言

方法名：`mute_guild`

```python
async def mute_guild(
    self,
    guild_id: str,
    mute_seconds: int | None = None,
    mute_end_timestamp: int | None = None,
) -> bool
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `guild_id` | `str` | 频道 ID |
| `mute_seconds` | `int \| None` | 禁言秒数 |
| `mute_end_timestamp` | `int \| None` | 禁言结束时间戳 |

**返回**: `bool`

---

### 频道指定成员禁言

方法名：`mute_guild_member`

```python
async def mute_guild_member(
    self,
    guild_id: str,
    user_id: str,
    mute_seconds: int | None = None,
    mute_end_timestamp: int | None = None,
) -> bool
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `guild_id` | `str` | 频道 ID |
| `user_id` | `str` | 用户 ID |
| `mute_seconds` | `int \| None` | 禁言秒数 |
| `mute_end_timestamp` | `int \| None` | 禁言结束时间戳 |

**返回**: `bool`

---

### 频道批量成员禁言

方法名：`mute_guild_members`

```python
async def mute_guild_members(
    self,
    guild_id: str,
    user_ids: list[str],
    mute_seconds: int | None = None,
    mute_end_timestamp: int | None = None,
) -> Model.MuteBatchResponse
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `guild_id` | `str` | 频道 ID |
| `user_ids` | `list[str]` | 用户 ID 列表 |
| `mute_seconds` | `int \| None` | 禁言秒数 |
| `mute_end_timestamp` | `int \| None` | 禁言结束时间戳 |

**返回**: `Model.MuteBatchResponse`

---

### 取消频道全员禁言

方法名：`cancel_mute_all`

```python
async def cancel_mute_all(self, guild_id: str) -> bool
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `guild_id` | `str` | 频道 ID |

**返回**: `bool`

---

### 取消频道批量成员禁言

方法名：`cancel_mute_multi_member`

```python
async def cancel_mute_multi_member(
    self,
    guild_id: str,
    user_ids: list[str],
) -> Model.MuteBatchResponse
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `guild_id` | `str` | 频道 ID |
| `user_ids` | `list[str]` | 用户 ID 列表 |

**返回**: `Model.MuteBatchResponse`

---

### 获取子频道用户权限

方法名：`get_channel_user_permissions`

```python
async def get_channel_user_permissions(
    self,
    channel_id: str,
    user_id: str,
) -> Model.ChannelPermissions
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `channel_id` | `str` | 子频道 ID |
| `user_id` | `str` | 用户 ID |

**返回**: `Model.ChannelPermissions`

---

### 获取子频道身份组权限

方法名：`get_channel_role_permissions`

```python
async def get_channel_role_permissions(
    self,
    channel_id: str,
    role_id: str,
) -> Model.ChannelPermissions
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `channel_id` | `str` | 子频道 ID |
| `role_id` | `str` | 身份组 ID |

**返回**: `Model.ChannelPermissions`

---

### 修改子频道用户权限

方法名：`update_channel_user_permissions`

```python
async def update_channel_user_permissions(
    self,
    channel_id: str,
    user_id: str,
    add: str | None = None,
    remove: str | None = None,
) -> bool
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `channel_id` | `str` | 子频道 ID |
| `user_id` | `str` | 用户 ID |
| `add` | `str \| None` | 赋予的权限 |
| `remove` | `str \| None` | 删除的权限 |

**返回**: `bool`

---

### 修改子频道身份组权限

方法名：`update_channel_role_permissions`

```python
async def update_channel_role_permissions(
    self,
    channel_id: str,
    role_id: str,
    add: str | None = None,
    remove: str | None = None,
) -> bool
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `channel_id` | `str` | 子频道 ID |
| `role_id` | `str` | 身份组 ID |
| `add` | `str \| None` | 赋予的权限 |
| `remove` | `str \| None` | 删除的权限 |

**返回**: `bool`

---

## 日程 API

### 获取频道日程列表

方法名：`get_schedules`

```python
async def get_schedules(
    self,
    channel_id: str,
    since: str | None = None,
) -> list[Model.Schedule]
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `channel_id` | `str` | 子频道 ID |
| `since` | `str \| None` | 起始时间戳（ms） |

**返回**: `list[Model.Schedule]`

---

### 获取日程详情

方法名：`get_schedule`

```python
async def get_schedule(
    self,
    channel_id: str,
    schedule_id: str,
) -> Model.Schedule
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `channel_id` | `str` | 子频道 ID |
| `schedule_id` | `str` | 日程 ID |

**返回**: `Model.Schedule`

---

### 创建日程

方法名：`create_schedule`

```python
async def create_schedule(
    self,
    channel_id: str,
    name: str,
    start_timestamp: str,
    end_timestamp: str,
    jump_channel_id: str | None = None,
    remind_type: str = "0",
    description: str | None = None,
) -> Model.Schedule
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `channel_id` | `str` | 子频道 ID |
| `name` | `str` | 日程名称 |
| `start_timestamp` | `str` | 开始时间戳（ms） |
| `end_timestamp` | `str` | 结束时间戳（ms） |
| `jump_channel_id` | `str \| None` | 开始时跳转到的子频道 ID |
| `remind_type` | `str` | 提醒类型（0 无提醒，1 开始时提醒，2 5分钟前，3 15分钟前，4 30分钟前，5 60分钟前） |
| `description` | `str \| None` | 日程描述 |

**返回**: `Model.Schedule`

---

### 修改日程

方法名：`update_schedule`

```python
async def update_schedule(
    self,
    channel_id: str,
    schedule_id: str,
    name: str | None = None,
    start_timestamp: str | None = None,
    end_timestamp: str | None = None,
    jump_channel_id: str | None = None,
    remind_type: str | None = None,
    description: str | None = None,
) -> Model.Schedule
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `channel_id` | `str` | 子频道 ID |
| `schedule_id` | `str` | 日程 ID |
| `name` | `str \| None` | 日程名称 |
| `start_timestamp` | `str \| None` | 开始时间戳（ms） |
| `end_timestamp` | `str \| None` | 结束时间戳（ms） |
| `jump_channel_id` | `str \| None` | 开始时跳转到的子频道 ID |
| `remind_type` | `str \| None` | 提醒类型 |
| `description` | `str \| None` | 日程描述 |

**返回**: `Model.Schedule`

---

### 删除日程

方法名：`delete_schedule`

```python
async def delete_schedule(self, channel_id: str, schedule_id: str) -> bool
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `channel_id` | `str` | 子频道 ID |
| `schedule_id` | `str` | 日程 ID |

**返回**: `bool`

---

## 精华消息 API

### 获取精华消息

方法名：`get_pins`

```python
async def get_pins(self, channel_id: str) -> Model.PinsMessage
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `channel_id` | `str` | 子频道 ID |

**返回**: `Model.PinsMessage`

---

### 添加精华消息

方法名：`add_pin`

```python
async def add_pin(self, channel_id: str, message_id: str) -> Model.PinsMessage
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `channel_id` | `str` | 子频道 ID |
| `message_id` | `str` | 消息 ID |

**返回**: `Model.PinsMessage`

---

### 删除精华消息

方法名：`delete_pin`

```python
async def delete_pin(self, channel_id: str, message_id: str) -> bool
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `channel_id` | `str` | 子频道 ID |
| `message_id` | `str` | 消息 ID |

**返回**: `bool`

---

## 论坛 API

### 获取帖子详情

方法名：`get_thread`

```python
async def get_thread(self, channel_id: str, thread_id: str) -> Model.ThreadDetail
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `channel_id` | `str` | 子频道 ID |
| `thread_id` | `str` | 帖子 ID |

**返回**: `Model.ThreadDetail`

---

### 获取帖子列表

方法名：`get_threads`

```python
async def get_threads(self, channel_id: str) -> Model.ThreadListResult
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `channel_id` | `str` | 子频道 ID（须为论坛子频道 type=10007） |

**返回**: `Model.ThreadListResult`

---

### 发表帖子

方法名：`create_thread`

```python
async def create_thread(
    self,
    channel_id: str,
    title: str,
    content: str | Model.ThreadContent,
    format: int | None = None,
) -> Model.CreateThreadResponse
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `channel_id` | `str` | 子频道 ID（须为论坛子频道 type=10007） |
| `title` | `str` | 帖子标题 |
| `content` | `str \| Model.ThreadContent` | 帖子内容，支持字符串或 ThreadContent 对象 |
| `format` | `int \| None` | 帖子格式（1=纯文本, 2=HTML, 3=Markdown, 4=JSON）。content 为字符串时默认 3，为 ThreadContent 时自动设为 4 |

**返回**: `Model.CreateThreadResponse`

**使用示例**:

```python
# Markdown 格式发帖
await bot.api.create_thread(channel_id="xxx", title="标题", content="正文内容")

# JSON 格式发帖（使用构建器）
from easybot import Builders

content = (Builders.ThreadContentBuilder()
    .add_text_paragraph("第一段文字")
    .add_image_paragraph("https://example.com/image.png")
    .add_text_paragraph("第二段文字", bold=True)
    .build())

await bot.api.create_thread(channel_id="xxx", title="标题", content=content)
```

---

### 删除帖子

方法名：`delete_thread`

```python
async def delete_thread(self, channel_id: str, thread_id: str) -> bool
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `channel_id` | `str` | 子频道 ID |
| `thread_id` | `str` | 帖子 ID |

**返回**: `bool`

---

### 发表评论

方法名：`create_thread_comment`

```python
async def create_thread_comment(
    self,
    channel_id: str,
    thread_id: str,
    thread_author: str,
    content: str,
    thread_create_time: str | None = None,
    image: str | None = None,
) -> Model.CreateCommentResponse
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `channel_id` | `str` | 子频道 ID |
| `thread_id` | `str` | 帖子 ID |
| `thread_author` | `str` | 帖子作者 ID |
| `content` | `str` | 评论内容 |
| `thread_create_time` | `str \| None` | 帖子创建时间 |
| `image` | `str \| None` | 图片链接 |

**返回**: `Model.CreateCommentResponse`

---

## 音频 API

### 音频控制

方法名：`audio_control`

```python
async def audio_control(
    self,
    channel_id: str,
    audio_url: str | None = None,
    text: str | None = None,
    status: int = 0,
) -> bool
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `channel_id` | `str` | 子频道 ID |
| `audio_url` | `str \| None` | 音频 URL |
| `text` | `str \| None` | 状态文本 |
| `status` | `int` | 播放状态（0 开始、1 暂停、2 继续、3 停止） |

**返回**: `bool`

---

### 机器人上麦

方法名：`mic_up`

```python
async def mic_up(self, channel_id: str) -> bool
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `channel_id` | `str` | 子频道 ID |

**返回**: `bool`

---

### 机器人下麦

方法名：`mic_down`

```python
async def mic_down(self, channel_id: str) -> bool
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `channel_id` | `str` | 子频道 ID |

**返回**: `bool`

---

## 其他 API

### 获取表情表态用户列表

方法名：`get_reaction_users`

```python
async def get_reaction_users(
    self,
    channel_id: str,
    message_id: str,
    emoji_type: int,
    emoji_id: str,
    cookie: str | None = None,
    limit: int = 20,
) -> Model.ReactionUsers
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `channel_id` | `str` | 子频道 ID |
| `message_id` | `str` | 消息 ID |
| `emoji_type` | `int` | 表情类型 |
| `emoji_id` | `str` | 表情 ID |
| `cookie` | `str \| None` | 分页 cookie |
| `limit` | `int` | 每页数量 |

**返回**: `Model.ReactionUsers`

---

### 机器人发表表情表态

方法名：`create_reaction`

```python
async def create_reaction(
    self,
    channel_id: str,
    message_id: str,
    emoji_type: int,
    emoji_id: str,
) -> bool
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `channel_id` | `str` | 子频道 ID |
| `message_id` | `str` | 消息 ID |
| `emoji_type` | `int` | 表情类型（1 系统表情，2 emoji表情） |
| `emoji_id` | `str` | 表情 ID |

**返回**: `bool`

---

### 删除机器人发表的表情表态

方法名：`delete_reaction`

```python
async def delete_reaction(
    self,
    channel_id: str,
    message_id: str,
    emoji_type: int,
    emoji_id: str,
) -> bool
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `channel_id` | `str` | 子频道 ID |
| `message_id` | `str` | 消息 ID |
| `emoji_type` | `int` | 表情类型 |
| `emoji_id` | `str` | 表情 ID |

**返回**: `bool`

---

### 获取通用 WSS 接入点

方法名：`get_gateway`

```python
async def get_gateway(self) -> Model.GatewayResponse
```

**返回**: `Model.GatewayResponse`

---

### 获取带分片 WSS 接入点

方法名：`get_gateway_bot`

```python
async def get_gateway_bot(self) -> Model.GatewayBotResponse
```

**返回**: `Model.GatewayBotResponse`

---

### 获取频道消息频率设置

方法名：`get_guild_message_setting`

```python
async def get_guild_message_setting(self, guild_id: str) -> Model.MessageSetting
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `guild_id` | `str` | 频道 ID |

**返回**: `Model.MessageSetting`

---

### 回应互动按钮点击事件

方法名：`respond_interaction`

```python
async def respond_interaction(
    self,
    interaction_id: str,
    code: int = 0,
) -> bool
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `interaction_id` | `str` | 互动事件 ID |
| `code` | `int` | 回应码（0 成功，1 操作失败，2 操作频繁，3 重复操作，4 没有权限，5 仅管理员操作） |

**返回**: `bool`

---

### 获取机器人资料页分享链接

方法名：`generate_url_link`

```python
async def generate_url_link(self, callback_data: str | None = None) -> Model.UrlLinkResponse
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `callback_data` | `str \| None` | 追踪参数（最长32字符） |

**返回**: `Model.UrlLinkResponse`

---

### 上传富媒体文件

方法名：`upload_media`

```python
async def upload_media(
    self,
    file_type: int,
    url: str | None = None,
    file_data: bytes | str | None = None,
    srv_send_msg: bool = False,
    user_openid: str | None = None,
    group_openid: str | None = None,
) -> Model.FileInfo
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `file_type` | `int` | 媒体类型（1 图片、2 视频、3 语音、4 文件） |
| `url` | `str \| None` | 媒体资源 URL |
| `file_data` | `bytes \| str \| None` | 文件数据（bytes 或本地文件路径） |
| `srv_send_msg` | `bool` | 是否直接发送消息 |
| `user_openid` | `str \| None` | 用户 openid（单聊时使用） |
| `group_openid` | `str \| None` | 群 openid（群聊时使用） |

**返回**: `Model.FileInfo`

**注意**: `url` 和 `file_data` 二选一；`user_openid` 和 `group_openid` 二选一。

---

### 获取当前用户（机器人）信息

方法名：`get_me`

```python
async def get_me(self) -> Model.Author
```

**返回**: `Model.Author`

---

### 获取机器人在频道可用权限列表

方法名：`get_guild_api_permissions`

```python
async def get_guild_api_permissions(self, guild_id: str) -> Model.APIPermissionListResponse
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `guild_id` | `str` | 频道 ID |

**返回**: `Model.APIPermissionListResponse`

---

### 发送机器人在频道接口权限的授权链接

方法名：`demand_guild_api_permission`

```python
async def demand_guild_api_permission(
    self,
    guild_id: str,
    channel_id: str,
    api_path: str,
    api_method: str,
    desc: str,
) -> Model.APIPermissionDemand
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `guild_id` | `str` | 频道 ID |
| `channel_id` | `str` | 子频道 ID |
| `api_path` | `str` | API 接口名 |
| `api_method` | `str` | 请求方法 |
| `desc` | `str` | 权限描述 |

**返回**: `Model.APIPermissionDemand`

---

### 创建频道公告

方法名：`create_announces`

```python
async def create_announces(
    self,
    guild_id: str,
    message_id: str | None = None,
    channel_id: str | None = None,
    announces_type: int = 0,
    recommend_channels: list[dict] | None = None,
) -> Model.Announces
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `guild_id` | `str` | 频道 ID |
| `message_id` | `str \| None` | 消息 ID |
| `channel_id` | `str \| None` | 子频道 ID |
| `announces_type` | `int` | 公告类别（0 成员公告，1 欢迎公告） |
| `recommend_channels` | `list[dict] \| None` | 推荐子频道列表 |

**返回**: `Model.Announces`

---

### 删除频道公告

方法名：`delete_announces`

```python
async def delete_announces(self, guild_id: str, message_id: str = "all") -> bool
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `guild_id` | `str` | 频道 ID |
| `message_id` | `str` | 消息 ID，传 "all" 删除全部 |

**返回**: `bool`

---

## 下一步

- [Messages Model](./05_Messages_Model.md) — 掌握各种消息类型的构建方法
- [Model 库](./06_Model库.md) — 了解接收事件时的数据模型定义
- [插件与权限](./07_插件与权限.md) — 命令注册、预处理器和权限控制
