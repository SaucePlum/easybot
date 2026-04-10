#!/usr/bin/env python3
"""
EasyBot SDK WebSocket 基类模块

提供 WebSocket 客户端的公共功能，避免代码重复。
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

import aiohttp

from .event_utils import cleanup_session, cleanup_task, cleanup_websocket

if TYPE_CHECKING:
    from ..bot import Bot
    from ..logger import Logger


class BaseWebSocketClient(ABC):
    """
    WebSocket 客户端基类

    提供心跳机制、资源清理等公共功能。
    事件采用异步分发方式处理，不使用队列。
    """

    def __init__(
        self,
        bot: "Bot",
        logger: "Logger",
        connect_timeout: float = 30.0,
        heartbeat_interval: float = 41.25,
        no_msg_timeout: float = 180.0,
    ):
        """
        初始化基类

        Args:
            bot: Bot 实例
            logger: 日志记录器
            connect_timeout: 连接超时时间（秒）
            heartbeat_interval: 心跳间隔时间（秒）
            no_msg_timeout: 无消息超时时间（秒）
        """
        self._bot = bot
        self._logger = logger
        self._connect_timeout = connect_timeout
        self._heartbeat_interval = heartbeat_interval
        self._no_msg_timeout = no_msg_timeout

        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._session: aiohttp.ClientSession | None = None
        self._connected: bool = False
        self._reconnect_count: int = 0
        self._stop_event: asyncio.Event = asyncio.Event()

        self._heartbeat_task: asyncio.Task | None = None
        self._last_heartbeat_ack: float = 0
        self._last_message_time: float = 0

    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._connected

    @abstractmethod
    async def run(self) -> None:
        """运行客户端"""
        pass

    @abstractmethod
    async def _connect(self) -> None:
        """建立连接"""
        pass

    @abstractmethod
    async def _handle_message(self, data: dict[str, Any]) -> None:
        """处理消息"""
        pass

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建 aiohttp session"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self._connect_timeout)
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=30,
                ttl_dns_cache=30,
                enable_cleanup_closed=True,
                keepalive_timeout=10,
            )
            self._session = aiohttp.ClientSession(timeout=timeout, connector=connector)
        return self._session

    def _dispatch_event(
        self,
        event_type: str,
        data: dict[str, Any],
        *,
        event_id: str | None = None,
        seq: int | None = None,
        opcode: int = 0,
        skip_sandbox: bool = False,
    ) -> None:
        """
        异步分发事件到处理器

        使用统一的事件分发器处理事件。
        采用 create_task 实现非阻塞分发，提高吞吐量。

        Args:
            event_type: 事件类型
            data: 事件数据
            event_id: 事件 ID（来自 Payload.id）
            seq: 序列号（来自 Payload.s）
            opcode: 操作码（来自 Payload.op）
            skip_sandbox: 是否跳过沙箱检查
        """
        task = asyncio.create_task(
            self._bot._event_dispatcher.dispatch(
                event_type,
                data,
                event_id=event_id,
                seq=seq,
                opcode=opcode,
                skip_sandbox=skip_sandbox,
            )
        )
        task.add_done_callback(self._on_dispatch_done)

    def _on_dispatch_done(self, task: asyncio.Task) -> None:
        """处理事件分发任务的完成状态，捕获并记录异常"""
        if task.cancelled():
            return
        if exc := task.exception():
            self._logger.exception("事件分发任务执行失败: %s", exc)

    def _start_heartbeat(self) -> None:
        """启动心跳任务"""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()

        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._last_heartbeat_ack = time.time()

    async def _heartbeat_loop(self) -> None:
        """心跳循环"""
        while self._connected:
            try:
                await asyncio.sleep(self._heartbeat_interval)

                if not self._connected:
                    break

                if (
                    time.time() - self._last_heartbeat_ack
                    > self._heartbeat_interval * 2
                ):
                    self._logger.debug("心跳超时，将重新连接")
                    await self._reconnect()
                    break

                if time.time() - self._last_message_time > self._no_msg_timeout:
                    self._logger.debug(
                        f"超过 {self._no_msg_timeout} 秒未收到消息，将重新连接"
                    )
                    await self._reconnect()
                    break

                await self._send_heartbeat()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"心跳发送失败: {e}")
                break

    @abstractmethod
    async def _send_heartbeat(self) -> None:
        """发送心跳"""
        pass

    async def _reconnect(self) -> None:
        """重新连接"""
        self._connected = False
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None

        if self._ws:
            await self._ws.close()

    async def close(self) -> None:
        """
        关闭客户端并释放所有资源

        包括：
        - 停止心跳任务
        - 关闭 WebSocket 连接
        - 关闭 HTTP Session
        """
        self._stop_event.set()
        self._connected = False

        await cleanup_task(self._heartbeat_task, "心跳任务")
        self._heartbeat_task = None

        await cleanup_websocket(self._ws, "WebSocket")
        self._ws = None

        await cleanup_session(self._session, "HTTP Session")
        self._session = None

        self._logger.info("WebSocket 客户端已关闭")

    async def __aenter__(self) -> "BaseWebSocketClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        await self.close()
        return False
