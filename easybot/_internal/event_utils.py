#!/usr/bin/env python3
"""
EasyBot SDK 事件处理工具模块

提供事件处理的公共工具函数，避免代码重复。
"""

import asyncio
from typing import TYPE_CHECKING, Any

from .constants import C2C_EVENTS, DIRECT_MESSAGE_EVENTS, GROUP_EVENTS, GUILD_EVENTS

if TYPE_CHECKING:
    from ..sandbox import SandBox


def check_sandbox(
    sandbox: "SandBox | None",
    is_sandbox_mode: bool,
    data: dict[str, Any],
    event_type: str,
) -> bool:
    """
    检查事件是否通过沙箱过滤

    Args:
        sandbox: 沙箱配置实例
        is_sandbox_mode: 是否为沙箱模式
        data: 事件数据
        event_type: 事件类型

    Returns:
        是否通过沙箱检查
    """
    if not sandbox:
        return True

    if event_type in GUILD_EVENTS:
        guild_id = data.get("guild_id")
        if guild_id:
            return sandbox.check_guild(guild_id, is_sandbox_mode)

    if event_type in GROUP_EVENTS:
        group_openid = data.get("group_openid")
        if group_openid:
            return sandbox.check_group(group_openid, is_sandbox_mode)

    if event_type in C2C_EVENTS:
        author = data.get("author", {})
        user_openid = author.get("user_openid") or author.get("member_openid")
        if user_openid:
            return sandbox.check_user(user_openid, is_sandbox_mode, is_qq=True)

    if event_type in DIRECT_MESSAGE_EVENTS:
        author = data.get("author", {})
        user_id = author.get("id")
        if user_id:
            return sandbox.check_user(user_id, is_sandbox_mode, is_qq=False)

    return sandbox.sandbox_fail_action


async def cleanup_task(task, name: str = "任务") -> None:
    """
    安全取消并清理异步任务

    Args:
        task: 要清理的任务
        name: 任务名称（用于日志）
    """
    if task is not None:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        except Exception:
            pass


async def cleanup_session(session: Any, name: str = "Session") -> None:
    """
    安全关闭aiohttp Session

    Args:
        session: aiohttp ClientSession实例
        name: Session名称（用于日志）
    """
    if session is not None and not session.closed:
        try:
            await session.close()
        except Exception:
            pass


async def cleanup_websocket(ws: Any, name: str = "WebSocket") -> None:
    """
    安全关闭WebSocket连接

    Args:
        ws: WebSocket响应对象
        name: WebSocket名称（用于日志）
    """
    if ws is not None and not ws.closed:
        try:
            await ws.close()
        except Exception:
            pass
