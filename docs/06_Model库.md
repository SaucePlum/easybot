# Model 库 — 数据模型参考

Model 库定义 EasyBot SDK 中所有数据对象的类型结构，基于 Python `dataclass` 实现，用于表示 API 返回值和事件数据。

> **导入**: `from easybot import Model`
> **使用**: `Model.GuildMessage`、`Model.Author`、`Model.Guild` 等

---

## 模型基类

所有模型继承自 `BaseModel`，提供通用能力。

### 通用方法

| 方法 | 说明 |
|------|------|
| `from_dict(data: dict)` | 类方法，从字典创建模型实例 |
| `to_dict()` | 将模型实例转换为字典（用于序列化） |
| `reply(content, reference=False)` | 快速回复消息（仅消息事件模型） |

### 通用属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `event_id` | `str` | 事件 ID |
| `seq` | `int \| None` | 事件序号 |
| `opcode` | `int` | 操作码（见 OpCode 枚举） |
| `event_type` | `str` | 事件类型名称 |
| `_raw_data` | `dict \| None` | 原始 API 响应数据 |

### from_dict 行为

- 只提取模型定义的字段，忽略多余字段
- 缺失的可选字段使用 dataclass 默认值
- `_raw_data` 始终保留原始完整响应

---

## Gateway 协议模型

### OpCode 操作码枚举

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

### Payload Gateway 数据结构

Webhook 或 WebSocket 连接上传输的统一数据结构。

```python
@dataclass
class Payload(BaseModel):
    id: str = ""                           # 事件 ID
    op: int = 0                             # 操作码
    d: dict[str, Any]                       # 事件数据
    s: Optional[int] = None                 # 事件序号
    t: Optional[str] = None                 # 事件类型名称
```

**类方法**:

| 方法 | 说明 |
|------|------|
| `from_dict(data: dict)` | 从字典创建 Payload 实例 |
| `is_dispatch()` | 是否为 Dispatch 事件（op=0） |

**使用示例**:

```python
@bot.on_all_intent_events
async def handle_event(event):
    if event.opcode == Model.OpCode.DISPATCH:
        print(f"事件类型: {event.event_type}")
```

---

## 用户相关模型

### Author 统一作者模型

表示用户信息，适用于频道、群聊、单聊等多种场景。

```python
@dataclass
class Author(BaseModel):
    id: str = ""                          # 用户 ID
    username: str = ""                     # 用户名
    avatar: str = ""                       # 头像 URL
    bot: bool = False                      # 是否机器人
    member_openid: Optional[str] = None    # 频道成员 openid
    user_openid: Optional[str] = None      # QQ 用户 openid
    union_openid: Optional[str] = None     # Union openid
```

### Member 频道成员

```python
@dataclass
class Member(BaseModel):
    user: Author | None = None             # 用户信息
    nick: str = ""                         # 昵称
    roles: list[str] = []                  # 身份组 ID 列表
    joined_at: str = ""                    # 加入时间
```

### MemberWithGuildID 带频道 ID 的成员

成员变更事件中使用，额外包含频道 ID。

```python
@dataclass
class MemberWithGuildID(Member):
    guild_id: str = ""                     # 频道 ID
    op_user_id: str | None = None          # 操作者 ID
```

---

## 频道相关模型

### Guild 频道对象

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

### Channel 子频道对象

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

## 消息相关模型

### MessageBase 消息基础模型

所有消息模型的公共基类。

```python
@dataclass
class MessageBase(BaseModel):
    id: str = ""                           # 消息 ID
    content: str = ""                      # 消息文本
    timestamp: str = ""                    # 发送时间戳
    author: Optional[Author] = None        # 发送者信息
    attachments: list[Attachment] = []     # 附件列表
    treated_msg: str = ""                  # 处理后的消息

    @property
    def msg_id(self) -> str:
        return self.id
```

### GuildMessage 频道消息

频道内发送和接收的消息。

```python
@dataclass
class GuildMessage(MessageBase):
    channel_id: str = ""                   # 子频道 ID
    guild_id: str = ""                     # 频道 ID
    edited_timestamp: Optional[str] = None # 编辑时间
    member: Optional[Member] = None        # 发送者成员信息
    seq_in_channel: Optional[str] = None   # 频道内序号
```

**reply() 方法**:

