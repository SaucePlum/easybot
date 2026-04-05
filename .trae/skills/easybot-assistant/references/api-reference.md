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

---

## 频道相关 API

### get_guild(guild_id: str) -> Model.Guild

获取频道详情。

```python
guild = await bot.api.get_guild("guild_id")
print(f"频道名称: {guild.name}")
```

### get_guild_list(before=None, after=None, limit=100) -> list[Model.Guild]

获取机器人所在频道列表。

```python
guilds = await bot.api.get_guild_list(limit=50)
for guild in guilds:
    print(f"{guild.id}: {guild.name}")
```

### get_me() -> Model.Author

获取当前机器人信息。

```python
me = await bot.api.get_me()
print(f"机器人ID: {me.id}, 名称: {me.username}")
```

---

## 子频道相关 API

### get_guild_channels(guild_id: str) -> list[Model.Channel]

获取频道子频道列表。

```python
channels = await bot.api.get_guild_channels("guild_id")
for ch in channels:
    print(f"{ch.id}: {ch.name} (type={ch.type})")
```

### get_channel(channel_id: str) -> Model.Channel

获取子频道详情。

```python
channel = await bot.api.get_channel("channel_id")
```

### create_channel(...) -> Model.Channel

创建子频道。

```python
channel = await bot.api.create_channel(
    guild_id="guild_id",
    name="新子频道",
    channel_type=0,  # 0=文字, 2=语音, 4=分类
    position=1,
)
```

### update_channel(...) -> Model.Channel

修改子频道。

```python
channel = await bot.api.update_channel(
    channel_id="channel_id",
    name="新名称",
)
```

### delete_channel(channel_id: str) -> bool

删除子频道。

```python
await bot.api.delete_channel("channel_id")
```

---

## 消息相关 API

### send_guild_message(...) -> Model.GuildMessage

发送频道消息。

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
```

### get_guild_message(channel_id, message_id) -> Model.GuildMessage

获取指定消息。

```python
msg = await bot.api.get_guild_message("channel_id", "message_id")
```

### recall_guild_message(channel_id, message_id, hidetip=False) -> bool

撤回频道消息。

```python
await bot.api.recall_guild_message("channel_id", "message_id")
```

### patch_guild_message(...) -> Model.GuildMessage

修改频道 Markdown 消息。

```python
await bot.api.patch_guild_message(
    channel_id="channel_id",
    patch_msg_id="message_id",
    content=MessagesModel.MessageMarkdown(content="# 更新后的标题")
)
```

---

## 群聊相关 API

### send_group_message(...) -> Model.GroupSendMessageResponse

发送群聊消息。

```python
# 文本消息
msg = await bot.api.send_group_message(
    group_openid="group_openid",
    content="Hello!",
    event_id="event_id",  # 被动消息需要
)

# Markdown 消息
msg = await bot.api.send_group_message(
    group_openid="group_openid",
    content=MessagesModel.MessageMarkdown(content="# 标题"),
    event_id="event_id",
)
```

**注意：** 群聊消息必须有文本内容，纯图片/富媒体需要配合文本使用。

### recall_group_message(group_openid, message_id) -> bool

撤回群聊消息。

```python
await bot.api.recall_group_message("group_openid", "message_id")
```

---

## 单聊相关 API

### send_c2c_message(...) -> Model.C2CSendMessageResponse

发送单聊消息。

```python
msg = await bot.api.send_c2c_message(
    openid="user_openid",
    content="Hello!",
    event_id="event_id",
)
```

### recall_c2c_message(openid, message_id) -> bool

撤回单聊消息。

```python
await bot.api.recall_c2c_message("openid", "message_id")
```

### send_c2c_stream_message(...) -> Model.StreamMessageResponse

发送流式消息（AI 对话场景）。

```python
# 首次发送
resp = await bot.api.send_c2c_stream_message(
    openid="openid",
    content_raw="正在生成...",
    event_id="event_id",
    msg_id="msg_id",
    msg_seq=0,
    index=0,
    input_state=1,  # 1=生成中, 10=结束
)
stream_msg_id = resp.id

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

---

## 私信相关 API

### create_dms(recipient_id, source_guild_id) -> Model.DMS

创建私信会话。

```python
dms = await bot.api.create_dms(
    recipient_id="user_id",
    source_guild_id="guild_id"
)
# 使用 dms.guild_id 发送私信
```

