#!/usr/bin/env python3
"""
EasyBot SDK 数据模型模块

提供所有数据模型的定义，按功能分类组织：
1. 基础模型
2. 用户相关模型
3. 频道相关模型
4. 消息相关模型
5. 事件相关模型
6. API响应模型
"""

from dataclasses import MISSING, dataclass, field
from enum import IntEnum
from typing import TYPE_CHECKING, Any, BinaryIO, ClassVar, TypeAlias, TypeVar

if TYPE_CHECKING:
    from ._internal.reply_strategy import ReplyStrategy
    from .api import API
    from .bot import Bot
    from .builders import MessagesModel
    from .session import SessionManager


# ==================== 生命周期事件模型 ====================


class SessionStatus:
    """
    会话状态枚举类

    会话只有两种状态：活跃和非活跃。超时后会话会变为 INACTIVE，
    然后由 GC 在指定时间后清理，这样可以给用户一个"缓冲期"来恢复会话。
    """

    ACTIVE = 0
    INACTIVE = 1


@dataclass
class GatewayInfo:
    """
    Gateway 信息数据类

    存储 /gateway/bot 接口返回的完整信息。
    """

    url: str
    shards: int
    session_total: int
    session_remaining: int
    session_reset_after: int
    max_concurrency: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GatewayInfo":
        """从 API 响应创建 GatewayInfo 实例"""
        session_limit = data.get("session_start_limit", {})
        return cls(
            url=data.get("url", ""),
            shards=data.get("shards", 1),
            session_total=session_limit.get("total", 1000),
            session_remaining=session_limit.get("remaining", 1000),
            session_reset_after=session_limit.get("reset_after", 0),
            max_concurrency=session_limit.get("max_concurrency", 1),
        )


@dataclass
class StartupEvent:
    """
    启动事件数据

    Attributes:
        bot: Bot 实例
        timestamp: 事件触发时间戳
    """

    bot: "Bot"
    timestamp: float


@dataclass
class ShutdownEvent:
    """
    关闭事件数据

    Attributes:
        bot: Bot 实例
        timestamp: 事件触发时间戳
    """

    bot: "Bot"
    timestamp: float


@dataclass
class TimerEvent:
    """
    定时器事件数据

    Attributes:
        bot: Bot 实例
        timestamp: 事件触发时间戳
        tick_count: 第几次触发（从1开始）
    """

    bot: "Bot"
    timestamp: float
    tick_count: int


# ==================== 基础模型 ====================
T = TypeVar("T", bound="BaseModel")

_field_names_cache: dict[type, set[str]] = {}
_field_info_cache: dict[type, dict[str, tuple]] = {}


@dataclass
class BaseModel:
    """模型基类，提供通用方法"""

    _raw_data: dict | None = field(default=None, repr=False, compare=False)
    _reply_strategy: "ReplyStrategy | None" = field(
        default=None, repr=False, compare=False
    )
    _msg_seq: int = field(default=1, repr=False, compare=False)

    event_id: str = field(default="", repr=False, compare=False)
    seq: int | None = field(default=None, repr=False, compare=False)
    opcode: int = field(default=0, repr=False, compare=False)
    event_type: str = field(default="", repr=False, compare=False)

    @classmethod
    def _get_field_names(cls: type[T]) -> set[str]:
        """获取缓存的字段名集合"""
        if cls not in _field_names_cache:
            _field_names_cache[cls] = {
                f.name for f in cls.__dataclass_fields__.values()
            }
        return _field_names_cache[cls]

    @classmethod
    def _get_field_info(cls: type[T]) -> dict[str, tuple]:
        """获取缓存的字段信息（包含default和default_factory）"""
        if cls not in _field_info_cache:
            info = {}
            for fname, f in cls.__dataclass_fields__.items():
                has_default = f.default is not MISSING
                has_factory = f.default_factory is not MISSING
                info[fname] = (has_default, has_factory)
            _field_info_cache[cls] = info
        return _field_info_cache[cls]

    @classmethod
    def from_dict(cls: type[T], data: dict) -> T:
        """
        从字典创建模型实例

        Args:
            data: 原始数据字典

        Returns:
            模型实例
        """
        if data is None:
            return None

        field_names = cls._get_field_names()
        field_info = cls._get_field_info()

        kwargs = {}
        for key, value in data.items():
            if key in field_names:
                kwargs[key] = value

        if "_raw_data" in field_names:
            kwargs["_raw_data"] = data

        for fname in field_names:
            if fname not in kwargs and fname != "_raw_data":
                has_default, has_factory = field_info.get(fname, (False, False))
                if has_default or has_factory:
                    continue
                kwargs[fname] = None

        return cls(**kwargs)

    _TO_DICT_EXCLUDE_FIELDS = {
        "event_id",
        "seq",
        "opcode",
        "event_type",
        "_msg_seq",
    }

    def to_dict(self) -> dict:
        """
        将模型实例转换为字典

        Returns:
            dict: 模型数据的字典表示
        """
        result = {}
        for f in self.__dataclass_fields__.values():
            if f.name.startswith("_"):
                continue
            if f.name in self._TO_DICT_EXCLUDE_FIELDS:
                continue
            if f.name.isupper():
                continue
            value = getattr(self, f.name)
            if value is None:
                continue
            if isinstance(value, BaseModel):
                result[f.name] = value.to_dict()
            elif isinstance(value, list):
                result[f.name] = [
                    item.to_dict() if isinstance(item, BaseModel) else item
                    for item in value
                ]
            else:
                result[f.name] = value
        return result

    async def reply(
        self,
        content: "str | MessagesModel.Message | MessagesModel.MessageEmbed | MessagesModel.MessageArk23 | MessagesModel.MessageArk24 | MessagesModel.MessageArk37 | MessagesModel.MessageMarkdown | None" = None,
        reference: bool = False,
        image: str | None = None,
        file_image: bytes | BinaryIO | str | None = None,
        media_file_info: str | None = None,
        msg_type: int | None = None,
        is_wakeup: bool = False,
        channel_id: str | None = None,
    ):
        """
        回复消息

        Args:
            content: 消息内容，支持文本、普通消息构建器或结构化消息构建器
            reference: 是否引用原消息
            image: 图片 URL（普通消息）
            file_image: 图片数据，支持 bytes、BinaryIO 或文件路径（普通消息）
            media_file_info: 富媒体文件信息（群聊/单聊 v2）
            msg_type: 消息类型，默认按内容自动推断
            is_wakeup: 是否发送互动召回消息（仅 QQ 单聊 v2）
            channel_id: 子频道 ID。仅频道类被动事件在缺少默认目标时需要显式传入

        Returns:
            发送结果模型

        Raises:
            RuntimeError: 模型不支持回复操作

        使用示例:
            # 文本回复
            await msg.reply("收到！")

            # Embed 消息
            await msg.reply(MessagesModel.MessageEmbed(title="标题"))

            # 普通图片回复
            await msg.reply("图片", image="https://example.com/image.png")

            # 带引用回复
            await msg.reply("回复你", reference=True)

            # 成员事件等无默认子频道的频道事件
            await msg.reply("欢迎加入", channel_id="目标子频道ID")
        """
        if self._reply_strategy is None:
            raise RuntimeError("此模型不支持回复操作")

        result = await self._reply_strategy.reply(
            content,
            reference=reference,
            msg_seq=self._msg_seq,
            image=image,
            file_image=file_image,
            media_file_info=media_file_info,
            msg_type=msg_type,
            is_wakeup=is_wakeup,
            channel_id=channel_id,
        )
        self._msg_seq += 1
        return result

    @property
    def api(self) -> "API | None":
        """
        获取 API 实例

        通过此属性可以访问所有 API 方法，用于主动调用接口。

        Returns:
            API 实例，如果模型不支持则返回 None

        使用示例:
            # 发送消息到其他子频道
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
        """
        if self._reply_strategy is None:
            return None
        return self._reply_strategy._api

    @property
    def bot(self) -> "Bot | None":
        """
        获取 Bot 实例

        通过此属性可以访问机器人实例，用于获取 session 等功能。

        Returns:
            Bot 实例，如果模型不支持则返回 None

        使用示例:
            # 使用会话管理
            with msg.bot.session.bind(msg) as s:
                await s.new(Scope.USER, "key", {"data": "value"})
        """
        if self._reply_strategy is None:
            return None
        return self._reply_strategy._api._bot

    @property
    def session(self) -> "SessionManager | None":
        """
        获取会话管理器

        这是访问会话管理器的快捷方式，等同于 msg.bot.session。

        Returns:
            SessionManager 实例，如果模型不支持则返回 None

        使用示例:
            # 在插件中使用会话（推荐方式）
            with msg.session.bind(msg) as s:
                await s.new(Scope.USER, "key", {"data": "value"})
                data = await s.get(Scope.USER, "key")
        """
        if self._reply_strategy is None:
            return None
        return self._reply_strategy._api._bot.session