```python
await msg.reply("收到！")                              # 文本回复
await msg.reply(MessagesModel.MessageEmbed(title="标题"))  # Embed 回复
await msg.reply("引用你", reference=True)                 # 引用回复
```

### GroupMessage 群聊消息

```python
@dataclass
class GroupMessage(MessageBase):
    group_openid: str = ""                 # 群 openid
```

### C2CMessage 单聊消息

继承自 `MessageBase`。

### DirectMessage 频道私信消息

```python
@dataclass
class DirectMessage(MessageBase):
    channel_id: str = ""                   # 私信频道 ID
    guild_id: str = ""                     # 来源频道 ID
    member: Optional[Member] = None        # 成员信息
```

### Attachment 消息附件

```python
@dataclass
class Attachment(BaseModel):
    url: str = ""                          # 附件 URL
    content_type: Optional[str] = None     # MIME 类型
    filename: Optional[str] = None         # 文件名
    height: Optional[int] = None            # 高度（图片）
    width: Optional[int] = None            # 宽度（图片）
    size: Optional[int] = None             # 文件大小
```

---

## 消息构建器模型

消息构建器用于构造发送消息时的内容参数。

### MessageEmbed Ark/Embed 对象

```python
@dataclass
class MessageEmbed(BaseModel):
    title: str = ""                        # 标题
    prompt: str = ""                       # 提示文本
    thumbnail: Optional[MessageEmbedThumbnail] = None  # 缩略图
    fields: list[MessageEmbedField] = []   # 字段列表
```

### MessageArk Ark 模板对象

```python
@dataclass
class MessageArk(BaseModel):
    template_id: int = 0                   # 模板 ID
    kv: list[MessageArkKv] = []            # KV 列表
```

### MessageMarkdown Markdown 对象

```python
@dataclass
class MessageMarkdown(BaseModel):
    template_id: int | None = None         # 模板 ID
    content: str | None = None             # 原生内容
```

### StreamInputState 流式消息状态

```python
class StreamInputState:
    GENERATING = 1   # 正文中
    DONE = 10        # 结束
```

---

## 事件相关模型

### MessageDelete 消息删除事件

```python
@dataclass
class MessageDelete(BaseModel):
    message: Optional[GuildMessage] = None # 被删除的消息
    op_user: Optional[Author] = None       # 操作者
```

### MessageAudited 消息审核事件

```python
@dataclass
class MessageAudited(BaseModel):
    audit_id: str = ""                     # 审核 ID
    message_id: str = ""                   # 消息 ID
    guild_id: str = ""
    channel_id: str = ""
    audit_time: str = ""                   # 审核时间
```

### MessageReaction 表情表态事件

```python
@dataclass
class MessageReaction(BaseModel):
    user_id: str = ""                      # 操作用户 ID
    guild_id: str = ""
    channel_id: str = ""
    target: Optional[ReactionTarget] = None # 表态目标
    emoji: Optional[Emoji] = None          # 表情
```

### Interaction 互动按钮回调事件

```python
@dataclass
class Interaction(BaseModel):
    id: str = ""                           # 交互 ID
    type: int = 0                          # 交互类型 (11=按钮 12=菜单)
    guild_id: Optional[str] = None
    channel_id: Optional[str] = None
    user_openid: Optional[str] = None
    data: Optional[InteractionData] = None # 交互数据
```

### AudioAction 音频事件

```python
@dataclass
class AudioAction(BaseModel):
    guild_id: str = ""
    channel_id: str = ""
    audio_url: str = ""                     # 音频 URL
    text: str = ""                         # TTS 文本
```

### LiveChannelMember 音视频频道进出事件

```python
@dataclass
class LiveChannelMember(BaseModel):
    guild_id: str = ""
    channel_id: str = ""
    channel_type: int = 0                  # 2=音频 4=直播
    user_id: str = ""
```

### 论坛相关模型

论坛子频道的 `Channel.type` 为 `10007`。

#### Thread 帖子对象

```python
@dataclass
class Thread(BaseModel):
    guild_id: str = ""                     # 频道 ID
    channel_id: str = ""                   # 子频道 ID
    author_id: str = ""                    # 作者 ID
    thread_info: Optional[ThreadInfo] = None  # 帖子信息
```

#### ThreadInfo 帖子信息

