#!/usr/bin/env python3
"""
EasyBot SDK 消息处理工具模块

提供消息内容处理功能，包括去除艾特机器人标记和斜杠等。
"""

import re
from functools import lru_cache


@lru_cache(maxsize=128)
def _get_at_pattern(bot_id: str) -> re.Pattern:
    """
    获取艾特机器人的正则表达式模式（缓存编译结果）

    Args:
        bot_id: 机器人ID

    Returns:
        编译后的正则表达式模式
    """
    return re.compile(rf"<@!?{bot_id}>")


def treat_message_content(content: str, bot_id: str | None = None) -> str:
    """
    处理消息内容，去除艾特机器人标记和开头的斜杠

    Args:
        content: 原始消息内容
        bot_id: 机器人ID（可选）

    Returns:
        处理后的消息内容
    """
    result = content

    if bot_id:
        at_pattern = _get_at_pattern(bot_id)
        result = at_pattern.sub("", result)

    result = result.strip()
    result = result.lstrip("/")
    result = result.strip()

    return result


def check_user_is_admin(member_roles: list[str]) -> bool:
    """
    检查用户是否为频道管理员或频道主

    Args:
        member_roles: 用户的身份组ID列表

    Returns:
        是否为管理员或频道主
    """
    admin_roles = {"2", "4"}
    return bool(admin_roles & set(member_roles))