### send_direct_message(...) -> Model.GuildMessage

发送频道私信消息。

```python
msg = await bot.api.send_direct_message(
    guild_id="dms_guild_id",
    content="私信内容",
)
```

### recall_direct_message(guild_id, message_id, hidetip=False) -> bool

撤回频道私信消息。

```python
await bot.api.recall_direct_message("guild_id", "message_id")
```

---

## 成员管理 API

### get_guild_members(guild_id, after="0", limit=100) -> list[Model.Member]

获取频道成员列表。

```python
members = await bot.api.get_guild_members("guild_id", limit=100)
```

### get_guild_member(guild_id, user_id) -> Model.Member

获取频道成员详情。

```python
member = await bot.api.get_guild_member("guild_id", "user_id")
```

### delete_guild_member(guild_id, user_id, add_blacklist=False, delete_history_msg_days=0) -> bool

删除频道成员（踢人）。

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

```python
result = await bot.api.get_channel_online_nums("channel_id")
print(f"在线人数: {result.online_nums}")
```

---

## 身份组管理 API

### get_guild_roles(guild_id) -> Model.GuildRolesResponse

获取频道身份组列表。

```python
result = await bot.api.get_guild_roles("guild_id")
for role in result.roles:
    print(f"{role.id}: {role.name}")
```

### create_guild_role(guild_id, name, color=0, hoist=0) -> Model.CreateRoleResponse

创建频道身份组。

```python
result = await bot.api.create_guild_role(
    guild_id="guild_id",
    name="新身份组",
    color=0xFF0000,
)
```

### update_guild_role(guild_id, role_id, ...) -> Model.CreateRoleResponse

修改频道身份组。

```python
await bot.api.update_guild_role(
    guild_id="guild_id",
    role_id="role_id",
    name="新名称",
)
```

### delete_guild_role(guild_id, role_id) -> bool

删除频道身份组。

```python
await bot.api.delete_guild_role("guild_id", "role_id")
```

### add_guild_member_role(guild_id, user_id, role_id, channel_id=None) -> bool

添加成员到身份组。

```python
await bot.api.add_guild_member_role(
    guild_id="guild_id",
    user_id="user_id",
    role_id="role_id",
)
```

### remove_guild_member_role(guild_id, user_id, role_id, channel_id=None) -> bool

从身份组移除成员。

```python
await bot.api.remove_guild_member_role(
    guild_id="guild_id",
    user_id="user_id",
    role_id="role_id",
)
```

### get_guild_role_members(guild_id, role_id, ...) -> Model.RoleMembersResponse

获取身份组成员列表。

```python
result = await bot.api.get_guild_role_members("guild_id", "role_id")
```

---

## 权限管理 API

### 禁言相关

```python
# 频道全员禁言
await bot.api.mute_guild(guild_id="guild_id", mute_seconds=3600)

# 指定成员禁言
await bot.api.mute_guild_member(
    guild_id="guild_id",
    user_id="user_id",
    mute_seconds=3600
)

# 批量禁言
result = await bot.api.mute_guild_members(
    guild_id="guild_id",
    user_ids=["user_id1", "user_id2"],
    mute_seconds=3600
)

# 取消全员禁言
await bot.api.cancel_mute_all("guild_id")

# 取消批量禁言
await bot.api.cancel_mute_multi_member("guild_id", ["user_id1"])
```

### 子频道权限

```python
# 获取用户权限
perms = await bot.api.get_channel_user_permissions("channel_id", "user_id")

# 获取身份组权限
perms = await bot.api.get_channel_role_permissions("channel_id", "role_id")

# 修改用户权限
await bot.api.update_channel_user_permissions(
    channel_id="channel_id",
    user_id="user_id",
    add="4",  # 添加查看权限
    remove="1"  # 移除发言权限
)

# 修改身份组权限
await bot.api.update_channel_role_permissions(
    channel_id="channel_id",
    role_id="role_id",
    add="4",
)
```

### API 权限

```python
# 获取机器人可用权限
result = await bot.api.get_guild_api_permissions("guild_id")

# 发送权限授权链接
await bot.api.demand_guild_api_permission(
    guild_id="guild_id",
    channel_id="channel_id",
    api_path="/path",
    api_method="GET",
    desc="功能描述"
)
```

---

## 其他 API

### 公告管理

