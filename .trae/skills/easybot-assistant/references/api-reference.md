# EasyBot API 参考文档

## 目录

1. [频道相关 API](#频道相关-api)
2. [子频道相关 API](#子频道相关-api)
3. [消息相关 API](#消息相关-api)
4. [群聊相关 API](#群聊相关-api)
5. [单聊相关 API](#单聊相关-api)
6. [私信相关 API](#私信相关-api)
7. [成员管理 API](#成员管理-api)
8. [身份组管理 API](#身份组管理-api)
9. [权限管理 API](#权限管理-api)
10. [其他 API](#其他-api)
    - [大文件分片上传](#大文件分片上传)

---

## 频道相关 API

### get_guild(guild_id: str) -> Model.Guild

获取频道详情。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| guild_id | str | 是 | 频道 ID |

**返回值：** `Model.Guild` - 频道对象

```python
guild = await bot.api.get_guild("guild_id")
print(f"频道名称: {guild.name}")
```

### get_guild_list(before=None, after=None, limit=100) -> list[Model.Guild]

获取机器人所在频道列表。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| before | str | 否 | 读此 guild id 之前的数据 |
| after | str | 否 | 读此 guild id 之后的数据 |
| limit | int | 否 | 每次拉取数量，默认 100，最大 100 |

**返回值：** `list[Model.Guild]` - 频道对象列表

```python
guilds = await bot.api.get_guild_list(limit=50)
for guild in guilds:
    print(f"{guild.id}: {guild.name}")
```

### get_me() -> Model.Author

获取当前机器人信息。

**返回值：** `Model.Author` - 用户对象

```python
me = await bot.api.get_me()
print(f"机器人ID: {me.id}, 名称: {me.username}")
```

### get_guild_message_setting(guild_id: str) -> Model.MessageSetting

获取频道消息频率设置。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| guild_id | str | 是 | 频道 ID |

**返回值：** `Model.MessageSetting` - 消息频率设置对象

```python
setting = await bot.api.get_guild_message_setting("guild_id")
```

---

## 子频道相关 API

### get_guild_channels(guild_id: str) -> list[Model.Channel]

获取频道子频道列表。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| guild_id | str | 是 | 频道 ID |

**返回值：** `list[Model.Channel]` - 子频道对象列表

```python
channels = await bot.api.get_guild_channels("guild_id")
for ch in channels:
    print(f"{ch.id}: {ch.name} (type={ch.type})")
```

### get_channel(channel_id: str) -> Model.Channel

获取子频道详情。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| channel_id | str | 是 | 子频道 ID |

**返回值：** `Model.Channel` - 子频道对象

```python
channel = await bot.api.get_channel("channel_id")
```

### create_channel(...) -> Model.Channel

创建子频道。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| guild_id | str | 是 | 频道 ID |
| name | str | 是 | 子频道名称 |
| channel_type | int | 是 | 子频道类型（0=文字, 2=语音, 4=分类, 10005=帖子, 10007=论坛） |
| position | int | 是 | 排序值 |
| parent_id | str | 否 | 所属分组 ID |
| sub_type | int | 否 | 子频道子类型（0=闲聊, 1=公告, 2=攻略, 3=开黑） |
| private_type | int | 否 | 子频道私密类型（0=公开, 1=指定成员可见, 2=指定身份组可见） |
| private_user_ids | list[str] | 否 | 子频道私密成员 ID 列表 |
| speak_permission | int | 否 | 子频道发言权限（0=继承父频道, 1=指定成员可发言, 2=指定身份组可发言） |
| application_id | str | 否 | 应用类型子频道 AppID |

**返回值：** `Model.Channel` - 创建的子频道对象

```python
channel = await bot.api.create_channel(
    guild_id="guild_id",
    name="新子频道",
    channel_type=0,
    position=1,
)

# 创建私密子频道
channel = await bot.api.create_channel(
    guild_id="guild_id",
    name="私密子频道",
    channel_type=0,
    position=2,
    private_type=1,
    private_user_ids=["user_id_1", "user_id_2"],
)
```

### update_channel(...) -> Model.Channel

修改子频道。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| channel_id | str | 是 | 子频道 ID |
| name | str | 否 | 子频道名称 |
| position | int | 否 | 排序值 |
| parent_id | str | 否 | 所属分组 ID |
| private_type | int | 否 | 子频道私密类型 |
| speak_permission | int | 否 | 子频道发言权限 |

**返回值：** `Model.Channel` - 修改后的子频道对象

```python
channel = await bot.api.update_channel(
    channel_id="channel_id",
    name="新名称",
)
```

### delete_channel(channel_id: str) -> bool

删除子频道。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| channel_id | str | 是 | 子频道 ID |

**返回值：** `bool` - 是否删除成功

```python
await bot.api.delete_channel("channel_id")
```

---

## 消息相关 API

### send_guild_message(...) -> Model.GuildMessage

发送频道消息。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| channel_id | str | 是 | 子频道 ID |
| content | str \| MessagesModel.Message \| MessagesModel.MessageEmbed \| MessagesModel.MessageArk23 \| MessagesModel.MessageArk24 \| MessagesModel.MessageArk37 \| MessagesModel.MessageMarkdown \| None | 否 | 消息内容，可以是文本或消息对象 |
| image | str | 否 | 图片 URL（普通消息） |
| file_image | bytes \| BinaryIO \| str | 否 | 图片数据，支持 bytes、BinaryIO 或文件路径（普通消息） |
| msg_id | str | 否 | 要回复的消息 ID（被动消息，有效期5分钟） |
| event_id | str | 否 | 要回复的事件 ID（被动消息） |
| message_reference_id | str | 否 | 引用消息 ID |
| ignore_message_reference_error | bool | 否 | 是否忽略引用消息错误，默认 False |

**返回值：** `Model.GuildMessage` - 发送的消息对象

```python
from easybot import MessagesModel

# 文本消息
msg = await bot.api.send_guild_message(
    channel_id="channel_id",
    content="Hello!",
)

# Embed 消息
msg = await bot.api.send_guild_message(
    channel_id="channel_id",
    content=MessagesModel.MessageEmbed(
        title="标题",
        prompt="提示",
        content=["字段1", "字段2"]
    )
)

# Markdown 消息
msg = await bot.api.send_guild_message(
    channel_id="channel_id",
    content=MessagesModel.MessageMarkdown(content="# 标题")
)

# 带图片
msg = await bot.api.send_guild_message(
    channel_id="channel_id",
    content="图片消息",
    image="https://example.com/image.png"
)

# 本地图片
msg = await bot.api.send_guild_message(
    channel_id="channel_id",
    content="本地图片",
    file_image="./image.png"
)

# 引用回复
msg = await bot.api.send_guild_message(
    channel_id="channel_id",
    content="引用回复",
    message_reference_id="被引用的消息ID"
)

# 被动消息（回复用户消息）
msg = await bot.api.send_guild_message(
    channel_id="channel_id",
    content="回复内容",
    msg_id="用户消息ID",  # 有效期5分钟
)
```

### get_guild_message(channel_id, message_id) -> Model.GuildMessage

获取指定消息。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| channel_id | str | 是 | 子频道 ID |
| message_id | str | 是 | 消息 ID |

**返回值：** `Model.GuildMessage` - 消息对象

```python
msg = await bot.api.get_guild_message("channel_id", "message_id")
```

### recall_guild_message(channel_id, message_id, hidetip=False) -> bool

撤回频道消息。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| channel_id | str | 是 | 子频道 ID |
| message_id | str | 是 | 消息 ID |
| hidetip | bool | 否 | 是否隐藏提示小灰条，默认 False |

**返回值：** `bool` - 是否撤回成功

```python
await bot.api.recall_guild_message("channel_id", "message_id")
```

### patch_guild_message(...) -> Model.GuildMessage

修改频道 Markdown 消息。

**注意：** 需要先申请权限才能使用此接口。仅支持修改 Markdown 和 Keyboard 内容。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| channel_id | str | 是 | 子频道 ID |
| patch_msg_id | str | 是 | 需要修改的消息 ID |
| content | str \| MessagesModel.MessageMarkdown \| ... | 否 | 消息内容，推荐使用 MessagesModel.MessageMarkdown |
| msg_id | str | 否 | 要回复的消息的 ID（被动消息） |
| event_id | str | 否 | 要回复的事件 ID（被动消息） |

**返回值：** `Model.GuildMessage` - 修改后的消息对象

```python
# 使用 Markdown 消息对象修改
md = MessagesModel.MessageMarkdown(content="# 更新后的标题")
await bot.api.patch_guild_message("channel_id", "message_id", content=md)

# 使用带 Keyboard 的 Markdown 修改
md = MessagesModel.MessageMarkdown(
    content="# 标题",
    keyboard_content={"rows": [{"buttons": [...]}]}
)
await bot.api.patch_guild_message("channel_id", "message_id", content=md)
```

---

## 群聊相关 API

### send_group_message(...) -> Model.GroupSendMessageResponse

发送群聊消息。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| group_openid | str | 是 | 群 openid |
| content | str \| MessagesModel.Message \| ... | 否 | 消息内容，可以是文本或消息对象 |
| media_file_info | str | 否 | 富媒体文件信息（群聊 v2，需先调用 upload_media） |
| event_id | str | 否 | 前置收到的事件 ID（被动消息） |
| msg_id | str | 否 | 要回复的消息 ID（被动消息） |
| msg_type | int | 否 | 消息类型，默认按内容自动推断 |
| msg_seq | int | 否 | 回复消息的序号，与 msg_id 联合使用避免重复发送 |
| message_reference_id | str | 否 | 引用消息 ID |
| ignore_message_reference_error | bool | 否 | 是否忽略引用消息错误，默认 False |

**返回值：** `Model.GroupSendMessageResponse` - 发送的消息响应

```python
# 文本消息
msg = await bot.api.send_group_message(
    group_openid="group_openid",
    content="Hello!",
)

# 被动消息
msg = await bot.api.send_group_message(
    group_openid="group_openid",
    content="Hello!",
    event_id="event_id",
)

# 富媒体消息（需先上传）
result = await bot.api.upload_media(
    file_type=1,
    file_data="./image.png",
    group_openid="group_openid"
)
msg = await bot.api.send_group_message(
    group_openid="group_openid",
    content="图片",
    media_file_info=result.file_info,
)

# Markdown 消息
msg = await bot.api.send_group_message(
    group_openid="group_openid",
    content=MessagesModel.MessageMarkdown(content="# 标题"),
)

# Embed 消息
msg = await bot.api.send_group_message(
    group_openid="group_openid",
    content=MessagesModel.MessageEmbed(title="标题"),
)

# 引用回复
msg = await bot.api.send_group_message(
    group_openid="group_openid",
    content="回复内容",
    message_reference_id="引用的消息ID"
)
```

### recall_group_message(group_openid, message_id) -> bool

撤回群聊消息。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| group_openid | str | 是 | 群 openid |
| message_id | str | 是 | 消息 ID |

**返回值：** `bool` - 是否撤回成功

```python
await bot.api.recall_group_message("group_openid", "message_id")
```

---

## 单聊相关 API

### send_c2c_message(...) -> Model.C2CSendMessageResponse

发送单聊消息。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| openid | str | 是 | 用户 openid |
| content | str \| MessagesModel.Message \| ... | 否 | 消息内容，可以是文本或消息对象 |
| media_file_info | str | 否 | 富媒体文件信息（QQ 单聊 v2，需先调用 upload_media） |
| event_id | str | 否 | 前置收到的事件 ID（被动消息） |
| msg_id | str | 否 | 要回复的消息 ID（被动消息） |
| msg_type | int | 否 | 消息类型，默认按内容自动推断 |
| msg_seq | int | 否 | 回复消息的序号，与 msg_id 联合使用避免重复发送 |
| is_wakeup | bool | 否 | 是否发送互动召回消息，默认 False |
| message_reference_id | str | 否 | 引用消息 ID |
| ignore_message_reference_error | bool | 否 | 是否忽略引用消息错误，默认 False |

**返回值：** `Model.C2CSendMessageResponse` - 发送的消息响应

```python
# 文本消息
msg = await bot.api.send_c2c_message(
    openid="user_openid",
    content="Hello!",
)

# 被动消息
msg = await bot.api.send_c2c_message(
    openid="user_openid",
    content="Hello!",
    event_id="event_id",
)

# 富媒体消息（需先上传）
result = await bot.api.upload_media(
    file_type=1,
    file_data="./image.png",
    user_openid="user_openid"
)
msg = await bot.api.send_c2c_message(
    openid="user_openid",
    content="图片",
    media_file_info=result.file_info,
)

# Markdown 消息
msg = await bot.api.send_c2c_message(
    openid="user_openid",
    content=MessagesModel.MessageMarkdown(content="# 标题"),
)

# Embed 消息
msg = await bot.api.send_c2c_message(
    openid="user_openid",
    content=MessagesModel.MessageEmbed(title="标题"),
)

# 引用回复
msg = await bot.api.send_c2c_message(
    openid="user_openid",
    content="回复内容",
    message_reference_id="引用的消息ID"
)
```

### recall_c2c_message(openid, message_id) -> bool

撤回单聊消息。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| openid | str | 是 | 用户 openid |
| message_id | str | 是 | 消息 ID |

**返回值：** `bool` - 是否撤回成功

```python
await bot.api.recall_c2c_message("openid", "message_id")
```

### send_c2c_stream_message(...) -> Model.StreamMessageResponse

发送流式消息（AI 对话场景）。

**流式协议说明：**
- 首次调用时不传 `stream_msg_id`，由平台返回
- 后续分片携带 `stream_msg_id` 和递增 `msg_seq`
- `input_state=1` 表示生成中，`input_state=10` 表示生成结束（终结状态）

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| openid | str | 是 | 用户 openid |
| content_raw | str | 是 | Markdown 内容 |
| event_id | str | 是 | 事件 ID |
| msg_id | str | 是 | 原始消息 ID |
| msg_seq | int | 是 | 递增序号 |
| index | int | 是 | 同一条流式会话内的发送索引，从 0 开始，每次发送前递增 |
| input_mode | str | 否 | 输入模式，默认 "replace"（每次发送的 content_raw 替换整条消息内容） |
| input_state | int | 否 | 输入状态，1=正文生成中，10=正文生成结束（终结状态） |
| content_type | str | 否 | 内容类型，默认 "markdown" |
| stream_msg_id | str | 否 | 流式消息 ID，首次发送后返回，后续分片需携带 |

**返回值：** `Model.StreamMessageResponse` - 流式消息响应

```python
# 首次发送（开始流式消息）
resp = await bot.api.send_c2c_stream_message(
    openid="openid",
    content_raw="正在生成...",
    event_id="event_id",
    msg_id="msg_id",
    msg_seq=0,
    index=0,
    input_state=1,  # 生成中
)
stream_msg_id = resp.id  # 保存后续使用

# 后续分片
await bot.api.send_c2c_stream_message(
    openid="openid",
    content_raw="更新内容",
    event_id="event_id",
    msg_id="msg_id",
    msg_seq=1,
    index=1,
    stream_msg_id=stream_msg_id,
    input_state=1,
)

# 结束
await bot.api.send_c2c_stream_message(
    openid="openid",
    content_raw="最终内容",
    event_id="event_id",
    msg_id="msg_id",
    msg_seq=2,
    index=2,
    stream_msg_id=stream_msg_id,
    input_state=10,  # 结束状态
)
```

### upload_media(...) -> Model.FileInfo

上传富媒体文件，支持 QQ 单聊和群聊场景。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file_type | int | 是 | 媒体类型（1=图片, 2=视频, 3=语音, 4=文件） |
| url | str | 否* | 媒体资源 URL，与 file_data 二选一 |
| file_data | bytes \| str | 否* | 文件数据或本地路径，与 url 二选一 |
| srv_send_msg | bool | 否 | 是否直接发送消息，默认 False |
| user_openid | str | 否* | 用户 openid（单聊），与 group_openid 二选一 |
| group_openid | str | 否* | 群 openid（群聊），与 user_openid 二选一 |
| file_name | str | 条件必填 | 文件名（含扩展名），**file_type=4 时必填** |

> *注：url 与 file_data 必须提供其中之一；user_openid 与 group_openid 必须提供其中之一。

**返回值：** `Model.FileInfo` - 包含 file_uuid、file_info、ttl 字段的响应

```python
# 上传图片到单聊
result = await bot.api.upload_media(
    file_type=1,
    file_data="./image.png",
    user_openid="openid"
)

# 上传图片到群聊
result = await bot.api.upload_media(
    file_type=1,
    file_data="./image.png",
    group_openid="group_openid"
)

# 上传文件（file_type=4 时 file_name 必填）
result = await bot.api.upload_media(
    file_type=4,
    file_data="./document.pdf",
    file_name="document.pdf",  # 必须包含扩展名
    group_openid="group_openid"
)

# 使用 URL 上传
result = await bot.api.upload_media(
    file_type=1,
    url="https://example.com/image.png",
    user_openid="openid"
)

# 使用二进制数据上传
with open("image.png", "rb") as f:
    result = await bot.api.upload_media(
        file_type=1,
        file_data=f.read(),
        user_openid="openid"
    )
```

---

## 私信相关 API

### create_dms(recipient_id, source_guild_id) -> Model.DMS

创建私信会话。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| recipient_id | str | 是 | 接收者 ID |
| source_guild_id | str | 是 | 源频道 ID |

**返回值：** `Model.DMS` - 私信会话对象

```python
dms = await bot.api.create_dms(
    recipient_id="user_id",
    source_guild_id="guild_id"
)
# 使用 dms.guild_id 发送私信
```

### send_direct_message(...) -> Model.GuildMessage

发送频道私信消息。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| guild_id | str | 是 | 私信频道 ID |
| content | str \| MessagesModel.Message \| ... | 否 | 消息内容，可以是文本或消息对象 |
| image | str | 否 | 图片 URL（普通消息） |
| file_image | bytes \| BinaryIO \| str | 否 | 图片数据，支持 bytes、BinaryIO 或文件路径（普通消息） |
| msg_id | str | 否 | 要回复的消息 ID（被动消息） |
| event_id | str | 否 | 要回复的事件 ID（被动消息） |
| message_reference_id | str | 否 | 引用消息 ID |
| ignore_message_reference_error | bool | 否 | 是否忽略引用消息错误，默认 False |

**返回值：** `Model.GuildMessage` - 发送的消息对象

```python
# 文本消息
msg = await bot.api.send_direct_message(
    guild_id="dms_guild_id",
    content="私信内容",
)

# Embed 消息
msg = await bot.api.send_direct_message(
    guild_id="dms_guild_id",
    content=MessagesModel.MessageEmbed(title="标题"),
)

# 带图片
msg = await bot.api.send_direct_message(
    guild_id="dms_guild_id",
    content="图片",
    image="https://example.com/image.png",
)

# 引用回复
msg = await bot.api.send_direct_message(
    guild_id="dms_guild_id",
    content="回复内容",
    message_reference_id="引用的消息ID"
)
```

### recall_direct_message(guild_id, message_id, hidetip=False) -> bool

撤回频道私信消息。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| guild_id | str | 是 | 私信频道 ID |
| message_id | str | 是 | 消息 ID |
| hidetip | bool | 否 | 是否隐藏提示小灰条，默认 False |

**返回值：** `bool` - 是否撤回成功

```python
await bot.api.recall_direct_message("guild_id", "message_id")
```

---

## 成员管理 API

### get_guild_members(guild_id, after="0", limit=100) -> list[Model.Member]

获取频道成员列表。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| guild_id | str | 是 | 频道 ID |
| after | str | 否 | 上一次回包中最后一个 member 的 user id，默认 "0" |
| limit | int | 否 | 分页大小，默认 100，最大 1000 |

**返回值：** `list[Model.Member]` - 成员对象列表

```python
members = await bot.api.get_guild_members("guild_id", limit=100)
```

### get_guild_member(guild_id, user_id) -> Model.Member

获取频道成员详情。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| guild_id | str | 是 | 频道 ID |
| user_id | str | 是 | 用户 ID |

**返回值：** `Model.Member` - 成员对象

```python
member = await bot.api.get_guild_member("guild_id", "user_id")
```

### delete_guild_member(guild_id, user_id, add_blacklist=False, delete_history_msg_days=0) -> bool

删除频道成员（踢人）。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| guild_id | str | 是 | 频道 ID |
| user_id | str | 是 | 用户 ID |
| add_blacklist | bool | 否 | 是否同时添加到黑名单，默认 False |
| delete_history_msg_days | int | 否 | 撤回消息天数（3, 7, 15, 30, -1 全部），默认 0 |

**返回值：** `bool` - 是否删除成功

```python
await bot.api.delete_guild_member(
    guild_id="guild_id",
    user_id="user_id",
    add_blacklist=True,
    delete_history_msg_days=3
)
```

### get_channel_online_nums(channel_id) -> Model.OnlineNumsResponse

获取子频道在线成员数。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| channel_id | str | 是 | 子频道 ID |

**返回值：** `Model.OnlineNumsResponse` - 在线成员数响应

```python
result = await bot.api.get_channel_online_nums("channel_id")
print(f"在线人数: {result.online_nums}")
```

---

## 身份组管理 API

### get_guild_roles(guild_id) -> Model.GuildRolesResponse

获取频道身份组列表。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| guild_id | str | 是 | 频道 ID |

**返回值：** `Model.GuildRolesResponse` - 包含 roles 列表和 role_num_limit 的响应

```python
result = await bot.api.get_guild_roles("guild_id")
for role in result.roles:
    print(f"{role.id}: {role.name}")
```

### create_guild_role(guild_id, name, color=0, hoist=0) -> Model.CreateRoleResponse

创建频道身份组。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| guild_id | str | 是 | 频道 ID |
| name | str | 否 | 身份组名称，默认 "新的身份组" |
| color | int | 否 | 颜色值，默认 0 |
| hoist | int | 否 | 是否在成员列表中单独展示，默认 0 |

**返回值：** `Model.CreateRoleResponse` - 包含 role_id 和 role 的响应

```python
result = await bot.api.create_guild_role(
    guild_id="guild_id",
    name="新身份组",
    color=0xFF0000,
)
```

### update_guild_role(guild_id, role_id, ...) -> Model.CreateRoleResponse

修改频道身份组。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| guild_id | str | 是 | 频道 ID |
| role_id | str | 是 | 身份组 ID |
| name | str | 否 | 身份组名称 |
| color | int | 否 | 颜色值 |
| hoist | int | 否 | 是否在成员列表中单独展示 |

**返回值：** `Model.CreateRoleResponse` - 包含 role_id 和 role 的响应

```python
await bot.api.update_guild_role(
    guild_id="guild_id",
    role_id="role_id",
    name="新名称",
)
```

### delete_guild_role(guild_id, role_id) -> bool

删除频道身份组。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| guild_id | str | 是 | 频道 ID |
| role_id | str | 是 | 身份组 ID |

**返回值：** `bool` - 是否删除成功

```python
await bot.api.delete_guild_role("guild_id", "role_id")
```

### add_guild_member_role(guild_id, user_id, role_id, channel_id=None) -> bool

添加成员到身份组。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| guild_id | str | 是 | 频道 ID |
| user_id | str | 是 | 用户 ID |
| role_id | str | 是 | 身份组 ID |
| channel_id | str | 否 | 子频道 ID（当身份组为子频道管理员时需要） |

**返回值：** `bool` - 是否添加成功

```python
await bot.api.add_guild_member_role(
    guild_id="guild_id",
    user_id="user_id",
    role_id="role_id",
)
```

### remove_guild_member_role(guild_id, user_id, role_id, channel_id=None) -> bool

从身份组移除成员。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| guild_id | str | 是 | 频道 ID |
| user_id | str | 是 | 用户 ID |
| role_id | str | 是 | 身份组 ID |
| channel_id | str | 否 | 子频道 ID（当身份组为子频道管理员时需要） |

**返回值：** `bool` - 是否移除成功

```python
await bot.api.remove_guild_member_role(
    guild_id="guild_id",
    user_id="user_id",
    role_id="role_id",
)
```

### get_guild_role_members(guild_id, role_id, ...) -> Model.RoleMembersResponse

获取身份组成员列表。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| guild_id | str | 是 | 频道 ID |
| role_id | str | 是 | 身份组 ID |
| start_index | str | 否 | 分页起始位置，默认 "0" |
| limit | int | 否 | 分页大小，默认 20 |

**返回值：** `Model.RoleMembersResponse` - 包含 data 和 next 的响应

```python
result = await bot.api.get_guild_role_members("guild_id", "role_id")
```

---

## 权限管理 API

### 禁言相关

#### mute_guild(guild_id, mute_seconds=None, mute_end_timestamp=None) -> bool

频道全员禁言。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| guild_id | str | 是 | 频道 ID |
| mute_seconds | int | 否 | 禁言秒数 |
| mute_end_timestamp | int | 否 | 禁言结束时间戳 |

**返回值：** `bool` - 是否禁言成功

```python
# 禁言 1 小时
await bot.api.mute_guild(guild_id="guild_id", mute_seconds=3600)

# 禁言到指定时间
await bot.api.mute_guild(guild_id="guild_id", mute_end_timestamp=1640000000)
```

#### mute_guild_member(guild_id, user_id, mute_seconds=None, mute_end_timestamp=None) -> bool

指定成员禁言。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| guild_id | str | 是 | 频道 ID |
| user_id | str | 是 | 用户 ID |
| mute_seconds | int | 否 | 禁言秒数 |
| mute_end_timestamp | int | 否 | 禁言结束时间戳 |

**返回值：** `bool` - 是否禁言成功

```python
await bot.api.mute_guild_member(
    guild_id="guild_id",
    user_id="user_id",
    mute_seconds=3600
)
```

#### mute_guild_members(guild_id, user_ids, mute_seconds=None, mute_end_timestamp=None) -> Model.MuteBatchResponse

批量禁言。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| guild_id | str | 是 | 频道 ID |
| user_ids | list[str] | 是 | 用户 ID 列表 |
| mute_seconds | int | 否 | 禁言秒数 |
| mute_end_timestamp | int | 否 | 禁言结束时间戳 |

**返回值：** `Model.MuteBatchResponse` - 设置成功的用户 ID 列表响应

```python
result = await bot.api.mute_guild_members(
    guild_id="guild_id",
    user_ids=["user_id1", "user_id2"],
    mute_seconds=3600
)
```

#### cancel_mute_all(guild_id) -> bool

取消全员禁言。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| guild_id | str | 是 | 频道 ID |

**返回值：** `bool` - 是否操作成功

```python
await bot.api.cancel_mute_all("guild_id")
```

#### cancel_mute_multi_member(guild_id, user_ids) -> Model.MuteBatchResponse

取消批量禁言。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| guild_id | str | 是 | 频道 ID |
| user_ids | list[str] | 是 | 用户 ID 列表 |

**返回值：** `Model.MuteBatchResponse` - 设置成功的用户 ID 列表响应

```python
await bot.api.cancel_mute_multi_member("guild_id", ["user_id1"])
```

### 子频道权限

#### get_channel_user_permissions(channel_id, user_id) -> Model.ChannelPermissions

获取用户权限。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| channel_id | str | 是 | 子频道 ID |
| user_id | str | 是 | 用户 ID |

**返回值：** `Model.ChannelPermissions` - 子频道权限对象

```python
perms = await bot.api.get_channel_user_permissions("channel_id", "user_id")
```

#### get_channel_role_permissions(channel_id, role_id) -> Model.ChannelPermissions

获取身份组权限。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| channel_id | str | 是 | 子频道 ID |
| role_id | str | 是 | 身份组 ID |

**返回值：** `Model.ChannelPermissions` - 子频道权限对象

```python
perms = await bot.api.get_channel_role_permissions("channel_id", "role_id")
```

#### update_channel_user_permissions(channel_id, user_id, add=None, remove=None) -> bool

修改用户权限。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| channel_id | str | 是 | 子频道 ID |
| user_id | str | 是 | 用户 ID |
| add | str | 否 | 赋予的权限 |
| remove | str | 否 | 删除的权限 |

**返回值：** `bool` - 是否修改成功

```python
await bot.api.update_channel_user_permissions(
    channel_id="channel_id",
    user_id="user_id",
    add="4",  # 添加查看权限
    remove="1"  # 移除发言权限
)
```

#### update_channel_role_permissions(channel_id, role_id, add=None, remove=None) -> bool

修改身份组权限。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| channel_id | str | 是 | 子频道 ID |
| role_id | str | 是 | 身份组 ID |
| add | str | 否 | 赋予的权限 |
| remove | str | 否 | 删除的权限 |

**返回值：** `bool` - 是否修改成功

```python
await bot.api.update_channel_role_permissions(
    channel_id="channel_id",
    role_id="role_id",
    add="4",
)
```

### API 权限

#### get_guild_api_permissions(guild_id) -> Model.APIPermissionListResponse

获取机器人可用权限。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| guild_id | str | 是 | 频道 ID |

**返回值：** `Model.APIPermissionListResponse` - 包含 apis 列表的响应

```python
result = await bot.api.get_guild_api_permissions("guild_id")
for api in result.apis:
    print(f"{api.path}: {api.auth_status}")
```

#### demand_guild_api_permission(guild_id, channel_id, api_path, api_method, desc) -> Model.APIPermissionDemand

发送权限申请链接。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| guild_id | str | 是 | 频道 ID |
| channel_id | str | 是 | 授权链接发送的子频道 ID |
| api_path | str | 是 | API 接口名 |
| api_method | str | 是 | 请求方法 |
| desc | str | 是 | 机器人申请权限后可使用功能的描述 |

**返回值：** `Model.APIPermissionDemand` - API权限需求对象

```python
await bot.api.demand_guild_api_permission(
    guild_id="xxx",
    channel_id="xxx",
    api_path="/guilds/{guild_id}/members/{user_id}",
    api_method="DELETE",
    desc="踢人功能需要此权限"
)
```

---

## 其他 API

### 公告管理

#### create_announces(guild_id, message_id=None, channel_id=None, announces_type=0, recommend_channels=None) -> Model.Announces

创建公告。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| guild_id | str | 是 | 频道 ID |
| message_id | str | 否 | 消息 ID |
| channel_id | str | 否 | 子频道 ID |
| announces_type | int | 否 | 公告类别（0=成员公告, 1=欢迎公告），默认 0 |
| recommend_channels | list[dict] | 否 | 推荐子频道列表 |

**返回值：** `Model.Announces` - 公告对象

```python
await bot.api.create_announces(
    guild_id="guild_id",
    message_id="message_id",
    channel_id="channel_id",
)
```

#### delete_announces(guild_id, message_id="all") -> bool

删除公告。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| guild_id | str | 是 | 频道 ID |
| message_id | str | 否 | 消息 ID，传 "all" 删除全部，默认 "all" |

**返回值：** `bool` - 是否删除成功

```python
# 删除指定公告
await bot.api.delete_announces("guild_id", "message_id")

# 删除全部公告
await bot.api.delete_announces("guild_id", "all")
```

### 日程管理

#### get_schedules(channel_id, since=None) -> list[Model.Schedule]

获取日程列表。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| channel_id | str | 是 | 子频道 ID |
| since | str | 否 | 起始时间戳（ms） |

**返回值：** `list[Model.Schedule]` - 日程对象列表

```python
schedules = await bot.api.get_schedules("channel_id")
```

#### get_schedule(channel_id, schedule_id) -> Model.Schedule

获取日程详情。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| channel_id | str | 是 | 子频道 ID |
| schedule_id | str | 是 | 日程 ID |

**返回值：** `Model.Schedule` - 日程对象

```python
schedule = await bot.api.get_schedule("channel_id", "schedule_id")
```

#### create_schedule(channel_id, name, start_timestamp, end_timestamp, ...) -> Model.Schedule

创建日程。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| channel_id | str | 是 | 子频道 ID |
| name | str | 是 | 日程名称 |
| start_timestamp | str | 是 | 开始时间戳（ms） |
| end_timestamp | str | 是 | 结束时间戳（ms） |
| jump_channel_id | str | 否 | 开始时跳转到的子频道 ID |
| remind_type | str | 否 | 提醒类型，默认 "0" |
| description | str | 否 | 日程描述 |

**remind_type 值说明：**
- "0": 无提醒
- "1": 开始时提醒
- "2": 5分钟前
- "3": 15分钟前
- "4": 30分钟前
- "5": 60分钟前

**返回值：** `Model.Schedule` - 日程对象

```python
await bot.api.create_schedule(
    channel_id="channel_id",
    name="会议",
    start_timestamp="1640000000000",
    end_timestamp="1640003600000",
    remind_type="5",  # 60分钟前提醒
    description="项目讨论会议"
)
```

#### update_schedule(channel_id, schedule_id, ...) -> Model.Schedule

修改日程。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| channel_id | str | 是 | 子频道 ID |
| schedule_id | str | 是 | 日程 ID |
| name | str | 否 | 日程名称 |
| start_timestamp | str | 否 | 开始时间戳（ms） |
| end_timestamp | str | 否 | 结束时间戳（ms） |
| jump_channel_id | str | 否 | 开始时跳转到的子频道 ID |
| remind_type | str | 否 | 提醒类型 |
| description | str | 否 | 日程描述 |

**返回值：** `Model.Schedule` - 日程对象

```python
await bot.api.update_schedule(
    channel_id="channel_id",
    schedule_id="schedule_id",
    name="新名称"
)
```

#### delete_schedule(channel_id, schedule_id) -> bool

删除日程。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| channel_id | str | 是 | 子频道 ID |
| schedule_id | str | 是 | 日程 ID |

**返回值：** `bool` - 是否删除成功

```python
await bot.api.delete_schedule("channel_id", "schedule_id")
```

### 精华消息

#### get_pins(channel_id) -> Model.PinsMessage

获取精华消息。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| channel_id | str | 是 | 子频道 ID |

**返回值：** `Model.PinsMessage` - 精华消息对象

```python
pins = await bot.api.get_pins("channel_id")
```

#### add_pin(channel_id, message_id) -> Model.PinsMessage

添加精华消息。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| channel_id | str | 是 | 子频道 ID |
| message_id | str | 是 | 消息 ID |

**返回值：** `Model.PinsMessage` - 精华消息对象

```python
await bot.api.add_pin("channel_id", "message_id")
```

#### delete_pin(channel_id, message_id) -> bool

删除精华消息。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| channel_id | str | 是 | 子频道 ID |
| message_id | str | 是 | 消息 ID |

**返回值：** `bool` - 是否删除成功

```python
await bot.api.delete_pin("channel_id", "message_id")
```

### 表情表态

#### get_reaction_users(channel_id, message_id, emoji_type, emoji_id, cookie=None, limit=20) -> Model.ReactionUsers

获取表态用户列表。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| channel_id | str | 是 | 子频道 ID |
| message_id | str | 是 | 消息 ID |
| emoji_type | int | 是 | 表情类型（1=系统表情, 2=emoji） |
| emoji_id | str | 是 | 表情 ID |
| cookie | str | 否 | 分页 cookie |
| limit | int | 否 | 每页数量，默认 20 |

**返回值：** `Model.ReactionUsers` - 表情表态用户列表

```python
users = await bot.api.get_reaction_users(
    channel_id="channel_id",
    message_id="message_id",
    emoji_type=1,  # 1=系统表情, 2=emoji
    emoji_id="emoji_id"
)
```

#### create_reaction(channel_id, message_id, emoji_type, emoji_id) -> bool

发表表情表态。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| channel_id | str | 是 | 子频道 ID |
| message_id | str | 是 | 消息 ID |
| emoji_type | int | 是 | 表情类型（1=系统表情, 2=emoji） |
| emoji_id | str | 是 | 表情 ID |

**返回值：** `bool` - 是否操作成功

```python
await bot.api.create_reaction(
    channel_id="channel_id",
    message_id="message_id",
    emoji_type=1,
    emoji_id="emoji_id"
)
```

#### delete_reaction(channel_id, message_id, emoji_type, emoji_id) -> bool

删除表情表态。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| channel_id | str | 是 | 子频道 ID |
| message_id | str | 是 | 消息 ID |
| emoji_type | int | 是 | 表情类型（1=系统表情, 2=emoji） |
| emoji_id | str | 是 | 表情 ID |

**返回值：** `bool` - 是否操作成功

```python
await bot.api.delete_reaction(
    channel_id="channel_id",
    message_id="message_id",
    emoji_type=1,
    emoji_id="emoji_id"
)
```

### 音频控制

#### audio_control(channel_id, audio_url=None, text=None, status=0) -> bool

音频控制。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| channel_id | str | 是 | 子频道 ID |
| audio_url | str | 否 | 音频 URL |
| text | str | 否 | 状态文本 |
| status | int | 否 | 播放状态，默认 0 |

**status 值说明：**
- 0: 开始播放
- 1: 暂停
- 2: 继续
- 3: 停止

**返回值：** `bool` - 是否操作成功

```python
# 播放音频
await bot.api.audio_control(
    channel_id="channel_id",
    audio_url="https://example.com/audio.mp3",
    status=0
)

# 暂停
await bot.api.audio_control("channel_id", status=1)

# 继续
await bot.api.audio_control("channel_id", status=2)

# 停止
await bot.api.audio_control("channel_id", status=3)
```

#### mic_up(channel_id) -> bool

机器人上麦。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| channel_id | str | 是 | 子频道 ID |

**返回值：** `bool` - 是否上麦成功

```python
await bot.api.mic_up("channel_id")
```

#### mic_down(channel_id) -> bool

机器人下麦。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| channel_id | str | 是 | 子频道 ID |

**返回值：** `bool` - 是否下麦成功

```python
await bot.api.mic_down("channel_id")
```

### 论坛帖子

#### get_threads(channel_id) -> Model.ThreadListResult

获取帖子列表。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| channel_id | str | 是 | 子频道 ID（须为论坛子频道 type=10007） |

**返回值：** `Model.ThreadListResult` - 帖子列表结果，包含 threads 和 is_finish

```python
threads = await bot.api.get_threads("channel_id")
```

#### get_thread(channel_id, thread_id) -> Model.ThreadDetail

获取帖子详情。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| channel_id | str | 是 | 子频道 ID |
| thread_id | str | 是 | 帖子 ID |

**返回值：** `Model.ThreadDetail` - 帖子详情对象

```python
thread = await bot.api.get_thread("channel_id", "thread_id")
```

#### create_thread(channel_id, title, content, format=None) -> Model.CreateThreadResponse

发表帖子。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| channel_id | str | 是 | 子频道 ID（须为论坛子频道 type=10007） |
| title | str | 是 | 帖子标题 |
| content | str \| Model.ThreadContent | 是 | 帖子内容，支持字符串或 ThreadContent 对象 |
| format | int | 否 | 帖子格式（1=纯文本, 2=HTML, 3=Markdown, 4=JSON） |

**format 说明：**
- 当 content 为字符串时，默认为 3（Markdown）
- 当 content 为 ThreadContent 对象时，自动设为 4（JSON）

**返回值：** `Model.CreateThreadResponse` - 创建帖子响应，包含 task_id 和 create_time

```python
from easybot import Builders

# Markdown 格式发帖
await bot.api.create_thread("channel_id", "标题", "正文内容")

# JSON 格式发帖（使用构建器）
content = (Builders.ThreadContentBuilder()
    .add_text_paragraph("第一段文字")
    .add_image_paragraph("https://example.com/image.png")
    .add_text_paragraph("第二段文字", bold=True)
    .build())
await bot.api.create_thread("channel_id", "标题", content)
```

#### delete_thread(channel_id, thread_id) -> bool

删除帖子。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| channel_id | str | 是 | 子频道 ID |
| thread_id | str | 是 | 帖子 ID |

**返回值：** `bool` - 是否删除成功

```python
await bot.api.delete_thread("channel_id", "thread_id")
```

#### create_thread_comment(channel_id, thread_id, thread_author, content, thread_create_time=None, image=None) -> Model.CreateCommentResponse

发表评论。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| channel_id | str | 是 | 子频道 ID |
| thread_id | str | 是 | 帖子 ID |
| thread_author | str | 是 | 帖子作者 ID |
| content | str | 是 | 评论内容 |
| thread_create_time | str | 否 | 帖子创建时间 |
| image | str | 否 | 图片链接 |

**返回值：** `Model.CreateCommentResponse` - 创建评论响应，包含 task_id 和 create_time

```python
await bot.api.create_thread_comment(
    channel_id="channel_id",
    thread_id="thread_id",
    thread_author="author_id",
    content="评论内容"
)
```

### 互动事件

#### respond_interaction(interaction_id, code=0) -> bool

回应互动按钮点击事件。

**注意：** 由于 websocket 推送事件是单向的，开发者收到事件之后，需要进行一次"回应"，告知 QQ 后台事件已经收到。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| interaction_id | str | 是 | 互动事件 ID |
| code | int | 否 | 回应码，默认 0 |

**code 值说明：**
- 0: 成功
- 1: 操作失败
- 2: 操作频繁
- 3: 重复操作
- 4: 没有权限
- 5: 仅管理员操作

**返回值：** `bool` - 是否回应成功

```python
await bot.api.respond_interaction(
    interaction_id="interaction_id",
    code=0  # 0=成功
)
```

### Gateway

#### get_gateway() -> Model.GatewayResponse

获取 WSS 接入点。

**返回值：** `Model.GatewayResponse` - 包含 url 的响应

```python
gateway = await bot.api.get_gateway()
print(f"WSS URL: {gateway.url}")
```

#### get_gateway_bot() -> Model.GatewayBotResponse

获取带分片信息。

**返回值：** `Model.GatewayBotResponse` - 包含 url、shards 和 session_start_limit 的响应

```python
gateway_bot = await bot.api.get_gateway_bot()
print(f"URL: {gateway_bot.url}, Shards: {gateway_bot.shards}")
```

### 其他

#### generate_url_link(callback_data=None) -> Model.UrlLinkResponse

生成机器人分享链接。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| callback_data | str | 否 | 添加好友时会回传该参数给到开发者（最长32字符） |

**返回值：** `Model.UrlLinkResponse` - 包含 url 字段的响应

```python
link = await bot.api.generate_url_link(callback_data="source")
print(f"分享链接: {link.url}")
```

### 大文件分片上传

#### upload_large_file(file_path, file_type, user_openid=None, group_openid=None, concurrency=None) -> Model.FileInfo

一键上传大文件（推荐使用）。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file_path | str | 是 | 本地文件路径 |
| file_type | int | 是 | 文件类型：1=图片, 2=视频, 3=语音, 4=文件 |
| user_openid | str | 否 | 用户 openid（单聊场景） |
| group_openid | str | 否 | 群 openid（群聊场景） |
| concurrency | int | 否 | 并发上传数 |

**返回值：** `Model.FileInfo` - 包含 file_info 字段的响应

**文件大小限制：**
- 图片：10MB
- 视频：100MB
- 语音：10MB
- 文件：100MB

```python
# 一键上传视频
result = await bot.api.upload_large_file(
    file_path="./videos/large_video.mp4",
    file_type=2,
    user_openid="user_xxx",
)

# 使用 file_info 发送消息
await bot.api.send_c2c_message(
    openid="user_xxx",
    content="视频已上传",
    media_file_info=result.file_info,
)
```

#### upload_prepare(file_type, file_name, file_size, md5, sha1, md5_10m, user_openid=None, group_openid=None) -> Model.UploadPrepareResponse

申请大文件分片上传。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file_type | int | 是 | 文件类型：1=图片, 2=视频, 3=语音, 4=文件 |
| file_name | str | 是 | 文件名（包含扩展名） |
| file_size | int | 是 | 文件大小（字节） |
| md5 | str | 是 | 文件完整 MD5（十六进制） |
| sha1 | str | 是 | 文件完整 SHA1（十六进制） |
| md5_10m | str | 是 | 文件前 10002432 字节的 MD5 |
| user_openid | str | 否 | 用户 openid（单聊场景） |
| group_openid | str | 否 | 群 openid（群聊场景） |

**返回值：** `Model.UploadPrepareResponse` - 包含 upload_id、block_size、parts 的响应

```python
import hashlib

# 计算文件哈希
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
    file_type=2,
    file_name="large_file.mp4",
    file_size=len(file_data),
    md5=file_md5,
    sha1=file_sha1,
    md5_10m=md5_10m,
    user_openid="user_xxx",
)
```

#### upload_part(presigned_url, part_data, upload_id, part_index, user_openid=None, group_openid=None, retry_timeout=None) -> bool

上传单个分片（封装方法）。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| presigned_url | str | 是 | 预签名上传链接 |
| part_data | bytes | 是 | 分片数据 |
| upload_id | str | 是 | 上传任务 ID |
| part_index | int | 是 | 分片索引（从 1 开始） |
| user_openid | str | 否 | 用户 openid（单聊场景） |
| group_openid | str | 否 | 群 openid（群聊场景） |
| retry_timeout | int | 否 | 重试超时时间（秒） |

**返回值：** `bool` - 是否上传成功

```python
# 上传单个分片
offset = (part.index - 1) * prepare.block_size
chunk_data = file_data[offset:offset + prepare.block_size]

await bot.api.upload_part(
    presigned_url=part.presigned_url,
    part_data=chunk_data,
    upload_id=prepare.upload_id,
    part_index=part.index,
    user_openid="user_xxx",
)
```

#### upload_part_finish(upload_id, part_index, block_size, md5, user_openid=None, group_openid=None, retry_timeout=None) -> bool

完成分片通知（官方API）。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| upload_id | str | 是 | 上传任务 ID |
| part_index | int | 是 | 分片索引（从 1 开始） |
| block_size | int | 是 | 本分片大小（字节） |
| md5 | str | 是 | 本分片数据的 MD5（十六进制） |
| user_openid | str | 否 | 用户 openid（单聊场景） |
| group_openid | str | 否 | 群 openid（群聊场景） |
| retry_timeout | int | 否 | 重试超时时间（秒） |

**返回值：** `bool` - 是否通知成功

```python
# 通知平台分片完成
await bot.api.upload_part_finish(
    upload_id=upload_id,
    part_index=1,
    block_size=2000000,
    md5="chunk_md5_hex",
    user_openid="user_xxx",
)
```

#### upload_complete(upload_id, user_openid=None, group_openid=None) -> Model.FileInfo

完成大文件上传。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| upload_id | str | 是 | 上传任务 ID |
| user_openid | str | 否 | 用户 openid（单聊场景） |
| group_openid | str | 否 | 群 openid（群聊场景） |

**返回值：** `Model.FileInfo` - 包含 file_info 字段的响应

```python
# 完成上传
result = await bot.api.upload_complete(
    upload_id=prepare.upload_id,
    user_openid="user_xxx",
)

# 使用 file_info 发送消息
await bot.api.send_c2c_message(
    openid="user_xxx",
    content="文件已上传",
    media_file_info=result.file_info,
)
```
