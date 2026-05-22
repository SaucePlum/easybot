#!/usr/bin/env python3
"""
EasyBot SDK Intent 计算模块

定义所有 Intent 值并提供自动计算功能。
"""

from enum import IntFlag


class Intent(IntFlag):
    """
    Intent 位标志

    用于订阅不同类型的事件。
    """

    GUILDS = 1 << 0
    GUILD_MEMBERS = 1 << 1
    GUILD_MESSAGES = 1 << 9
    GUILD_MESSAGE_REACTIONS = 1 << 10
    DIRECT_MESSAGE = 1 << 12
    OPEN_FORUM_EVENT = 1 << 18
    INTERACTION = 1 << 26
    MESSAGE_AUDIT = 1 << 27
    FORUMS_EVENT = 1 << 28
    AUDIO_ACTION = 1 << 29
    PUBLIC_GUILD_MESSAGES = 1 << 30
    GROUP_AND_C2C_EVENT = 1 << 25

    ALL_INTENT_EVENT = (
        GUILDS
        | GUILD_MEMBERS
        | GUILD_MESSAGES
        | GUILD_MESSAGE_REACTIONS
        | DIRECT_MESSAGE
        | MESSAGE_AUDIT
        | FORUMS_EVENT
        | AUDIO_ACTION
        | PUBLIC_GUILD_MESSAGES
        | INTERACTION
        | GROUP_AND_C2C_EVENT
        | OPEN_FORUM_EVENT
    )

    DEFAULT_PUBLIC = (
        GUILDS | PUBLIC_GUILD_MESSAGES | GROUP_AND_C2C_EVENT | OPEN_FORUM_EVENT
    )

    DEFAULT_PRIVATE = (
        GUILDS
        | GUILD_MEMBERS
        | GUILD_MESSAGES
        | GUILD_MESSAGE_REACTIONS
        | DIRECT_MESSAGE
        | MESSAGE_AUDIT
        | INTERACTION
        | GROUP_AND_C2C_EVENT
    )