# 用户相关模型
@dataclass
class Author(BaseModel):
    """
    统一的作者模型

    包含所有场景下的用户信息字段，支持频道、群聊、单聊等多种场景。
    """

    id: str = ""
    username: str = ""
    avatar: str = ""
    bot: bool = False
    member_openid: str | None = None
    user_openid: str | None = None
    union_openid: str | None = None
    union_user_account: str | None = None


@dataclass
class Member(BaseModel):
    """
    频道成员对象

    用于频道内的成员信息。
    """

    user: Author | None = None
    nick: str = ""
    roles: list[str] = field(default_factory=list)
    joined_at: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "Member":
        if data is None:
            return None

        user_data = data.get("user")
        user = Author.from_dict(user_data) if user_data else None

        return cls(
            user=user,
            nick=data.get("nick", ""),
            roles=data.get("roles", []),
            joined_at=data.get("joined_at", ""),
            _raw_data=data,
        )


@dataclass
class MemberWithGuildID(Member):
    """
    带频道 ID 的成员对象

    用于成员相关事件中。
    """

    guild_id: str = ""
    op_user_id: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "MemberWithGuildID":
        if data is None:
            return None

        user_data = data.get("user")
        user = Author.from_dict(user_data) if user_data else None

        return cls(
            user=user,
            nick=data.get("nick", ""),
            roles=data.get("roles", []),
            joined_at=data.get("joined_at", ""),
            guild_id=data.get("guild_id", ""),
            op_user_id=data.get("op_user_id"),
            _raw_data=data,
        )


# 频道相关模型
@dataclass
class Guild(BaseModel):
    """
    频道对象

    用于频道信息获取。
    """

    id: str = ""
    name: str = ""
    icon: str = ""
    owner_id: str = ""
    owner: bool = False
    member_count: int = 0
    max_members: int = 0
    description: str = ""
    joined_at: str = ""


@dataclass
class Channel(BaseModel):
    """
    子频道对象

    用于子频道信息获取。
    """

    id: str = ""
    guild_id: str = ""
    name: str = ""
    type: int = 0
    sub_type: int = 0
    position: int = 0
    parent_id: str = ""
    owner_id: str = ""
    private_type: int = 0
    speak_permission: int = 0
    permissions: str = ""
    application_id: str | None = None
    op_user_id: str | None = None

    TYPE_TEXT: ClassVar[int] = 0
    TYPE_VOICE: ClassVar[int] = 2
    TYPE_CATEGORY: ClassVar[int] = 4
    TYPE_LIVE: ClassVar[int] = 10005
    TYPE_APP: ClassVar[int] = 10006
    TYPE_FORUM: ClassVar[int] = 10007

    SUB_TYPE_TALK: ClassVar[int] = 0
    SUB_TYPE_ANNOUNCEMENT: ClassVar[int] = 1
    SUB_TYPE_GUIDE: ClassVar[int] = 2
    SUB_TYPE_TEAM: ClassVar[int] = 3


@dataclass
class Thread(BaseModel):
    """
    帖子对象

    用于论坛帖子 API 响应。
    """

    guild_id: str = ""
    channel_id: str = ""
    author_id: str = ""
    thread_info: "ThreadInfo | None" = None

    @classmethod
    def from_dict(cls, data: dict) -> "Thread":
        if data is None:
            return None

        thread_info_data = data.get("thread_info")
        thread_info = (
            ThreadInfo.from_dict(thread_info_data) if thread_info_data else None
        )

        return cls(
            guild_id=data.get("guild_id", ""),
            channel_id=data.get("channel_id", ""),
            author_id=data.get("author_id", ""),
            thread_info=thread_info,
            _raw_data=data,
        )


@dataclass
class ThreadListResult(BaseModel):
    """
    帖子列表响应

    用于获取帖子列表 API。
    """

    threads: list["Thread"] = field(default_factory=list)
    is_finish: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> "ThreadListResult":
        if data is None:
            return None

        threads_data = data.get("threads", [])
        threads = [Thread.from_dict(t) for t in threads_data if t]

        return cls(
            threads=threads,
            is_finish=data.get("is_finish", 0),
            _raw_data=data,
        )


@dataclass
class ThreadDetail(BaseModel):
    """
    帖子详情响应

    用于获取帖子详情 API。
    """

    thread: "Thread | None" = None

    @classmethod
    def from_dict(cls, data: dict) -> "ThreadDetail":
        if data is None:
            return None

        thread_data = data.get("thread")
        thread = Thread.from_dict(thread_data) if thread_data else None

        return cls(
            thread=thread,
            _raw_data=data,
        )


@dataclass
class ThreadInfo(BaseModel):
    """
    帖子信息

    用于论坛帖子的 API 响应。
    """

    thread_id: str = ""
    title: str = ""
    content: str = ""
    date_time: str = ""


class Alignment(IntEnum):
    """
    段落对齐方向枚举

    用于富文本段落属性。
    """

    ALIGNMENT_LEFT = 0
    ALIGNMENT_MIDDLE = 1
    ALIGNMENT_RIGHT = 2


@dataclass
class TextInfo(BaseModel):
    """
    富文本 - 普通文本信息

    用于 RichObject 中的 text_info 字段。
    """

    text: str = ""


