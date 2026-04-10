#!/usr/bin/env python3
"""
EasyBot SDK 消息去重模块

提供基于消息 ID 的事件去重功能，防止同一消息被重复处理。

使用 LRU 策略管理缓存，自动清理最旧的消息 ID。
"""

import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any


@dataclass
class DedupConfig:
    """
    去重配置

    Attributes:
        enabled: 是否启用去重
        max_size: 最大缓存消息数量
        ttl_seconds: 消息 ID 过期时间（秒），0 表示不过期
    """

    enabled: bool = True
    max_size: int = 10000
    ttl_seconds: int = 300


class MessageDeduplicator:
    """
    消息去重器

    使用 LRU 缓存存储已处理的消息 ID，防止重复处理。

    特性：
    - 基于 LRU 策略自动清理旧消息
    - 支持 TTL 过期清理
    - 线程安全（适用于 asyncio 环境）

    使用示例：
        dedup = MessageDeduplicator(max_size=10000, ttl_seconds=300)

        if dedup.check_and_mark("message_123"):
            print("新消息，开始处理")
        else:
            print("重复消息，跳过")
    """

    __slots__ = ("_max_size", "_ttl_seconds", "_cache", "_hit_count", "_miss_count")

    def __init__(
        self,
        max_size: int = 10000,
        ttl_seconds: int = 300,
    ):
        """
        初始化去重器

        Args:
            max_size: 最大缓存消息数量，默认 10000
            ttl_seconds: 消息 ID 过期时间（秒），默认 300 秒（5 分钟）
        """
        self._max_size = max_size
        self._ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, float] = OrderedDict()
        self._hit_count = 0
        self._miss_count = 0

    def check_and_mark(self, message_id: str) -> bool:
        """
        检查消息是否为新消息，并标记为已处理

        若消息已存在于缓存中，会刷新其 TTL 并移至 LRU 末尾，
        避免因 LRU 顺序与时间戳不一致导致过期清理遗漏。

        Args:
            message_id: 消息 ID

        Returns:
            True 表示新消息，False 表示重复消息
        """
        if not message_id:
            return True

        current_time = time.time()

        if message_id in self._cache:
            self._cache[message_id] = current_time
            self._cache.move_to_end(message_id)
            self._hit_count += 1
            return False

        self._cleanup_expired(current_time)

        self._cache[message_id] = current_time
        self._cache.move_to_end(message_id)
        self._miss_count += 1

        if len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

        return True

    def is_duplicate(self, message_id: str) -> bool:
        """
        检查消息是否为重复消息

        注意：此方法会刷新已存在消息的 TTL 并移至 LRU 末尾，
        而非纯只读查询。如需无副作用查询，请直接使用 ``message_id in dedup``。

        Args:
            message_id: 消息 ID

        Returns:
            True 表示重复消息，False 表示新消息
        """
        if not message_id:
            return False

        if message_id in self._cache:
            self._cache[message_id] = time.time()
            self._cache.move_to_end(message_id)
            return True

        return False

    def mark_processed(self, message_id: str) -> None:
        """
        标记消息为已处理

        以当前时间作为时间戳写入缓存并移至 LRU 末尾。
        若缓存超出 max_size，则淘汰最久未访问的条目。

        Args:
            message_id: 消息 ID
        """
        if not message_id:
            return

        self._cache[message_id] = time.time()
        self._cache.move_to_end(message_id)

        if len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def _cleanup_expired(self, current_time: float) -> None:
        """
        清理过期的消息 ID

        利用 OrderedDict 按"最后访问时间"升序排列的特性，
        从头部开始收集过期条目，遇到第一个未过期元素即停止。
        """
        if self._ttl_seconds <= 0:
            return

        expired_keys = []
        for key, timestamp in self._cache.items():
            if current_time - timestamp > self._ttl_seconds:
                expired_keys.append(key)
            else:
                break

        for key in expired_keys:
            del self._cache[key]

    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()
        self._hit_count = 0
        self._miss_count = 0

    @property
    def size(self) -> int:
        """当前缓存大小"""
        return len(self._cache)

    @property
    def stats(self) -> dict[str, Any]:
        """
        获取统计信息

        Returns:
            包含缓存大小、命中率等统计信息的字典
        """
        total = self._hit_count + self._miss_count
        hit_rate = self._hit_count / total if total > 0 else 0.0

        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "ttl_seconds": self._ttl_seconds,
            "hit_count": self._hit_count,
            "miss_count": self._miss_count,
            "hit_rate": hit_rate,
        }

    def __len__(self) -> int:
        return len(self._cache)

    def __contains__(self, message_id: str) -> bool:
        return message_id in self._cache
