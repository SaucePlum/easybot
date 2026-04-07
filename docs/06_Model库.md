# Model 库 — 数据模型

本章介绍 EasyBot SDK 中的数据模型，用于表示 API 返回值和事件数据。

---

## 一、概述

**模块**: `easybot.models`  
**导入**: `from easybot import Model`  
**使用**: `Model.GuildMessage`、`Model.Author`、`Model.Guild` 等

所有模型继承自 `BaseModel`，基于 Python `dataclass` 实现。

### 1.1 通用方法

| 方法 | 说明 |
|------|------|
| `from_dict(data: dict)` | 类方法，从字典创建模型实例 |
| `to_dict()` | 将模型实例转换为字典（用于序列化） |
| `reply(content, reference=False)` | 快速回复消息（仅消息事件模型） |

### 1.2 通用属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `event_id` | `str` | 事件 ID |
| `seq` | `int \| None` | 事件序号 |
| `opcode` | `int` | 操作码 |
| `event_type` | `str` | 事件类型名称 |
| `_raw_data` | `dict \| None` | 原始 API 响应数据 |

### 1.3 类型注解获得 IDE 支持

```python
from easybot import Bot, Model

@bot.on_guild_message
async def handle(msg: Model.GuildMessage):
    print(msg.channel_id)        # IDE 自动补全
    print(msg.author.username)   # IDE 自动补全
```

---

## 二、用户相关模型

### 2.1 Author — 统一作者模型

表示用户信息，适用于频道、群聊、单聊等多种场景。

```python
@dataclass
class Author(BaseModel):
    id: str = ""                          # 用户 ID
    username: str = ""                     # 用户名
    avatar: str = ""                       # 头像 URL
    bot: bool = False                      # 是否机器人
    member_openid: str | None = None       # 频道成员 openid
    user_openid: str | None = None         # QQ 用户 openid
    union_openid: str | None = None        # Union openid
```

### 2.2 Member — 频道成员

```python
@dataclass
class Member(BaseModel):
    user: Author | None = None             # 用户信息
    nick: str = ""                         # 昵称
    roles: list[str] = []                  # 身份组 ID 列表
    joined_at: str = ""                    # 加入时间
```

---

## 三、频道相关模型

### 3.1 Guild — 频道对象

```python
@dataclass
class Guild(BaseModel):
    id: str = ""                           # 频道 ID
    name: str = ""                         # 频道名称
    icon: str = ""                         # 频道图标
    owner_id: str = ""                     # 创建者 ID
    owner: bool = False                    # 是否创建者
    member_count: int = 0                  # 成员数量
    max_members: int = 0                   # 最大成员数
    description: str = ""                  # 频道描述
    joined_at: str = ""                    # 机器人加入时间
```

### 3.2 Channel — 子频道对象

```python
@dataclass
class Channel(BaseModel):
    id: str = ""                           # 子频道 ID
    guild_id: str = ""                     # 所属频道 ID
    name: str = ""                         # 子频道名称
    type: int = 0                          # 类型
    sub_type: int = 0                      # 子类型
    position: int = 0                      # 排序位置
    parent_id: str = ""                    # 所属分组 ID

    # 类型常量
    TYPE_TEXT: ClassVar[int] = 0           # 文字频道
    TYPE_VOICE: ClassVar[int] = 2          # 语音频道
    TYPE_CATEGORY: ClassVar[int] = 4       # 分组
    TYPE_LIVE: ClassVar[int] = 10005       # 直播频道
    TYPE_APP: ClassVar[int] = 10006        # 应用频道
    TYPE_FORUM: ClassVar[int] = 10007      # 论坛频道
```

---

## 四、消息相关模型

### 4.1 MessageBase — 消息基础模型

所有消息模型的公共基类。

```python
@dataclass
class MessageBase(BaseModel):
    id: str = ""                           # 消息 ID
    content: str = ""                      # 消息文本
    timestamp: str = ""                    # 发送时间戳
    author: Author | None = None           # 发送者信息
    attachments: list[Attachment] = []     # 附件列表

    @property
    def msg_id(self) -> str:
        return self.id
```

### 4.2 GuildMessage — 频道消息

频道内发送和接收的消息。