@dataclass
class AtUserInfo(BaseModel):
    """
    富文本 - @用户信息

    用于 AtInfo 中的 user_info 字段。
    """

    id: str = ""
    nick: str = ""


@dataclass
class AtRoleInfo(BaseModel):
    """
    富文本 - @身份组信息

    用于 AtInfo 中的 role_info 字段。
    """

    role_id: int = 0
    name: str = ""
    color: int = 0


@dataclass
class AtGuildInfo(BaseModel):
    """
    富文本 - @频道信息

    用于 AtInfo 中的 guild_info 字段。
    """

    guild_id: str = ""
    guild_name: str = ""


@dataclass
class AtInfo(BaseModel):
    """
    富文本 - @内容信息

    用于 RichObject 中的 at_info 字段。
    """

    type: int = 0
    user_info: AtUserInfo | None = None
    role_info: AtRoleInfo | None = None
    guild_info: AtGuildInfo | None = None

    TYPE_EXPLICIT_USER: ClassVar[int] = 1
    TYPE_ROLE_GROUP: ClassVar[int] = 2
    TYPE_GUILD: ClassVar[int] = 3

    @classmethod
    def from_dict(cls, data: dict) -> "AtInfo":
        if data is None:
            return None

        user_info_data = data.get("user_info")
        user_info = AtUserInfo.from_dict(user_info_data) if user_info_data else None

        role_info_data = data.get("role_info")
        role_info = AtRoleInfo.from_dict(role_info_data) if role_info_data else None

        guild_info_data = data.get("guild_info")
        guild_info = AtGuildInfo.from_dict(guild_info_data) if guild_info_data else None

        return cls(
            type=data.get("type", 0),
            user_info=user_info,
            role_info=role_info,
            guild_info=guild_info,
            _raw_data=data,
        )


@dataclass
class URLInfo(BaseModel):
    """
    富文本 - 链接信息

    用于 RichObject 中的 url_info 字段。
    """

    url: str = ""
    display_text: str = ""


@dataclass
class EmojiInfo(BaseModel):
    """
    富文本 - Emoji信息

    用于 RichObject 中的 emoji_info 字段。
    """

    id: str = ""
    type: str = ""
    name: str = ""
    url: str = ""


@dataclass
class ChannelInfo(BaseModel):
    """
    富文本 - 子频道信息

    用于 RichObject 中的 channel_info 字段。
    """

    channel_id: int = 0
    channel_name: str = ""


@dataclass
class RichText(BaseModel):
    """
    富文本对象（对应官方 RichObject）

    用于论坛帖子内容。
    """

    type: int = 0
    text_info: TextInfo | None = None
    at_info: AtInfo | None = None
    url_info: URLInfo | None = None
    emoji_info: EmojiInfo | None = None
    channel_info: ChannelInfo | None = None

    TYPE_TEXT: ClassVar[int] = 1
    TYPE_AT: ClassVar[int] = 2
    TYPE_URL: ClassVar[int] = 3
    TYPE_EMOJI: ClassVar[int] = 4
    TYPE_CHANNEL: ClassVar[int] = 5
    TYPE_VIDEO: ClassVar[int] = 10
    TYPE_IMAGE: ClassVar[int] = 11

    @classmethod
    def from_dict(cls, data: dict) -> "RichText":
        if data is None:
            return None

        text_info_data = data.get("text_info")
        text_info = TextInfo.from_dict(text_info_data) if text_info_data else None

        at_info_data = data.get("at_info")
        at_info = AtInfo.from_dict(at_info_data) if at_info_data else None

        url_info_data = data.get("url_info")
        url_info = URLInfo.from_dict(url_info_data) if url_info_data else None

        emoji_info_data = data.get("emoji_info")
        emoji_info = EmojiInfo.from_dict(emoji_info_data) if emoji_info_data else None

        channel_info_data = data.get("channel_info")
        channel_info = (
            ChannelInfo.from_dict(channel_info_data) if channel_info_data else None
        )

        return cls(
            type=data.get("type", 0),
            text_info=text_info,
            at_info=at_info,
            url_info=url_info,
            emoji_info=emoji_info,
            channel_info=channel_info,
            _raw_data=data,
        )


@dataclass
class TextProps(BaseModel):
    """
    富文本 - 文本段落属性

    用于 TextElem 中的 props 字段。
    """

    font_bold: bool = False
    italic: bool = False
    underline: bool = False


@dataclass
class ParagraphProps(BaseModel):
    """
    富文本 - 段落属性

    用于 Paragraph 中的 props 字段。
    """

    alignment: int = 0


@dataclass
class ThreadContentText(BaseModel):
    """
    帖子内容文本元素（对应官方 TextElem）

    用于 ThreadContentElem 中的 text 字段。
    """

    text: str = ""
    props: TextProps | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "ThreadContentText":
        if data is None:
            return None

        props_data = data.get("props")
        props = TextProps.from_dict(props_data) if props_data else None

        return cls(
            text=data.get("text", ""),
            props=props,
            _raw_data=data,
        )


@dataclass
class ThreadContentUrl(BaseModel):
    """
    帖子内容链接元素

    用于 ThreadContentElem 中的 url 字段。
    """

    url: str = ""
    desc: str = ""


@dataclass
class ThreadContentPlatImage(BaseModel):
    """
    帖子内容平台图片

    用于 ThreadContentImage 中的 plat_image 字段。
    """

    url: str = ""
    width: int = 0
    height: int = 0
    image_id: str = ""


@dataclass
class ThreadContentImage(BaseModel):
    """
    帖子内容图片元素（对应官方 ImageElem）

    用于 ThreadContentElem 中的 image 字段。
    """

    third_url: str = ""
    width_percent: float = 0.0


@dataclass
class ThreadContentPlatVideo(BaseModel):
    """
    帖子内容平台视频（对应官方 PlatVideo）

    用于 ThreadContentVideo 中的 plat_video 字段。
    """

    url: str = ""
    width: int = 0
    height: int = 0
    video_id: str = ""
    duration: int = 0
    cover: "ThreadContentPlatImage | None" = None

    @classmethod
    def from_dict(cls, data: dict) -> "ThreadContentPlatVideo":
        if data is None:
            return None

        cover_data = data.get("cover")
        cover = ThreadContentPlatImage.from_dict(cover_data) if cover_data else None

        return cls(
            url=data.get("url", ""),
            width=data.get("width", 0),
            height=data.get("height", 0),
            video_id=data.get("video_id", ""),
            duration=data.get("duration", 0),
            cover=cover,
            _raw_data=data,
        )


@dataclass
class ThreadContentVideo(BaseModel):
    """
    帖子内容视频元素（对应官方 VideoElem）

    用于 ThreadContentElem 中的 video 字段。
    """

    third_url: str = ""
    plat_video: "ThreadContentPlatVideo | None" = None

    @classmethod
    def from_dict(cls, data: dict) -> "ThreadContentVideo":
        if data is None:
            return None

        plat_video_data = data.get("plat_video")
        plat_video = (
            ThreadContentPlatVideo.from_dict(plat_video_data)
            if plat_video_data
            else None
        )

        return cls(
            third_url=data.get("third_url", ""),
            plat_video=plat_video,
            _raw_data=data,
        )