```python
@dataclass
class ThreadInfo(BaseModel):
    thread_id: str = ""                    # 帖子 ID
    title: str = ""                        # 帖子标题
    content: str = ""                      # 帖子内容（JSON 字符串）
    date_time: str = ""                    # 创建时间
```

**解析帖子内容示例**:

```python
import json
from easybot import Model

content_dict = json.loads(thread.thread_info.content)
content = Model.ThreadContent.from_dict(content_dict)
```

#### Post 评论对象（事件）

```python
@dataclass
class Post(BaseModel):
    guild_id: str = ""
    channel_id: str = ""
    author_id: str = ""
    post_info: Optional[PostInfo] = None
```

#### Reply 回复对象（事件）

```python
@dataclass
class Reply(BaseModel):
    guild_id: str = ""
    channel_id: str = ""
    author_id: str = ""
    reply_info: Optional[ReplyInfo] = None
```

#### AuditResult 审核结果

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

#### AuditType 审核类型枚举

```python
class AuditType(IntEnum):
    PUBLISH_THREAD = 1                     # 帖子
    PUBLISH_POST = 2                       # 评论
    PUBLISH_REPLY = 3                      # 回复
```

#### ThreadContent 帖子内容

```python
@dataclass
class ThreadContent(BaseModel):
    paragraphs: list[ThreadContentParagraph] = []  # 段落列表
```

**解析帖子内容示例**:

```python
import json
from easybot import Model

content_dict = json.loads(thread.thread_info.content)
content = Model.ThreadContent.from_dict(content_dict)
```

**构建帖子内容示例**（用于发帖）:

```python
from easybot import Builders

content = (Builders.ThreadContentBuilder()
    .add_text_paragraph("第一段文字")
    .add_image_paragraph("https://example.com/image.png")
    .build())

await bot.api.create_thread(channel_id="xxx", title="标题", content=content)
```

#### ThreadContentParagraph 段落

```python
@dataclass
class ThreadContentParagraph(BaseModel):
    elems: list[ThreadContentElem] = []    # 元素列表
    props: Optional[ParagraphProps] = None  # 段落属性
```

#### ThreadContentElem 元素

```python
@dataclass
class ThreadContentElem(BaseModel):
    type: int = 1                          # 元素类型
    text: Optional[ThreadContentText] = None
    image: Optional[ThreadContentImage] = None
    video: Optional[ThreadContentVideo] = None
    url: Optional[ThreadContentUrl] = None

    TYPE_TEXT: ClassVar[int] = 1           # 文本
    TYPE_IMAGE: ClassVar[int] = 2          # 图片
    TYPE_VIDEO: ClassVar[int] = 3          # 视频
    TYPE_URL: ClassVar[int] = 4            # 链接
```

#### ThreadContentText 文本元素

```python
@dataclass
class ThreadContentText(BaseModel):
    text: str = ""
    props: Optional[TextProps] = None      # 文本属性
```

#### ThreadContentImage 图片元素

```python
@dataclass
class ThreadContentImage(BaseModel):
    third_url: str = ""                    # 第三方图片链接
    width_percent: float = 0.0             # 宽度比例
```

#### ThreadContentVideo 视频元素

```python
@dataclass
class ThreadContentVideo(BaseModel):
    third_url: str = ""                    # 第三方视频链接
    plat_video: Optional[ThreadContentPlatVideo] = None
```

#### TextProps 文本属性

```python
@dataclass
class TextProps(BaseModel):
    font_bold: bool = False                # 加粗
    italic: bool = False                   # 斜体
    underline: bool = False                # 下划线
```

#### ParagraphProps 段落属性

```python
@dataclass
class ParagraphProps(BaseModel):
    alignment: int = 0                     # 对齐方式（Alignment 枚举）
```

#### Alignment 对齐方式枚举

```python
class Alignment(IntEnum):
    ALIGNMENT_LEFT = 0                     # 左对齐
    ALIGNMENT_MIDDLE = 1                   # 居中
    ALIGNMENT_RIGHT = 2                    # 右对齐
```

#### RichText 富文本对象

用于论坛帖子内容中的富文本元素。