```python
@dataclass
class GuildMessage(MessageBase):
    channel_id: str = ""                   # 子频道 ID
    guild_id: str = ""                     # 频道 ID
    edited_timestamp: str | None = None    # 编辑时间
    member: Member | None = None           # 发送者成员信息
    seq_in_channel: str | None = None      # 频道内序号
```

**reply() 方法**：

```python
await msg.reply("收到！")                              # 文本回复
await msg.reply(MessagesModel.MessageEmbed(title="标题"))  # Embed 回复
await msg.reply("引用你", reference=True)                 # 引用回复
```

### 4.3 GroupMessage — 群聊消息

```python
@dataclass
class GroupMessage(MessageBase):
    group_openid: str = ""                 # 群 openid
```

### 4.4 C2CMessage — 单聊消息

继承自 `MessageBase`。

### 4.5 DirectMessage — 频道私信消息

```python
@dataclass
class DirectMessage(MessageBase):
    channel_id: str = ""                   # 私信频道 ID
    guild_id: str = ""                     # 来源频道 ID
    member: Member | None = None           # 成员信息
```

### 4.6 Attachment — 消息附件

```python
@dataclass
class Attachment(BaseModel):
    url: str = ""                          # 附件 URL
    content_type: str | None = None        # MIME 类型
    filename: str | None = None            # 文件名
    height: int | None = None              # 高度（图片）
    width: int | None = None               # 宽度（图片）
    size: int | None = None                # 文件大小
```

---

## 五、事件相关模型

### 5.1 Interaction — 互动按钮回调事件

```python
@dataclass
class Interaction(BaseModel):
    id: str = ""                           # 交互 ID
    type: int = 0                          # 交互类型 (11=按钮 12=菜单)
    guild_id: str | None = None
    channel_id: str | None = None
    user_openid: str | None = None
    data: InteractionData | None = None    # 交互数据
```

### 5.2 AudioAction — 音频事件

```python
@dataclass
class AudioAction(BaseModel):
    guild_id: str = ""
    channel_id: str = ""
    audio_url: str = ""                    # 音频 URL
    text: str = ""                         # TTS 文本
```

### 5.3 MessageReaction — 表情表态事件

```python
@dataclass
class MessageReaction(BaseModel):
    user_id: str = ""                      # 操作用户 ID
    guild_id: str = ""
    channel_id: str = ""
    target: ReactionTarget | None = None   # 表态目标
    emoji: Emoji | None = None             # 表情
```

### 5.4 MessageDelete — 消息删除事件

```python
@dataclass
class MessageDelete(BaseModel):
    message: GuildMessage | None = None    # 被删除的消息
    op_user: Author | None = None          # 操作者
```

### 5.5 MessageAudited — 消息审核事件

```python
@dataclass
class MessageAudited(BaseModel):
    audit_id: str = ""                     # 审核 ID
    message_id: str = ""                   # 消息 ID
    guild_id: str = ""
    channel_id: str = ""
    audit_time: str = ""                   # 审核时间
```

### 5.6 LiveChannelMember — 音视频频道进出事件

```python
@dataclass
class LiveChannelMember(BaseModel):
    guild_id: str = ""
    channel_id: str = ""
    channel_type: int = 0                  # 2=音频 4=直播
    user_id: str = ""
```

---

## 六、论坛相关模型

论坛子频道的 `Channel.type` 为 `10007`。

### 6.1 Thread — 帖子对象

```python
@dataclass
class Thread(BaseModel):
    guild_id: str = ""                     # 频道 ID
    channel_id: str = ""                   # 子频道 ID
    author_id: str = ""                    # 作者 ID
    thread_info: ThreadInfo | None = None  # 帖子信息
```

### 6.2 ThreadInfo — 帖子信息

```python
@dataclass
class ThreadInfo(BaseModel):
    thread_id: str = ""                    # 帖子 ID
    title: str = ""                        # 帖子标题
    content: str = ""                      # 帖子内容（JSON 字符串）
    date_time: str = ""                    # 创建时间
```

**解析帖子内容**：

```python
import json
from easybot import Model

content_dict = json.loads(thread.thread_info.content)
content = Model.ThreadContent.from_dict(content_dict)
```

### 6.3 Post — 评论对象（事件）