@dataclass
class ThreadContentElem(BaseModel):
    """
    帖子内容元素（对应官方 Elem）

    用于 ThreadContentParagraph 中的 elems 数组。
    """

    type: int = 1
    text: "ThreadContentText | None" = None
    image: "ThreadContentImage | None" = None
    video: "ThreadContentVideo | None" = None
    url: "ThreadContentUrl | None" = None

    TYPE_TEXT: ClassVar[int] = 1
    TYPE_IMAGE: ClassVar[int] = 2
    TYPE_VIDEO: ClassVar[int] = 3
    TYPE_URL: ClassVar[int] = 4

    @classmethod
    def from_dict(cls, data: dict) -> "ThreadContentElem":
        if data is None:
            return None

        text_data = data.get("text")
        text = ThreadContentText.from_dict(text_data) if text_data else None

        image_data = data.get("image")
        image = ThreadContentImage.from_dict(image_data) if image_data else None

        video_data = data.get("video")
        video = ThreadContentVideo.from_dict(video_data) if video_data else None

        url_data = data.get("url")
        url = ThreadContentUrl.from_dict(url_data) if url_data else None

        return cls(
            type=data.get("type", 1),
            text=text,
            image=image,
            video=video,
            url=url,
            _raw_data=data,
        )


@dataclass
class ThreadContentParagraph(BaseModel):
    """
    帖子内容段落（对应官方 Paragraph）

    用于 ThreadContent 中的 paragraphs 数组。
    """

    elems: list["ThreadContentElem"] = field(default_factory=list)
    props: ParagraphProps | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "ThreadContentParagraph":
        if data is None:
            return None

        elems_data = data.get("elems", [])
        elems = [ThreadContentElem.from_dict(e) for e in elems_data if e]

        props_data = data.get("props")
        props = ParagraphProps.from_dict(props_data) if props_data else None

        return cls(
            elems=elems,
            props=props,
            _raw_data=data,
        )


@dataclass
class ThreadContent(BaseModel):
    """
    帖子内容对象

    用于解析 ThreadInfo.content JSON 字符串。
    """

    paragraphs: list["ThreadContentParagraph"] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "ThreadContent":
        if data is None:
            return None

        paragraphs_data = data.get("paragraphs", [])
        paragraphs = [ThreadContentParagraph.from_dict(p) for p in paragraphs_data if p]

        return cls(
            paragraphs=paragraphs,
            _raw_data=data,
        )


# 消息相关模型
@dataclass
class Attachment(BaseModel):
    """
    消息附件

    用于消息中的图片、视频、语音、文件等附件。
    """

    url: str = ""
    content_type: str | None = None
    filename: str | None = None
    height: int | None = None
    width: int | None = None
    size: int | None = None
    voice_wav_url: str | None = None
    asr_refer_text: str | None = None


@dataclass
class MessageMedia(BaseModel):
    """富媒体消息"""

    file_info: str = ""


@dataclass
class MessageScene(BaseModel):
    """
    消息场景对象

    用于群聊和单聊消息中的场景信息,包含引用消息的扩展数据。
    """

    ext: list[str] = field(default_factory=list)
    source: str = ""


@dataclass
class MessageElement(BaseModel):
    """
    消息元素对象

    用于引用消息中包含的原始消息内容。
    """

    content: str = ""
    msg_idx: str = ""
    attachments: list[Attachment] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "MessageElement":
        if data is None:
            return None

        attachments_data = data.get("attachments", [])
        attachments = [Attachment.from_dict(a) for a in attachments_data if a]

        return cls(
            content=data.get("content", ""),
            msg_idx=data.get("msg_idx", ""),
            attachments=attachments,
            _raw_data=data,
        )


@dataclass
class MessageReference(BaseModel):
    """
    消息引用对象

    用于频道消息和私信消息中引用其他消息时的引用信息。
    """

    message_id: str = ""


@dataclass
class MessageBase(BaseModel):
    """
    消息基础模型

    包含所有消息模型的共同字段和方法。
    """

    id: str = ""
    content: str = ""
    timestamp: str = ""
    author: Author | None = None
    attachments: list[Attachment] = field(default_factory=list)
    treated_msg: str = ""

    @property
    def msg_id(self) -> str:
        """消息 ID 的别名"""
        return self.id

    @classmethod
    def _process_common_fields(cls, data: dict) -> dict:
        """处理消息模型的共同字段"""
        kwargs = {}

        # 处理作者信息
        author_data = data.get("author")
        kwargs["author"] = Author.from_dict(author_data) if author_data else None

        # 处理附件信息
        attachments_data = data.get("attachments", [])
        kwargs["attachments"] = [Attachment.from_dict(a) for a in attachments_data if a]

        # 处理共同字段
        kwargs["id"] = data.get("id", "")
        kwargs["content"] = data.get("content", "")
        kwargs["timestamp"] = data.get("timestamp", "")
        kwargs["_raw_data"] = data

        return kwargs


@dataclass
class GuildMessage(MessageBase):
    """
    频道消息模型

    用于频道内发送消息的响应。
    """

    channel_id: str = ""
    guild_id: str = ""
    edited_timestamp: str | None = None
    tts: bool = False
    mention_everyone: bool = False
    member: Member | None = None
    seq: int | None = None
    seq_in_channel: str | None = None
    pinned: bool = False
    type: int = 0
    flags: int = 0
    mentions: list[Author] = field(default_factory=list)
    message_reference: MessageReference | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "GuildMessage":
        if data is None:
            return None

        kwargs = cls._process_common_fields(data)

        member_data = data.get("member")
        kwargs["member"] = Member.from_dict(member_data) if member_data else None

        mentions_data = data.get("mentions", [])
        kwargs["mentions"] = [Author.from_dict(m) for m in mentions_data if m]

        message_reference_data = data.get("message_reference")
        kwargs["message_reference"] = (
            MessageReference.from_dict(message_reference_data)
            if message_reference_data
            else None
        )

        kwargs["channel_id"] = data.get("channel_id", "")
        kwargs["guild_id"] = data.get("guild_id", "")
        kwargs["edited_timestamp"] = data.get("edited_timestamp")
        kwargs["tts"] = data.get("tts", False)
        kwargs["mention_everyone"] = data.get("mention_everyone", False)
        kwargs["seq"] = data.get("seq")
        kwargs["seq_in_channel"] = data.get("seq_in_channel")
        kwargs["pinned"] = data.get("pinned", False)
        kwargs["type"] = data.get("type", 0)
        kwargs["flags"] = data.get("flags", 0)

        return cls(**kwargs)


@dataclass
class GroupMessage(MessageBase):
    """
    群聊消息模型（事件）

    用于群聊场景的消息事件。
    """

    group_openid: str = ""
    group_id: str = ""
    message_scene: MessageScene | None = None
    message_type: int = 0
    msg_elements: list[MessageElement] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "GroupMessage":
        if data is None:
            return None

        kwargs = cls._process_common_fields(data)

        kwargs["group_openid"] = data.get("group_openid", "")
        kwargs["group_id"] = data.get("group_id", "")

        message_scene_data = data.get("message_scene")
        kwargs["message_scene"] = (
            MessageScene.from_dict(message_scene_data) if message_scene_data else None
        )

        kwargs["message_type"] = data.get("message_type", 0)

        msg_elements_data = data.get("msg_elements", [])
        kwargs["msg_elements"] = [
            MessageElement.from_dict(e) for e in msg_elements_data if e
        ]

        return cls(**kwargs)


