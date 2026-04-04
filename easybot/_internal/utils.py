#!/usr/bin/env python3
"""
EasyBot SDK 工具函数模块

提供各种通用工具函数，包括时间戳转换、ID验证、安全获取和URL格式化等。
"""

from datetime import datetime
from typing import Any, Optional, Union


def timestamp_to_datetime(timestamp: Union[int, str, float]) -> datetime:
    """
    将时间戳转换为 datetime 对象

    Args:
        timestamp: 时间戳，可以是整数、字符串或浮点数

    Returns:
        datetime 对象

    Examples:
        >>> timestamp_to_datetime(1704067200)
        datetime.datetime(2026, 1, 1, 0, 0)
        >>> timestamp_to_datetime("2026-01-01T00:00:00")
        datetime.datetime(2026, 1, 1, 0, 0)
    """
    if isinstance(timestamp, str):
        # 处理 ISO 格式字符串
        if "T" in timestamp:
            # 移除可能的 Z 后缀
            timestamp = timestamp.rstrip("Z")
            return datetime.fromisoformat(timestamp)
        else:
            # 处理纯数字字符串
            timestamp = int(timestamp)

    if isinstance(timestamp, (int, float)):
        # 处理毫秒时间戳
        if timestamp > 10**10:
            timestamp = timestamp / 1000
        return datetime.fromtimestamp(timestamp)

    raise ValueError(f"无法转换时间戳: {timestamp}")


def validate_id(id_str: Optional[str], name: str = "ID") -> None:
    """
    验证 ID 是否有效

    Args:
        id_str: 要验证的 ID 字符串
        name: ID 的名称，用于错误消息

    Raises:
        ValueError: 如果 ID 无效

    Examples:
        >>> validate_id("123456")
        >>> validate_id("", "频道ID")
        ValueError: 频道ID 不能为空
    """
    if not id_str:
        raise ValueError(f"{name} 不能为空")


def safe_get(data: Optional[dict], *keys, default: Any = None) -> Any:
    """
    安全地从嵌套字典中获取值

    Args:
        data: 要查询的字典
        *keys: 要查找的键路径
        default: 如果找不到值返回的默认值

    Returns:
        找到的值或默认值

    Examples:
        >>> safe_get({"level1": {"level2": "value"}}, "level1", "level2")
        'value'
        >>> safe_get({"key": "value"}, "missing", default="default")
        'default'
    """
    if data is None:
        return default

    current = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]

    return current


def format_url(base_url: str, *path_segments: str) -> str:
    """
    格式化 URL 路径

    Args:
        base_url: 基础 URL
        *path_segments: 路径片段

    Returns:
        格式化后的完整 URL

    Examples:
        >>> format_url("https://api.example.com", "users", "123")
        'https://api.example.com/users/123'
        >>> format_url("https://api.example.com/", "/users")
        'https://api.example.com/users'
    """
    # 移除基础 URL 尾部的斜杠
    base_url = base_url.rstrip("/")

    # 处理路径片段
    segments = []
    for segment in path_segments:
        if segment:
            # 移除片段前后的斜杠
            segment = segment.strip("/")
            if segment:
                segments.append(segment)

    # 组合 URL
    if segments:
        return f"{base_url}/{'/'.join(segments)}"
    return base_url