```python
@dataclass
class Post(BaseModel):
    guild_id: str = ""
    channel_id: str = ""
    author_id: str = ""
    post_info: PostInfo | None = None
```

### 6.4 Reply — 回复对象（事件）

```python
@dataclass
class Reply(BaseModel):
    guild_id: str = ""
    channel_id: str = ""
    author_id: str = ""
    reply_info: ReplyInfo | None = None
```

### 6.5 AuditResult — 审核结果

```python
@dataclass
class AuditResult(BaseModel):
    guild_id: str = ""
    channel_id: str = ""
    author_id: str = ""
    thread_id: str = ""
    post_id: str = ""
    reply_id: str = ""
    type: int = 0                          # AuditType 审核类型
    result: int = 0                        # 0=通过 1=拒绝
    err_msg: str = ""                      # 错误信息
```

### 6.6 AuditType — 审核类型枚举

```python
class AuditType(IntEnum):
    PUBLISH_THREAD = 1                     # 帖子
    PUBLISH_POST = 2                       # 评论
    PUBLISH_REPLY = 3                      # 回复
```

---

## 七、群聊/好友事件模型

### 7.1 GroupEvent — 群聊事件

```python
@dataclass
class GroupEvent(BaseModel):
    timestamp: int = 0
    group_openid: str = ""
    op_member_openid: str = ""
```

### 7.2 FriendEvent — 好友事件

```python
@dataclass
class FriendEvent(BaseModel):
    timestamp: int = 0
    openid: str = ""
```

---

## 八、Gateway 协议模型

### 8.1 OpCode — 操作码枚举

WebSocket/Webhook 传输数据的操作类型标识。

```python
class OpCode(IntEnum):
    DISPATCH = 0            # 事件分发
    HEARTBEAT = 1           # 心跳请求
    IDENTIFY = 2            # 身份验证
    RESUME = 6              # 恢复连接
    RECONNECT = 7           # 服务器要求重连
    INVALID_SESSION = 9     # 无效会话
    HELLO = 10              # 服务器欢迎消息
    HEARTBEAT_ACK = 11      # 心跳确认
```

### 8.2 Payload — Gateway 数据结构

Webhook 或 WebSocket 连接上传输的统一数据结构。

```python
@dataclass
class Payload(BaseModel):
    id: str = ""                           # 事件 ID
    op: int = 0                             # 操作码
    d: dict[str, Any]                       # 事件数据
    s: int | None = None                    # 事件序号
    t: str | None = None                    # 事件类型名称
```

**使用示例**：

```python
@bot.on_all_intent_events
async def handle_event(event):
    if event.opcode == Model.OpCode.DISPATCH:
        print(f"事件类型: {event.event_type}")
```

---

## 九、API 响应模型

### 9.1 常用响应模型

| 模型 | 说明 |
|------|------|
| `OnlineNumsResponse` | 在线人数 |
| `GuildRolesResponse` | 身份组列表 |
| `CreateRoleResponse` | 创建身份组结果 |
| `RoleMembersResponse` | 身份组成员 |
| `MuteBatchResponse` | 批量禁言结果 |
| `ChannelPermissions` | 子频道权限 |
| `DMS` | 私信会话 |

### 9.2 示例

```python
# 获取在线人数
online_nums = await bot.api.get_guild_online_nums(guild_id)
print(f"在线人数: {online_nums.online_nums}")

# 获取身份组列表
roles = await bot.api.get_guild_roles(guild_id)
print(f"身份组数量: {len(roles.roles)}")
```

---

## 十、使用技巧

### 10.1 安全访问可选字段

```python
@bot.on_guild_message
async def handle(msg: Model.GuildMessage):
    username = msg.author.username if msg.author else "未知"
    roles = msg.member.roles if msg.member else []
```

### 10.2 访问原始数据

```python
@bot.on_guild_message
async def handle(msg: Model.GuildMessage):
    if msg._raw_data:
        print("原始数据:", msg._raw_data)
```

### 10.3 模型序列化

```python
@bot.on_guild_message
async def handle(msg: Model.GuildMessage):
    data = msg.to_dict()  # 转换为字典
    print(data)
```

---

## 十一、下一步

- [插件与权限](./07_插件与权限.md) — 学习插件开发和命令注册
- [API 参考](./04_API参考.md) — 查看完整的 API 方法列表