@dataclass
class C2CMessage(MessageBase):
    """
    单聊消息模型（事件）

    用于单聊场景的消息事件。
    """

    message_scene: MessageScene | None = None
    message_type: int = 0
    msg_elements: list[MessageElement] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "C2CMessage":
        if data is None:
            return None

        kwargs = cls._process_common_fields(data)

        message_scene_data = data.get("message_scene")
        kwargs["message_scene"] = (
            MessageScene.from_dict(message_scene_data) if message_scene_data else None
        )

        kwargs["message_type"] = data.get("message_type", 0)

        msg_elements_data = data.get("msg_elements", [])
        kwargs["msg_elements"] = [
            MessageElement.from_dict(e) for e in msg_elements_data if e
        ]

        return cls(**kwargs)


@dataclass
class DirectMessage(MessageBase):
    """
    频道私信消息模型（事件）

    用于频道私信场景的消息事件。
    """

    channel_id: str = ""
    guild_id: str = ""
    member: Member | None = None
    direct_message: bool = False
    message_reference: MessageReference | None = None
    src_guild_id: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "DirectMessage":
        if data is None:
            return None

        kwargs = cls._process_common_fields(data)

        member_data = data.get("member")
        kwargs["member"] = Member.from_dict(member_data) if member_data else None

        message_reference_data = data.get("message_reference")
        kwargs["message_reference"] = (
            MessageReference.from_dict(message_reference_data)
            if message_reference_data
            else None
        )

        kwargs["channel_id"] = data.get("channel_id", "")
        kwargs["guild_id"] = data.get("guild_id", "")
        kwargs["direct_message"] = data.get("direct_message", False)
        kwargs["src_guild_id"] = data.get("src_guild_id", "")

        return cls(**kwargs)


# 事件相关模型
@dataclass
class MessageDelete(BaseModel):
    """
    消息删除对象（事件）

    用于消息删除事件。
    """

    message: GuildMessage | None = None
    op_user: Author | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "MessageDelete":
        if data is None:
            return None

        message_data = data.get("message")
        message = GuildMessage.from_dict(message_data) if message_data else None

        op_user_data = data.get("op_user")
        op_user = Author.from_dict(op_user_data) if op_user_data else None

        return cls(message=message, op_user=op_user, _raw_data=data)


@dataclass
class MessageAudited(BaseModel):
    """
    消息审核对象（事件）

    用于消息审核事件。
    """

    audit_id: str = ""
    message_id: str = ""
    guild_id: str = ""
    channel_id: str = ""
    audit_time: str = ""
    create_time: str = ""
    seq_in_channel: str = ""


@dataclass
class Emoji(BaseModel):
    """
    Emoji 表情对象

    用于表情表态等功能。
    """

    id: str = ""
    type: int = 0

    TYPE_SYSTEM: ClassVar[int] = 1
    TYPE_EMOJI: ClassVar[int] = 2


@dataclass
class ReactionTarget(BaseModel):
    """
    表态对象（事件）

    用于表情表态事件。
    """

    id: str = ""
    type: int = 0

    TYPE_MESSAGE: ClassVar[int] = 0
    TYPE_THREAD: ClassVar[int] = 1
    TYPE_POST: ClassVar[int] = 2
    TYPE_REPLY: ClassVar[int] = 3


@dataclass
class MessageReaction(BaseModel):
    """
    表情表态对象（事件）

    用于表情表态事件。
    """

    user_id: str = ""
    guild_id: str = ""
    channel_id: str = ""
    target: ReactionTarget | None = None
    emoji: Emoji | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "MessageReaction":
        if data is None:
            return None

        target_data = data.get("target")
        target = ReactionTarget.from_dict(target_data) if target_data else None

        emoji_data = data.get("emoji")
        emoji = Emoji.from_dict(emoji_data) if emoji_data else None

        return cls(
            user_id=data.get("user_id", ""),
            guild_id=data.get("guild_id", ""),
            channel_id=data.get("channel_id", ""),
            target=target,
            emoji=emoji,
            _raw_data=data,
        )


@dataclass
class AudioAction(BaseModel):
    """
    音频操作对象（事件）

    用于音频事件。
    """

    guild_id: str = ""
    channel_id: str = ""
    audio_url: str = ""
    text: str = ""


@dataclass
class LiveChannelMember(BaseModel):
    """
    音视频/直播子频道成员对象（事件）

    用于用户进出音视频/直播子频道事件。
    """

    guild_id: str = ""
    channel_id: str = ""
    channel_type: int = 0
    user_id: str = ""

    TYPE_AUDIO: ClassVar[int] = 2
    TYPE_LIVE: ClassVar[int] = 4


@dataclass
class PostInfo(BaseModel):
    """
    帖子信息（事件）

    用于论坛评论。
    """

    thread_id: str = ""
    post_id: str = ""
    content: list[RichText] = field(default_factory=list)
    date_time: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "PostInfo":
        if data is None:
            return None

        content_data = data.get("content", [])
        content = [RichText.from_dict(c) for c in content_data if c]

        return cls(
            thread_id=data.get("thread_id", ""),
            post_id=data.get("post_id", ""),
            content=content,
            date_time=data.get("date_time", ""),
            _raw_data=data,
        )


@dataclass
class Post(BaseModel):
    """
    帖子评论对象（事件）

    用于论坛评论事件。
    """

    guild_id: str = ""
    channel_id: str = ""
    author_id: str = ""
    post_info: PostInfo | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "Post":
        if data is None:
            return None

        post_info_data = data.get("post_info")
        post_info = PostInfo.from_dict(post_info_data) if post_info_data else None

        return cls(
            guild_id=data.get("guild_id", ""),
            channel_id=data.get("channel_id", ""),
            author_id=data.get("author_id", ""),
            post_info=post_info,
            _raw_data=data,
        )


@dataclass
class ReplyInfo(BaseModel):
    """
    回复信息（事件）

    用于论坛回复。
    """

    thread_id: str = ""
    post_id: str = ""
    reply_id: str = ""
    content: list[RichText] = field(default_factory=list)
    date_time: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "ReplyInfo":
        if data is None:
            return None

        content_data = data.get("content", [])
        content = [RichText.from_dict(c) for c in content_data if c]

        return cls(
            thread_id=data.get("thread_id", ""),
            post_id=data.get("post_id", ""),
            reply_id=data.get("reply_id", ""),
            content=content,
            date_time=data.get("date_time", ""),
            _raw_data=data,
        )