```python
@dataclass
class RichText(BaseModel):
    type: int = 0                          # RichType 富文本类型
    text_info: Optional[TextInfo] = None
    at_info: Optional[AtInfo] = None
    url_info: Optional[URLInfo] = None
    emoji_info: Optional[EmojiInfo] = None
    channel_info: Optional[ChannelInfo] = None

    TYPE_TEXT: ClassVar[int] = 1
    TYPE_AT: ClassVar[int] = 2
    TYPE_URL: ClassVar[int] = 3
    TYPE_EMOJI: ClassVar[int] = 4
    TYPE_CHANNEL: ClassVar[int] = 5
    TYPE_VIDEO: ClassVar[int] = 10
    TYPE_IMAGE: ClassVar[int] = 11
```

#### AtInfo @内容信息

```python
@dataclass
class AtInfo(BaseModel):
    type: int = 0                          # AtType @类型
    user_info: Optional[AtUserInfo] = None
    role_info: Optional[AtRoleInfo] = None
    guild_info: Optional[AtGuildInfo] = None
```

#### AtType @类型枚举

```python
class AtType(IntEnum):
    AT_EXPLICIT_USER = 1                   # @特定人
    AT_ROLE_GROUP = 2                      # @角色组所有人
    AT_GUILD = 3                           # @频道所有人
```

#### AtUserInfo @用户信息

```python
@dataclass
class AtUserInfo(BaseModel):
    id: str = ""
    nick: str = ""
```

#### AtRoleInfo @身份组信息

```python
@dataclass
class AtRoleInfo(BaseModel):
    role_id: int = 0
    name: str = ""
    color: int = 0
```

#### AtGuildInfo @频道信息

```python
@dataclass
class AtGuildInfo(BaseModel):
    guild_id: str = ""
    guild_name: str = ""
```

#### TextInfo / URLInfo / EmojiInfo / ChannelInfo

```python
@dataclass
class TextInfo(BaseModel):
    text: str = ""

@dataclass
class URLInfo(BaseModel):
    url: str = ""
    display_text: str = ""

@dataclass
class EmojiInfo(BaseModel):
    id: str = ""
    type: str = ""
    name: str = ""
    url: str = ""

@dataclass
class ChannelInfo(BaseModel):
    channel_id: int = 0
    channel_name: str = ""
```

### GroupEvent / FriendEvent 群聊/好友事件

```python
@dataclass
class GroupEvent(BaseModel):
    timestamp: int = 0
    group_openid: str = ""
    op_member_openid: str = ""

@dataclass
class FriendEvent(BaseModel):
    timestamp: int = 0
    openid: str = ""
```

---

## API 响应模型

### OnlineNumsResponse 在线人数

```python
@dataclass
class OnlineNumsResponse(BaseModel):
    online_nums: int = 0
```

### GuildRolesResponse 身份组列表

```python
@dataclass
class GuildRolesResponse(BaseModel):
    roles: list = []
    role_num_limit: int = 0
```

### CreateRoleResponse 创建身份组结果

```python
@dataclass
class CreateRoleResponse(BaseModel):
    role_id: str = ""
    role: dict = {}
```

### RoleMembersResponse 身份组成员

```python
@dataclass
class RoleMembersResponse(BaseModel):
    data: list = []
    next: str = ""
```

### MuteBatchResponse 批量禁言结果

```python
@dataclass
class MuteBatchResponse(BaseModel):
    user_ids: list[str] = []
```

### ChannelPermissions 子频道权限

```python
@dataclass
class ChannelPermissions(BaseModel):
    user_id: str = ""
    role_id: str = ""
    permissions: str = ""
```

### DMS 私信会话

```python
@dataclass
class DMS(BaseModel):
    guild_id: str = ""
```

---

## 使用示例

### 类型注解获得 IDE 支持

```python
from easybot import Bot, Model

@bot.on_guild_message
async def handle(msg: Model.GuildMessage):
    print(msg.channel_id)
    print(msg.author.username)
```

### 访问原始数据

```python
@bot.on_guild_message
async def handle(msg: Model.GuildMessage):
    if msg._raw_data:
        print("原始数据:", msg._raw_data)
```

### 安全访问可选字段

```python
@bot.on_guild_message
async def handle(msg: Model.GuildMessage):
    username = msg.author.username if msg.author else "未知"
```

---

## 下一步

- [插件与权限](./07_插件与权限.md) — 命令注册、预处理器和权限控制
