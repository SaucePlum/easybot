#!/usr/bin/env python3
"""
EasyBot SDK 常量定义模块

集中管理所有事件类型、错误码、API URL 等常量。
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..api import API

from ..models import Model
from .reply_strategy import create_reply_strategy

RETRYABLE_CODES: set[int] = {
    11281,
    11242,
    11252,
    306003,
    306005,
    306006,
    501002,
    501003,
    501004,
    501006,
    501007,
    501011,
    501012,
}

PERMISSION_DENIED_CODES: set[int] = {
    11253,
    11254,
    11265,
    11282,
    301006,
    302010,
    304004,
    304014,
    304036,
    304037,
    304046,
    304048,
    306004,
    501017,
}

API_BASE_URL: str = "https://api.sgroup.qq.com"
SANDBOX_API_BASE_URL: str = "https://sandbox.api.sgroup.qq.com"
TOKEN_API_URL: str = "https://bots.qq.com/app/getAppAccessToken"

GUILD_EVENTS: set[str] = {
    "GUILD_CREATE",
    "GUILD_UPDATE",
    "GUILD_DELETE",
    "CHANNEL_CREATE",
    "CHANNEL_UPDATE",
    "CHANNEL_DELETE",
    "GUILD_MEMBER_ADD",
    "GUILD_MEMBER_UPDATE",
    "GUILD_MEMBER_REMOVE",
    "MESSAGE_CREATE",
    "AT_MESSAGE_CREATE",
}

GROUP_EVENTS: set[str] = {
    "GROUP_AT_MESSAGE_CREATE",
    "GROUP_ADD_ROBOT",
    "GROUP_DEL_ROBOT",
    "GROUP_MSG_REJECT",
    "GROUP_MSG_RECEIVE",
}

C2C_EVENTS: set[str] = {
    "C2C_MESSAGE_CREATE",
    "FRIEND_ADD",
    "FRIEND_DEL",
    "C2C_MSG_REJECT",
    "C2C_MSG_RECEIVE",
}

DIRECT_MESSAGE_EVENTS: set[str] = {
    "DIRECT_MESSAGE_CREATE",
}

EVENT_DISPLAY_NAMES: dict[str, str] = {
    "AT_MESSAGE_CREATE": "频道@消息",
    "MESSAGE_CREATE": "频道全量消息",
    "MESSAGE_DELETE": "消息删除",
    "PUBLIC_MESSAGE_DELETE": "公域消息删除",
    "DIRECT_MESSAGE_DELETE": "私信消息删除",
    "GROUP_AT_MESSAGE_CREATE": "群聊@消息",
    "C2C_MESSAGE_CREATE": "私聊消息",
    "DIRECT_MESSAGE_CREATE": "频道私信",
    "GUILD_CREATE": "加入频道",
    "GUILD_UPDATE": "频道更新",
    "GUILD_DELETE": "退出频道",
    "CHANNEL_CREATE": "子频道创建",
    "CHANNEL_UPDATE": "子频道更新",
    "CHANNEL_DELETE": "子频道删除",
    "GUILD_MEMBER_ADD": "成员加入频道",
    "GUILD_MEMBER_UPDATE": "成员更新",
    "GUILD_MEMBER_REMOVE": "成员退出频道",
    "GROUP_ADD_ROBOT": "加入群聊",
    "GROUP_DEL_ROBOT": "退出群聊",
    "GROUP_MSG_REJECT": "群聊拒绝消息",
    "GROUP_MSG_RECEIVE": "群聊接受消息",
    "FRIEND_ADD": "添加好友",
    "FRIEND_DEL": "删除好友",
    "C2C_MSG_REJECT": "私聊拒绝消息",
    "C2C_MSG_RECEIVE": "私聊接受消息",
    "MESSAGE_AUDIT_PASS": "消息审核通过",
    "MESSAGE_AUDIT_REJECT": "消息审核拒绝",
    "MESSAGE_REACTION_ADD": "表情表态添加",
    "MESSAGE_REACTION_REMOVE": "表情表态移除",
    "INTERACTION_CREATE": "互动按钮回调",
    "FORUM_THREAD_CREATE": "帖子创建",
    "FORUM_THREAD_UPDATE": "帖子更新",
    "FORUM_THREAD_DELETE": "帖子删除",
    "FORUM_POST_CREATE": "评论创建",
    "FORUM_POST_DELETE": "评论删除",
    "FORUM_REPLY_CREATE": "回复创建",
    "FORUM_REPLY_DELETE": "回复删除",
    "FORUM_PUBLISH_AUDIT_RESULT": "论坛帖子审核结果",
    "OPEN_FORUM_THREAD_CREATE": "开放论坛主题创建",
    "OPEN_FORUM_THREAD_UPDATE": "开放论坛主题更新",
    "OPEN_FORUM_THREAD_DELETE": "开放论坛主题删除",
    "OPEN_FORUM_POST_CREATE": "开放论坛帖子创建",
    "OPEN_FORUM_POST_DELETE": "开放论坛帖子删除",
    "OPEN_FORUM_REPLY_CREATE": "开放论坛回复创建",
    "OPEN_FORUM_REPLY_DELETE": "开放论坛回复删除",
    "AUDIO_START": "音频开始播放",
    "AUDIO_FINISH": "音频播放结束",
    "AUDIO_ON_MIC": "上麦",
    "AUDIO_OFF_MIC": "下麦",
    "AUDIO_OR_LIVE_CHANNEL_MEMBER_ENTER": "进入音视频频道",
    "AUDIO_OR_LIVE_CHANNEL_MEMBER_EXIT": "离开音视频频道",
}

_EVENT_MODEL_MAP: dict[str, Any] = {
    "AT_MESSAGE_CREATE": Model.GuildMessage,
    "MESSAGE_CREATE": Model.GuildMessage,
    "MESSAGE_DELETE": Model.MessageDelete,
    "PUBLIC_MESSAGE_DELETE": Model.MessageDelete,
    "DIRECT_MESSAGE_CREATE": Model.DirectMessage,
    "DIRECT_MESSAGE_DELETE": Model.MessageDelete,
    "GROUP_AT_MESSAGE_CREATE": Model.GroupMessage,
    "C2C_MESSAGE_CREATE": Model.C2CMessage,
    "GUILD_CREATE": Model.Guild,
    "GUILD_UPDATE": Model.Guild,
    "GUILD_DELETE": Model.Guild,
    "CHANNEL_CREATE": Model.Channel,
    "CHANNEL_UPDATE": Model.Channel,
    "CHANNEL_DELETE": Model.Channel,
    "GUILD_MEMBER_ADD": Model.MemberWithGuildID,
    "GUILD_MEMBER_UPDATE": Model.MemberWithGuildID,
    "GUILD_MEMBER_REMOVE": Model.MemberWithGuildID,
    "MESSAGE_REACTION_ADD": Model.MessageReaction,
    "MESSAGE_REACTION_REMOVE": Model.MessageReaction,
    "MESSAGE_AUDIT_PASS": Model.MessageAudited,
    "MESSAGE_AUDIT_REJECT": Model.MessageAudited,
    "INTERACTION_CREATE": Model.Interaction,
    "FORUM_THREAD_CREATE": Model.Thread,
    "FORUM_THREAD_UPDATE": Model.Thread,
    "FORUM_THREAD_DELETE": Model.Thread,
    "FORUM_POST_CREATE": Model.Post,
    "FORUM_POST_DELETE": Model.Post,
    "FORUM_REPLY_CREATE": Model.Reply,
    "FORUM_REPLY_DELETE": Model.Reply,
    "FORUM_PUBLISH_AUDIT_RESULT": Model.AuditResult,
    "OPEN_FORUM_THREAD_CREATE": Model.OpenForumEvent,
    "OPEN_FORUM_THREAD_UPDATE": Model.OpenForumEvent,
    "OPEN_FORUM_THREAD_DELETE": Model.OpenForumEvent,
    "OPEN_FORUM_POST_CREATE": Model.OpenForumEvent,
    "OPEN_FORUM_POST_DELETE": Model.OpenForumEvent,
    "OPEN_FORUM_REPLY_CREATE": Model.OpenForumEvent,
    "OPEN_FORUM_REPLY_DELETE": Model.OpenForumEvent,
    "AUDIO_START": Model.AudioAction,
    "AUDIO_FINISH": Model.AudioAction,
    "AUDIO_ON_MIC": Model.AudioAction,
    "AUDIO_OFF_MIC": Model.AudioAction,
    "AUDIO_OR_LIVE_CHANNEL_MEMBER_ENTER": Model.LiveChannelMember,
    "AUDIO_OR_LIVE_CHANNEL_MEMBER_EXIT": Model.LiveChannelMember,
    "GROUP_ADD_ROBOT": Model.GroupEvent,
    "GROUP_DEL_ROBOT": Model.GroupEvent,
    "GROUP_MSG_REJECT": Model.GroupEvent,
    "GROUP_MSG_RECEIVE": Model.GroupEvent,
    "FRIEND_ADD": Model.FriendEvent,
    "FRIEND_DEL": Model.FriendEvent,
    "C2C_MSG_REJECT": Model.FriendEvent,
    "C2C_MSG_RECEIVE": Model.FriendEvent,
}


def convert_to_model(
    event_type: str,
    data: dict[str, Any],
    api: "API" = None,
    event_id: str | None = None,
    seq: int | None = None,
    opcode: int = 0,
) -> Any:
    """
    将原始事件数据转换为模型对象

    Args:
        event_type: 事件类型（Payload.t）
        data: 原始事件数据（Payload.d）
        api: API 实例（用于注入回复策略）
        event_id: 事件 ID（Payload.id）
        seq: 序列号（Payload.s）
        opcode: 操作码（Payload.op）

    Returns:
        转换后的模型对象，如果无法转换则返回 None
    """
    model_class = _EVENT_MODEL_MAP.get(event_type)
    if model_class:
        try:
            model = model_class.from_dict(data)
            model.event_type = event_type
            if event_id is not None:
                model.event_id = event_id
            if seq is not None:
                model.seq = seq
            model.opcode = opcode
            if api:
                strategy = create_reply_strategy(
                    event_type, api, data, event_id=event_id
                )
                model._reply_strategy = strategy
            return model
        except Exception:
            pass
    return None