@dataclass
class Reply(BaseModel):
    """
    回复对象（事件）

    用于论坛回复事件。
    """

    guild_id: str = ""
    channel_id: str = ""
    author_id: str = ""
    reply_info: ReplyInfo | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "Reply":
        if data is None:
            return None

        reply_info_data = data.get("reply_info")
        reply_info = ReplyInfo.from_dict(reply_info_data) if reply_info_data else None

        return cls(
            guild_id=data.get("guild_id", ""),
            channel_id=data.get("channel_id", ""),
            author_id=data.get("author_id", ""),
            reply_info=reply_info,
            _raw_data=data,
        )


@dataclass
class AuditResult(BaseModel):
    """
    审核结果对象（事件）

    用于论坛审核事件。
    """

    guild_id: str = ""
    channel_id: str = ""
    author_id: str = ""
    type: int = 0
    result: int = 0
    err_msg: str = ""
    thread_id: str | None = None
    post_id: str | None = None
    reply_id: str | None = None

    TYPE_PUBLISH_THREAD: ClassVar[int] = 1
    TYPE_PUBLISH_POST: ClassVar[int] = 2
    TYPE_PUBLISH_REPLY: ClassVar[int] = 3


@dataclass
class OpenForumEvent(BaseModel):
    """
    开放论坛事件对象（事件）

    用于话题子频道内发帖、评论、回复评论事件。
    公域机器人可订阅此事件。
    """

    guild_id: str = ""
    channel_id: str = ""
    author_id: str = ""


@dataclass
class GroupEvent(BaseModel):
    """
    群聊事件对象（事件）

    用于群聊相关事件。
    """

    timestamp: int = 0
    group_openid: str = ""
    op_member_openid: str = ""


@dataclass
class FriendEvent(BaseModel):
    """
    好友事件对象（事件）

    用于好友相关事件。
    """

    timestamp: int = 0
    openid: str = ""
    scene: int | None = None
    scene_param: str | None = None


@dataclass
class InteractionDataResolved(BaseModel):
    """互动事件数据解析"""

    button_data: str = ""
    button_id: str = ""
    user_id: str = ""
    message_id: str = ""


@dataclass
class InteractionData(BaseModel):
    """互动事件数据"""

    type: int = 0
    resolved: InteractionDataResolved | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "InteractionData":
        if data is None:
            return None

        resolved_data = data.get("resolved")
        resolved = (
            InteractionDataResolved.from_dict(resolved_data) if resolved_data else None
        )

        return cls(
            type=data.get("type", 0),
            resolved=resolved,
            _raw_data=data,
        )


@dataclass
class Interaction(BaseModel):
    """
    互动事件对象（事件）

    用于消息按钮点击等互动事件。
    """

    id: str = ""
    type: int = 0
    scene: str = ""
    chat_type: int = 0
    timestamp: str = ""
    guild_id: str | None = None
    channel_id: str | None = None
    user_openid: str | None = None
    group_openid: str | None = None
    group_member_openid: str | None = None
    data: InteractionData | None = None
    version: int = 1

    TYPE_BUTTON: ClassVar[int] = 11
    TYPE_MENU: ClassVar[int] = 12

    SCENE_C2C: ClassVar[str] = "c2c"
    SCENE_GROUP: ClassVar[str] = "group"
    SCENE_GUILD: ClassVar[str] = "guild"

    CHAT_TYPE_GUILD: ClassVar[int] = 0
    CHAT_TYPE_GROUP: ClassVar[int] = 1
    CHAT_TYPE_C2C: ClassVar[int] = 2

    @classmethod
    def from_dict(cls, data: dict) -> "Interaction":
        if data is None:
            return None

        data_obj = data.get("data")
        interaction_data = InteractionData.from_dict(data_obj) if data_obj else None

        return cls(
            id=data.get("id", ""),
            type=data.get("type", 0),
            scene=data.get("scene", ""),
            chat_type=data.get("chat_type", 0),
            timestamp=data.get("timestamp", ""),
            guild_id=data.get("guild_id"),
            channel_id=data.get("channel_id"),
            user_openid=data.get("user_openid"),
            group_openid=data.get("group_openid"),
            group_member_openid=data.get("group_member_openid"),
            data=interaction_data,
            version=data.get("version", 1),
            _raw_data=data,
        )


class OpCode(IntEnum):
    """
    Gateway 操作码（Opcode）

    用于标识 WebSocket/Webhook 传输数据的操作类型。
    参考官方文档: 事件订阅与通知 -> 通用数据结构 Payload
    """

    DISPATCH = 0
    HEARTBEAT = 1
    IDENTIFY = 2
    RESUME = 6
    RECONNECT = 7
    INVALID_SESSION = 9
    HELLO = 10
    HEARTBEAT_ACK = 11
    WEBHOOK_VALIDATION = 13


@dataclass
class Payload(BaseModel):
    """
    Gateway 通用数据结构（Payload）

    Webhook 或 WebSocket 连接上传输的数据统一采用此结构。
    所有上下行消息都封装在此结构中，通过 op 字段区分消息类型。

    参考官方文档: 事件订阅与通知 -> 4.1 通用数据结构 Payload

    结构示例::
        {
            "id": "event_id",
            "op": 0,
            "d": {},
            "s": 42,
            "t": "GATEWAY_EVENT_NAME"
        }
    """

    id: str = ""
    op: int = 0
    d: dict[str, Any] = field(default_factory=dict)
    s: int | None = None
    t: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "Payload":
        if data is None:
            return None
        return cls(
            id=data.get("id", ""),
            op=data.get("op", 0),
            d=data.get("d", {}) if data.get("d") is not None else {},
            s=data.get("s"),
            t=data.get("t"),
            event_id=data.get("id", ""),
            seq=data.get("s"),
            opcode=data.get("op", 0),
            event_type=data.get("t", "") or "",
            _raw_data=data,
        )

    def is_dispatch(self) -> bool:
        """是否为 Dispatch 事件（op=0）"""
        return self.op == OpCode.DISPATCH


# API响应模型
@dataclass
class APIPermission(BaseModel):
    """
    API 权限对象

    用于频道权限管理。
    """

    path: str = ""
    method: str = ""
    desc: str = ""
    auth_status: int = 0


@dataclass
class Role(BaseModel):
    """
    身份组对象

    用于频道身份组管理。
    """

    id: str = ""
    name: str = ""
    color: int = 0
    hoist: int = 0
    number: int = 0
    member_limit: int = 0


@dataclass
class ChannelPermissions(BaseModel):
    """
    子频道权限对象

    用于子频道权限管理。
    """

    channel_id: str = ""
    user_id: str | None = None
    role_id: str | None = None
    permissions: str = ""


@dataclass
class DMS(BaseModel):
    """
    私信会话对象

    用于创建和管理私信会话。
    """

    guild_id: str = ""
    channel_id: str = ""
    create_time: str = ""


@dataclass
class RecommendChannel(BaseModel):
    """推荐子频道"""

    channel_id: str = ""
    introduce: str = ""


@dataclass
class Announces(BaseModel):
    """
    公告对象

    用于频道公告管理。
    """

    guild_id: str = ""
    channel_id: str = ""
    message_id: str = ""
    announces_type: int = 0
    recommend_channels: list[RecommendChannel] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "Announces":
        if data is None:
            return None

        recommend_channels_data = data.get("recommend_channels", [])
        recommend_channels = [
            RecommendChannel.from_dict(rc) for rc in recommend_channels_data if rc
        ]

        return cls(
            guild_id=data.get("guild_id", ""),
            channel_id=data.get("channel_id", ""),
            message_id=data.get("message_id", ""),
            announces_type=data.get("announces_type", 0),
            recommend_channels=recommend_channels,
            _raw_data=data,
        )