EVENT_INTENT_MAP = {
    "GUILD_CREATE": Intent.GUILDS,
    "GUILD_UPDATE": Intent.GUILDS,
    "GUILD_DELETE": Intent.GUILDS,
    "CHANNEL_CREATE": Intent.GUILDS,
    "CHANNEL_UPDATE": Intent.GUILDS,
    "CHANNEL_DELETE": Intent.GUILDS,
    "GUILD_MEMBER_ADD": Intent.GUILD_MEMBERS,
    "GUILD_MEMBER_UPDATE": Intent.GUILD_MEMBERS,
    "GUILD_MEMBER_REMOVE": Intent.GUILD_MEMBERS,
    "MESSAGE_CREATE": Intent.GUILD_MESSAGES,
    "AT_MESSAGE_CREATE": Intent.PUBLIC_GUILD_MESSAGES,
    "MESSAGE_DELETE": Intent.GUILD_MESSAGES,
    "PUBLIC_MESSAGE_DELETE": Intent.PUBLIC_GUILD_MESSAGES,
    "DIRECT_MESSAGE_CREATE": Intent.DIRECT_MESSAGE,
    "DIRECT_MESSAGE_DELETE": Intent.DIRECT_MESSAGE,
    "MESSAGE_AUDIT_PASS": Intent.MESSAGE_AUDIT,
    "MESSAGE_AUDIT_REJECT": Intent.MESSAGE_AUDIT,
    "MESSAGE_REACTION_ADD": Intent.GUILD_MESSAGE_REACTIONS,
    "MESSAGE_REACTION_REMOVE": Intent.GUILD_MESSAGE_REACTIONS,
    "INTERACTION_CREATE": Intent.INTERACTION,
    "FORUM_THREAD_CREATE": Intent.FORUMS_EVENT,
    "FORUM_THREAD_UPDATE": Intent.FORUMS_EVENT,
    "FORUM_THREAD_DELETE": Intent.FORUMS_EVENT,
    "FORUM_POST_CREATE": Intent.FORUMS_EVENT,
    "FORUM_POST_DELETE": Intent.FORUMS_EVENT,
    "FORUM_REPLY_CREATE": Intent.FORUMS_EVENT,
    "FORUM_REPLY_DELETE": Intent.FORUMS_EVENT,
    "FORUM_PUBLISH_AUDIT_RESULT": Intent.FORUMS_EVENT,
    "OPEN_FORUM_THREAD_CREATE": Intent.OPEN_FORUM_EVENT,
    "OPEN_FORUM_THREAD_UPDATE": Intent.OPEN_FORUM_EVENT,
    "OPEN_FORUM_THREAD_DELETE": Intent.OPEN_FORUM_EVENT,
    "OPEN_FORUM_POST_CREATE": Intent.OPEN_FORUM_EVENT,
    "OPEN_FORUM_POST_DELETE": Intent.OPEN_FORUM_EVENT,
    "OPEN_FORUM_REPLY_CREATE": Intent.OPEN_FORUM_EVENT,
    "OPEN_FORUM_REPLY_DELETE": Intent.OPEN_FORUM_EVENT,
    "AUDIO_START": Intent.AUDIO_ACTION,
    "AUDIO_FINISH": Intent.AUDIO_ACTION,
    "AUDIO_ON_MIC": Intent.AUDIO_ACTION,
    "AUDIO_OFF_MIC": Intent.AUDIO_ACTION,
    "AUDIO_OR_LIVE_CHANNEL_MEMBER_ENTER": Intent.AUDIO_ACTION,
    "AUDIO_OR_LIVE_CHANNEL_MEMBER_EXIT": Intent.AUDIO_ACTION,
    "GROUP_AT_MESSAGE_CREATE": Intent.GROUP_AND_C2C_EVENT,
    "GROUP_MESSAGE_CREATE": Intent.GROUP_AND_C2C_EVENT,
    "C2C_MESSAGE_CREATE": Intent.GROUP_AND_C2C_EVENT,
    "GROUP_ADD_ROBOT": Intent.GROUP_AND_C2C_EVENT,
    "GROUP_DEL_ROBOT": Intent.GROUP_AND_C2C_EVENT,
    "GROUP_MSG_REJECT": Intent.GROUP_AND_C2C_EVENT,
    "GROUP_MSG_RECEIVE": Intent.GROUP_AND_C2C_EVENT,
    "FRIEND_ADD": Intent.GROUP_AND_C2C_EVENT,
    "FRIEND_DEL": Intent.GROUP_AND_C2C_EVENT,
    "C2C_MSG_REJECT": Intent.GROUP_AND_C2C_EVENT,
    "C2C_MSG_RECEIVE": Intent.GROUP_AND_C2C_EVENT,
}


class IntentCalculator:
    """
    Intent 计算器

    用于根据注册的事件处理器自动计算所需的 Intent 值。
    """

    def __init__(self):
        self._registered_events: set[str] = set()
        self._intent_value: int = 0

    def register_event(self, event_type: str) -> None:
        """
        注册事件类型

        Args:
            event_type: 事件类型名称
        """
        if event_type in EVENT_INTENT_MAP:
            self._registered_events.add(event_type)
            self._intent_value |= EVENT_INTENT_MAP[event_type]

    def get_intent_value(self) -> int:
        """
        获取计算后的 Intent 值

        Returns:
            Intent 整数值
        """
        return self._intent_value

    def get_registered_events(self) -> set[str]:
        """
        获取已注册的事件类型

        Returns:
            事件类型集合
        """
        return self._registered_events.copy()

    def has_intent(self, intent: Intent) -> bool:
        """
        检查是否包含指定的 Intent

        Args:
            intent: 要检查的 Intent

        Returns:
            是否包含该 Intent
        """
        return bool(self._intent_value & intent)

    def reset(self) -> None:
        """重置计算器"""
        self._registered_events.clear()
        self._intent_value = 0


def get_event_types_by_intent(intent: Intent) -> list[str]:
    """
    根据 Intent 获取对应的事件类型列表

    Args:
        intent: Intent 值或组合

    Returns:
        该 Intent 对应的所有事件类型列表
    """
    event_types = []
    for event_type, event_intent in EVENT_INTENT_MAP.items():
        if intent & event_intent:
            event_types.append(event_type)
    return event_types
