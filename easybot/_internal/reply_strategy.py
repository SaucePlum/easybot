#!/usr/bin/env python3
"""
EasyBot SDK 回复策略模块

提供事件级别回复功能的统一策略实现。

被动回复参数说明：
- msg_id 和 event_id 任填一个即为被动消息
- 本模块优先使用 msg_id；仅当事件没有 msg_id 时才回退到 event_id

支持的被动回复事件类型（共 22 个）：
- 频道: AT_MESSAGE_CREATE, MESSAGE_CREATE, DIRECT_MESSAGE_CREATE,
        MESSAGE_REACTION_*, FORUM_THREAD_*, FORUM_POST_*, FORUM_REPLY_*,
        GUILD_MEMBER_ADD/UPDATE/REMOVE
- 群聊: GROUP_AT_MESSAGE_CREATE, GROUP_ADD_ROBOT, GROUP_MSG_RECEIVE
- 单聊: C2C_MESSAGE_CREATE, FRIEND_ADD, C2C_MSG_RECEIVE
- 动态: INTERACTION_CREATE（按 chat_type 自动分发）
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, BinaryIO

if TYPE_CHECKING:
    from ..api import API
    from ..builders import MessagesModel


class ReplyStrategy(ABC):
    """
    回复策略抽象基类

    定义统一的消息回复接口，具体实现由各场景策略完成。
    """

    @abstractmethod
    async def reply(
        self,
        content: "str | MessagesModel.Message | MessagesModel.MessageEmbed | MessagesModel.MessageArk23 | MessagesModel.MessageArk24 | MessagesModel.MessageArk37 | MessagesModel.MessageMarkdown | None" = None,
        reference: bool = False,
        msg_seq: int = 1,
        image: str | None = None,
        file_image: bytes | BinaryIO | str | None = None,
        media_file_info: str | None = None,
        msg_type: int | None = None,
        is_wakeup: bool = False,
        channel_id: str | None = None,
    ):
        """
        发送回复消息

        Args:
            content: 消息内容，支持文本、普通消息构建器或结构化消息构建器
            reference: 是否引用原消息
            msg_seq: 消息序号（群聊/单聊使用）
            image: 图片 URL（普通消息）
            file_image: 图片数据（普通消息）
            media_file_info: 富媒体文件信息（群聊/单聊 v2）
            msg_type: 消息类型
            is_wakeup: 是否发送互动召回消息
            channel_id: 子频道 ID（仅频道场景使用，用于指定回复目标）

        Returns:
            发送结果
        """
        pass


class UnifiedReplyStrategy(ReplyStrategy):
    """
    统一被动回复策略

    所有支持被动回复的事件共享同一个策略类，通过 scene 区分回复目标：
    - guild: 频道子频道 → send_guild_message(channel_id, ..., msg_id/event_id)
    - direct: 频道私信 → send_direct_message(guild_id, ..., msg_id/event_id)
    - group: 群聊 → send_group_message(group_openid, ..., msg_id/event_id)
    - c2c: 单聊 → send_c2c_message(openid, ..., msg_id/event_id)

    官方文档说明：msg_id 和 event_id 任填一个即为被动消息。
    本策略按事件类型自动选择：
    - 消息类事件（有 msg_id）→ 优先使用 msg_id，兼容官方可能的消息类专属限制
    - 非消息类事件（无 msg_id）→ 使用 event_id

    引用回复说明：
    - 公开 reply() 继续使用 reference=True 语义
    - reply_strategy 内部统一转成发送 API 所需的引用参数
    """

    def __init__(
        self,
        api: "API",
        scene: str,
        locator: str,
        event_id: str,
        msg_id: str = "",
    ):
        self._api: "API" = api
        self._scene: str = scene
        self._locator: str = locator
        self._event_id: str = event_id
        self._msg_id: str = msg_id

    async def reply(
        self,
        content: "str | MessagesModel.Message | MessagesModel.MessageEmbed | MessagesModel.MessageArk23 | MessagesModel.MessageArk24 | MessagesModel.MessageArk37 | MessagesModel.MessageMarkdown | None" = None,
        reference: bool = False,
        msg_seq: int = 1,
        image: str | None = None,
        file_image: bytes | BinaryIO | str | None = None,
        media_file_info: str | None = None,
        msg_type: int | None = None,
        is_wakeup: bool = False,
        channel_id: str | None = None,
    ):
        """
        发送回复消息

        Args:
            content: 消息内容，支持文本、普通消息构建器或结构化消息构建器
            reference: 是否引用原消息（引用回复）
            msg_seq: 消息序号（群聊/单聊使用）
            image: 图片 URL（普通消息）
            file_image: 图片数据（普通消息）
            media_file_info: 富媒体文件信息（群聊/单聊 v2）
            msg_type: 消息类型，默认按内容自动推断
            is_wakeup: 是否发送互动召回消息（仅 QQ 单聊 v2）
            channel_id: 子频道 ID（仅频道场景使用，用于指定回复目标）

        Returns:
            发送结果

        """
        message_reference_id = self._msg_id if reference and self._msg_id else None

        match self._scene:
            case "guild":
                target = channel_id or self._locator
                if not target:
                    raise ValueError(
                        "缺少 channel_id，无法确定回复目标子频道。"
                        "请在 reply(channel_id='xxx') 中指定，或确认事件数据包含 channel_id。"
                    )
                return await self._api.send_guild_message(
                    channel_id=target,
                    content=content,
                    image=image,
                    file_image=file_image,
                    msg_id=self._msg_id or None,
                    event_id=self._event_id if not self._msg_id else None,
                    message_reference_id=message_reference_id,
                )

            case "direct":
                return await self._api.send_direct_message(
                    guild_id=self._locator,
                    content=content,
                    image=image,
                    file_image=file_image,
                    msg_id=self._msg_id or None,
                    event_id=self._event_id if not self._msg_id else None,
                    message_reference_id=message_reference_id,
                )

            case "group":
                return await self._api.send_group_message(
                    group_openid=self._locator,
                    content=content,
                    media_file_info=media_file_info,
                    msg_id=self._msg_id or None,
                    event_id=self._event_id if not self._msg_id else None,
                    msg_type=msg_type,
                    msg_seq=msg_seq,
                    message_reference_id=message_reference_id,
                )

            case "c2c":
                return await self._api.send_c2c_message(
                    openid=self._locator,
                    content=content,
                    media_file_info=media_file_info,
                    msg_id=self._msg_id or None,
                    event_id=self._event_id if not self._msg_id else None,
                    msg_type=msg_type,
                    msg_seq=msg_seq,
                    is_wakeup=is_wakeup,
                    message_reference_id=message_reference_id,
                )

            case _:
                raise ValueError(f"未知的回复场景: {self._scene}")


# 事件 → (scene, 定位字段名, 消息ID字段名) 配置表
# scene 决定调用哪个 API，定位字段决定回复目标，消息ID字段决定是否使用 msg_id
_EVENT_CONFIG: dict[str, tuple[str, str, str]] = {
    # ===== 频道场景 (guild) =====
    "AT_MESSAGE_CREATE": ("guild", "channel_id", "id"),
    "MESSAGE_CREATE": ("guild", "channel_id", "id"),
    "MESSAGE_REACTION_ADD": ("guild", "channel_id", ""),
    "MESSAGE_REACTION_REMOVE": ("guild", "channel_id", ""),
    "FORUM_THREAD_CREATE": ("guild", "channel_id", ""),
    "FORUM_THREAD_UPDATE": ("guild", "channel_id", ""),
    "FORUM_THREAD_DELETE": ("guild", "channel_id", ""),
    "FORUM_POST_CREATE": ("guild", "channel_id", ""),
    "FORUM_POST_DELETE": ("guild", "channel_id", ""),
    "FORUM_REPLY_CREATE": ("guild", "channel_id", ""),
    "FORUM_REPLY_DELETE": ("guild", "channel_id", ""),
    "GUILD_MEMBER_ADD": ("guild", "", ""),
    "GUILD_MEMBER_UPDATE": ("guild", "", ""),
    "GUILD_MEMBER_REMOVE": ("guild", "", ""),
    # ===== 频道私信 (direct) =====
    "DIRECT_MESSAGE_CREATE": ("direct", "guild_id", "id"),
    # ===== 群聊场景 (group) =====
    "GROUP_AT_MESSAGE_CREATE": ("group", "group_openid", "id"),
    "GROUP_ADD_ROBOT": ("group", "group_openid", ""),
    "GROUP_MSG_RECEIVE": ("group", "group_openid", ""),
    # ===== 单聊场景 (c2c) =====
    "C2C_MESSAGE_CREATE": ("c2c", "_author_user_openid", "id"),
    "FRIEND_ADD": ("c2c", "openid", ""),
    "C2C_MSG_RECEIVE": ("c2c", "openid", ""),
    # INTERACTION_CREATE 不在表中，由动态分发处理
}


def create_reply_strategy(
    event_type: str,
    api: "API",
    data: dict,
    event_id: str | None = None,
) -> ReplyStrategy | None:
    """
    根据事件类型创建统一的回复策略

    Args:
        event_type: 事件类型（Payload.t）
        api: API 实例
        data: 事件原始数据（Payload.d）
        event_id: 事件 ID（Payload.id）

    Returns:
        UnifiedReplyStrategy 实例，如果不支持则返回 None

    Note:
        官方规定 msg_id/event_id 任填一个即可被动回复。
        消息类事件优先使用 msg_id，非消息类事件使用 event_id。
    """
    if event_type == "INTERACTION_CREATE":
        return _create_interaction_strategy(api, data, event_id)

    config = _EVENT_CONFIG.get(event_type)
    if not config:
        return None

    scene, field, msg_field = config
    locator = _extract_locator(data, field)
    msg_id = _extract_msg_id(data, msg_field) if msg_field else ""

    if not event_id and not msg_id:
        return None

    return UnifiedReplyStrategy(
        api=api,
        scene=scene,
        locator=locator,
        event_id=event_id or "",
        msg_id=msg_id,
    )


def _extract_locator(data: dict, field: str) -> str:
    """从事件数据中提取定位字段值（用于确定回复目标）"""
    if not field:
        return ""
    if field == "_author_user_openid":
        author = data.get("author", {})
        return author.get("user_openid", "")
    return data.get(field, "")


def _extract_msg_id(data: dict, field: str) -> str:
    """从事件数据中提取消息 ID（仅消息类事件有此字段）"""
    if not field:
        return ""
    return data.get(field, "")


def _create_interaction_strategy(
    api: "API",
    data: dict,
    event_id: str,
) -> ReplyStrategy | None:
    """
    互动事件策略工厂

    根据 chat_type 动态分发到对应场景：
    - chat_type=0 (频道): guild 场景
    - chat_type=1 (群聊): group 场景
    - chat_type=2 (单聊): c2c 场景
    """
    chat_type = data.get("chat_type")

    if chat_type == 0:
        return UnifiedReplyStrategy(
            api=api,
            scene="guild",
            locator=data.get("channel_id", ""),
            event_id=event_id,
        )
    elif chat_type == 1:
        return UnifiedReplyStrategy(
            api=api,
            scene="group",
            locator=data.get("group_openid", ""),
            event_id=event_id,
        )
    elif chat_type == 2:
        user_openid = data.get("user_openid") or data.get("group_member_openid", "")
        return UnifiedReplyStrategy(
            api=api,
            scene="c2c",
            locator=user_openid,
            event_id=event_id,
        )

    return None