@dataclass
class Schedule(BaseModel):
    """
    日程对象

    用于日程管理。
    """

    id: str = ""
    name: str = ""
    description: str = ""
    start_timestamp: str = ""
    end_timestamp: str = ""
    creator: Member | None = None
    jump_channel_id: str = ""
    remind_type: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "Schedule":
        if data is None:
            return None

        creator_data = data.get("creator")
        creator = Member.from_dict(creator_data) if creator_data else None

        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            start_timestamp=data.get("start_timestamp", ""),
            end_timestamp=data.get("end_timestamp", ""),
            creator=creator,
            jump_channel_id=data.get("jump_channel_id", ""),
            remind_type=data.get("remind_type", ""),
            _raw_data=data,
        )

    REMIND_NONE: ClassVar[str] = "0"
    REMIND_START: ClassVar[str] = "1"
    REMIND_5_MIN: ClassVar[str] = "2"
    REMIND_15_MIN: ClassVar[str] = "3"
    REMIND_30_MIN: ClassVar[str] = "4"
    REMIND_1_HOUR: ClassVar[str] = "5"


@dataclass
class PinsMessage(BaseModel):
    """
    精华消息对象

    用于精华消息管理。
    """

    guild_id: str = ""
    channel_id: str = ""
    message_ids: list[str] = field(default_factory=list)


@dataclass
class ReactionUsers(BaseModel):
    """
    表情表态用户列表

    用于获取表情表态用户。
    """

    users: list[Author] = field(default_factory=list)
    cookie: str = ""
    is_end: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> "ReactionUsers":
        if data is None:
            return None

        users_data = data.get("users", [])
        users = [Author.from_dict(u) for u in users_data if u]

        return cls(
            users=users,
            cookie=data.get("cookie", ""),
            is_end=data.get("is_end", False),
            _raw_data=data,
        )


@dataclass
class FileInfo(BaseModel):
    """
    文件信息对象

    用于文件上传结果。
    """

    file_uuid: str = ""
    file_info: str = ""
    ttl: int = 0
    id: str | None = None


@dataclass
class UploadPart(BaseModel):
    """
    分片信息对象

    用于大文件分片上传的分片信息。
    """

    index: int = 0
    presigned_url: str = ""


@dataclass
class UploadPrepareResponse(BaseModel):
    """
    大文件分片上传申请响应

    接口: POST /v2/users/{openid}/upload_prepare 或 /v2/groups/{group_openid}/upload_prepare
    返回上传任务 ID、分块大小和分片列表。
    """

    upload_id: str = ""
    block_size: int = 0
    parts: list[UploadPart] = field(default_factory=list)
    concurrency: int | None = None
    retry_timeout: int | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "UploadPrepareResponse":
        if data is None:
            return None

        parts_data = data.get("parts", [])
        parts = [UploadPart.from_dict(p) for p in parts_data if p]

        return cls(
            upload_id=data.get("upload_id", ""),
            block_size=int(data.get("block_size", 0)),
            parts=parts,
            concurrency=(
                int(data.get("concurrency")) if data.get("concurrency") else None
            ),
            retry_timeout=(
                int(data.get("retry_timeout")) if data.get("retry_timeout") else None
            ),
            _raw_data=data,
        )


@dataclass
class MessageSetting(BaseModel):
    """
    消息频率设置

    用于获取频道消息频率设置详情。
    """

    disable_create_dm: str = ""
    disable_push_msg: str = ""
    channel_ids: list[str] = field(default_factory=list)
    channel_push_max_num: int = 0


@dataclass
class APIPermissionDemandIdentify(BaseModel):
    """API 权限需求标识"""

    path: str = ""
    method: str = ""


@dataclass
class APIPermissionDemand(BaseModel):
    """
    API 权限需求对象

    用于发送权限授权链接。
    """

    guild_id: str = ""
    channel_id: str = ""
    api_identify: APIPermissionDemandIdentify | None = None
    title: str = ""
    desc: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "APIPermissionDemand":
        if data is None:
            return None

        api_identify_data = data.get("api_identify")
        api_identify = (
            APIPermissionDemandIdentify.from_dict(api_identify_data)
            if api_identify_data
            else None
        )

        return cls(
            guild_id=data.get("guild_id", ""),
            channel_id=data.get("channel_id", ""),
            api_identify=api_identify,
            title=data.get("title", ""),
            desc=data.get("desc", ""),
            _raw_data=data,
        )


@dataclass
class SessionStartLimit(BaseModel):
    """
    Session创建限制信息

    用于Gateway连接时返回的Session限制信息。
    """

    total: int = 0
    remaining: int = 0
    reset_after: int = 0
    max_concurrency: int = 1


@dataclass
class GatewayResponse(BaseModel):
    """
    获取通用WSS接入点响应

    接口: GET /gateway
    返回用于连接WebSocket的地址。
    """

    url: str = ""


@dataclass
class GatewayBotResponse(BaseModel):
    """
    获取带分片WSS接入点响应

    接口: GET /gateway/bot
    返回WebSocket连接地址及分片信息。
    """

    url: str = ""
    shards: int = 1
    session_start_limit: SessionStartLimit | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "GatewayBotResponse":
        if data is None:
            return None

        session_start_limit_data = data.get("session_start_limit")
        session_start_limit = (
            SessionStartLimit.from_dict(session_start_limit_data)
            if session_start_limit_data
            else None
        )

        return cls(
            url=data.get("url", ""),
            shards=data.get("shards", 1),
            session_start_limit=session_start_limit,
            _raw_data=data,
        )


@dataclass
class GuildRolesResponse(BaseModel):
    """
    获取频道身份组列表响应

    接口: GET /guilds/{guild_id}/roles
    返回频道下的身份组列表。
    """

    roles: list[Role] = field(default_factory=list)
    role_num_limit: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "GuildRolesResponse":
        if data is None:
            return None

        roles_data = data.get("roles", [])
        roles = [Role.from_dict(r) for r in roles_data if r]

        return cls(
            roles=roles,
            role_num_limit=data.get("role_num_limit", ""),
            _raw_data=data,
        )


@dataclass
class CreateRoleResponse(BaseModel):
    """
    创建频道身份组响应

    接口: POST /guilds/{guild_id}/roles
    返回创建的身份组信息。
    """

    role_id: str = ""
    role: Role | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "CreateRoleResponse":
        if data is None:
            return None

        role_data = data.get("role")
        role = Role.from_dict(role_data) if role_data else None

        return cls(
            role_id=data.get("role_id", ""),
            role=role,
            _raw_data=data,
        )