```python
# 创建公告
await bot.api.create_announces(
    guild_id="guild_id",
    message_id="message_id",
    channel_id="channel_id"
)

# 删除公告
await bot.api.delete_announces("guild_id", "message_id")
# 删除全部公告
await bot.api.delete_announces("guild_id", "all")
```

### 日程管理

```python
# 获取日程列表
schedules = await bot.api.get_schedules("channel_id")

# 创建日程
await bot.api.create_schedule(
    channel_id="channel_id",
    name="会议",
    start_timestamp="1640000000000",
    end_timestamp="1640003600000",
    remind_type="5"  # 60分钟前提醒
)

# 修改日程
await bot.api.update_schedule(
    channel_id="channel_id",
    schedule_id="schedule_id",
    name="新名称"
)

# 删除日程
await bot.api.delete_schedule("channel_id", "schedule_id")
```

### 精华消息

```python
# 获取精华消息
pins = await bot.api.get_pins("channel_id")

# 添加精华消息
await bot.api.add_pin("channel_id", "message_id")

# 删除精华消息
await bot.api.delete_pin("channel_id", "message_id")
```

### 表情表态

```python
# 获取表态用户列表
users = await bot.api.get_reaction_users(
    channel_id="channel_id",
    message_id="message_id",
    emoji_type=1,  # 1=系统表情, 2=emoji
    emoji_id="emoji_id"
)

# 发表表情表态
await bot.api.create_reaction(
    channel_id="channel_id",
    message_id="message_id",
    emoji_type=1,
    emoji_id="emoji_id"
)

# 删除表情表态
await bot.api.delete_reaction(
    channel_id="channel_id",
    message_id="message_id",
    emoji_type=1,
    emoji_id="emoji_id"
)
```

### 音频控制

```python
# 播放音频
await bot.api.audio_control(
    channel_id="channel_id",
    audio_url="https://example.com/audio.mp3",
    status=0  # 0=开始
)

# 暂停
await bot.api.audio_control("channel_id", status=1)

# 继续
await bot.api.audio_control("channel_id", status=2)

# 停止
await bot.api.audio_control("channel_id", status=3)

# 上麦
await bot.api.mic_up("channel_id")

# 下麦
await bot.api.mic_down("channel_id")
```

### 论坛帖子

```python
from easybot import Builders

# 获取帖子列表
threads = await bot.api.get_threads("channel_id")

# 获取帖子详情
thread = await bot.api.get_thread("channel_id", "thread_id")

# 发表帖子（Markdown 格式）
await bot.api.create_thread(
    channel_id="channel_id",
    title="标题",
    content="内容"
)

# 发表帖子（JSON 格式，使用构建器）
content = (Builders.ThreadContentBuilder()
    .add_text_paragraph("第一段文字")
    .add_image_paragraph("https://example.com/image.png")
    .add_text_paragraph("第二段文字", bold=True)
    .build())
await bot.api.create_thread("channel_id", "标题", content)

# 删除帖子
await bot.api.delete_thread("channel_id", "thread_id")

# 发表评论
await bot.api.create_thread_comment(
    channel_id="channel_id",
    thread_id="thread_id",
    thread_author="author_id",
    content="评论内容"
)
```

### 互动事件

```python
# 回应互动按钮点击
await bot.api.respond_interaction(
    interaction_id="interaction_id",
    code=0  # 0=成功
)
```

### 富媒体上传

```python
# 上传图片
result = await bot.api.upload_media(
    file_type=1,  # 1=图片, 2=视频, 3=语音, 4=文件
    file_data="./image.png",
    user_openid="openid"
)

# 发送富媒体消息
msg = MessagesModel.Message(
    content="图片消息",
    media_file_info=result.file_info
)
await bot.api.send_c2c_message(
    openid="openid",
    content=msg,
    event_id="event_id"
)
```

### Gateway

```python
# 获取 WSS 接入点
gateway = await bot.api.get_gateway()
print(f"WSS URL: {gateway.url}")

# 获取带分片信息
gateway_bot = await bot.api.get_gateway_bot()
print(f"URL: {gateway_bot.url}, Shards: {gateway_bot.shards}")
```

### 其他

```python
# 获取消息频率设置
setting = await bot.api.get_guild_message_setting("guild_id")

# 生成机器人分享链接
link = await bot.api.generate_url_link(callback_data="source")
print(f"分享链接: {link.url}")
```