@dataclass
class RoleMembersResponse(BaseModel):
    """
    获取身份组成员列表响应

    接口: GET /guilds/{guild_id}/roles/{role_id}/members
    返回身份组的成员列表。
    """

    data: list[Member] = field(default_factory=list)
    next: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "RoleMembersResponse":
        if data is None:
            return None

        members_data = data.get("data", [])
        members = [Member.from_dict(m) for m in members_data if m]

        return cls(
            data=members,
            next=data.get("next", ""),
            _raw_data=data,
        )


@dataclass
class OnlineNumsResponse(BaseModel):
    """
    获取子频道在线成员数响应

    接口: GET /channels/{channel_id}/online_nums
    返回子频道的在线成员数。
    """

    online_nums: int = 0


@dataclass
class CreateThreadResponse(BaseModel):
    """
    发表帖子响应

    接口: PUT /channels/{channel_id}/threads
    返回创建帖子的任务 ID 和创建时间。
    """

    task_id: str = ""
    create_time: str = ""


@dataclass
class CreateCommentResponse(BaseModel):
    """
    发表评论响应

    接口: POST /channels/{channel_id}/threads/{thread_id}/comment
    返回创建评论的任务 ID 和创建时间。
    """

    task_id: str = ""
    create_time: int = 0


@dataclass
class C2CSendMessageResponse(BaseModel):
    """
    单聊发送消息响应

    接口: POST /v2/users/{openid}/messages
    返回发送的消息ID和时间戳。
    """

    id: str = ""
    timestamp: int = 0


@dataclass
class GroupSendMessageResponse(BaseModel):
    """
    群聊发送消息响应

    接口: POST /v2/groups/{group_openid}/messages
    返回发送的消息ID和时间戳。
    """

    id: str = ""
    timestamp: int = 0


@dataclass
class APIPermissionListResponse(BaseModel):
    """
    获取机器人在频道可用权限列表响应

    接口: GET /guilds/{guild_id}/api_permission
    返回机器人可用权限列表。
    """

    apis: list[APIPermission] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "APIPermissionListResponse":
        if data is None:
            return None

        apis_data = data.get("apis", [])
        apis = [APIPermission.from_dict(api) for api in apis_data if api]

        return cls(
            apis=apis,
            _raw_data=data,
        )


@dataclass
class UrlLinkResponse(BaseModel):
    """
    获取机器人分享链接响应

    接口: POST /v2/generate_url_link
    返回生成的分享链接。
    """

    url: str = ""


@dataclass
class MuteBatchResponse(BaseModel):
    """
    批量禁言响应

    接口: PATCH /guilds/{guild_id}/mute (批量)
    返回设置成功的成员user_ids。
    """

    user_ids: list[str] = field(default_factory=list)


@dataclass
class StreamMessageResponse(BaseModel):
    """
    流式消息发送响应

    接口: POST /v2/users/{openid}/stream_messages
    返回流式消息ID和时间戳。

    成功时返回: { id, timestamp, extInfo }
    失败时返回: { code, message }
    """

    code: int | None = None
    message: str | None = None
    id: str | None = None
    timestamp: str | None = None
    ext_info: dict | None = None


# 流式消息输入模式常量
class StreamInputMode:
    """流式消息输入模式"""

    REPLACE = "replace"


# 流式消息输入状态常量
class StreamInputState:
    """流式消息输入状态"""

    GENERATING = 1
    DONE = 10


# 流式消息内容类型常量
class StreamContentType:
    """流式消息内容类型"""

    MARKDOWN = "markdown"


# 模型导出类
class Model:
    """
    数据模型主类

    所有数据模型都可以通过 Model.xxx 访问。
    """

    BaseModel: TypeAlias = BaseModel
    MessageBase: TypeAlias = MessageBase

    Author: TypeAlias = Author
    Member: TypeAlias = Member
    MemberWithGuildID: TypeAlias = MemberWithGuildID

    Guild: TypeAlias = Guild
    Channel: TypeAlias = Channel
    Thread: TypeAlias = Thread
    ThreadListResult: TypeAlias = ThreadListResult
    ThreadDetail: TypeAlias = ThreadDetail
    ThreadContent: TypeAlias = ThreadContent
    Alignment: TypeAlias = Alignment

    GuildMessage: TypeAlias = GuildMessage
    GroupMessage: TypeAlias = GroupMessage
    C2CMessage: TypeAlias = C2CMessage
    DirectMessage: TypeAlias = DirectMessage

    Message: TypeAlias = GuildMessage | GroupMessage | C2CMessage | DirectMessage

    MessageDelete: TypeAlias = MessageDelete
    MessageAudited: TypeAlias = MessageAudited
    MessageReaction: TypeAlias = MessageReaction
    AudioAction: TypeAlias = AudioAction
    LiveChannelMember: TypeAlias = LiveChannelMember
    Post: TypeAlias = Post
    Reply: TypeAlias = Reply
    AuditResult: TypeAlias = AuditResult
    OpenForumEvent: TypeAlias = OpenForumEvent
    GroupEvent: TypeAlias = GroupEvent
    FriendEvent: TypeAlias = FriendEvent
    Interaction: TypeAlias = Interaction

    OpCode: TypeAlias = OpCode
    Payload: TypeAlias = Payload

    Role: TypeAlias = Role
    ChannelPermissions: TypeAlias = ChannelPermissions
    DMS: TypeAlias = DMS
    Announces: TypeAlias = Announces
    Schedule: TypeAlias = Schedule
    PinsMessage: TypeAlias = PinsMessage
    ReactionUsers: TypeAlias = ReactionUsers
    FileInfo: TypeAlias = FileInfo
    UploadPart: TypeAlias = UploadPart
    UploadPrepareResponse: TypeAlias = UploadPrepareResponse
    MessageSetting: TypeAlias = MessageSetting
    APIPermissionDemand: TypeAlias = APIPermissionDemand
    GatewayResponse: TypeAlias = GatewayResponse
    GatewayBotResponse: TypeAlias = GatewayBotResponse
    GuildRolesResponse: TypeAlias = GuildRolesResponse
    CreateRoleResponse: TypeAlias = CreateRoleResponse
    RoleMembersResponse: TypeAlias = RoleMembersResponse
    OnlineNumsResponse: TypeAlias = OnlineNumsResponse
    CreateThreadResponse: TypeAlias = CreateThreadResponse
    CreateCommentResponse: TypeAlias = CreateCommentResponse
    C2CSendMessageResponse: TypeAlias = C2CSendMessageResponse
    GroupSendMessageResponse: TypeAlias = GroupSendMessageResponse
    APIPermissionListResponse: TypeAlias = APIPermissionListResponse
    UrlLinkResponse: TypeAlias = UrlLinkResponse
    MuteBatchResponse: TypeAlias = MuteBatchResponse
    StreamMessageResponse: TypeAlias = StreamMessageResponse
    StreamInputMode: TypeAlias = StreamInputMode
    StreamInputState: TypeAlias = StreamInputState
    StreamContentType: TypeAlias = StreamContentType

    # 生命周期事件
    StartupEvent: TypeAlias = StartupEvent
    ShutdownEvent: TypeAlias = ShutdownEvent
    TimerEvent: TypeAlias = TimerEvent
    SessionStatus: TypeAlias = SessionStatus
    GatewayInfo: TypeAlias = GatewayInfo
