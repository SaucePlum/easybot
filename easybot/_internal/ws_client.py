#!/usr/bin/env python3
"""
EasyBot SDK WebSocket 客户端模块

提供 WebSocket 连接和远程 Webhook 连接功能。
"""

import asyncio
import json
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import aiohttp

from ..exceptions import AuthenticationError, NetworkError
from ..models import Model
from .event_utils import cleanup_task
from .http_client import generate_remote_signature
from .ws_base import BaseWebSocketClient

if TYPE_CHECKING:
    from ..bot import Bot


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


class SessionLimiter:
    """
    Session 启动限制器

    实现官方要求的 max_concurrency 限制：
    - 每 5 秒最多启动 max_concurrency 个 Session
    - 使用令牌桶算法控制并发
    """

    _global_semaphore: asyncio.Semaphore | None = None
    _last_acquire_time: float = 0
    _lock: asyncio.Lock | None = None
    _max_concurrency: int = 1

    @classmethod
    def set_max_concurrency(cls, value: int) -> None:
        """设置最大并发数（在首次 acquire 前调用）"""
        cls._max_concurrency = value

    @classmethod
    async def _ensure_initialized(cls) -> None:
        """
        确保限制器已初始化（线程安全）

        使用双重检查锁定模式避免竞态条件。
        """
        if cls._lock is None:
            cls._lock = asyncio.Lock()

        async with cls._lock:
            if cls._global_semaphore is None:
                cls._global_semaphore = asyncio.Semaphore(cls._max_concurrency)

    @classmethod
    async def acquire(cls) -> None:
        """
        获取一个 Session 启动许可

        遵守 max_concurrency 限制，每 5 秒窗口内最多启动指定数量的 Session。
        """
        await cls._ensure_initialized()

        async with cls._lock:
            now = time.time()
            elapsed = now - cls._last_acquire_time

            if elapsed < 5.0:
                await asyncio.sleep(5.0 - elapsed)

            await cls._global_semaphore.acquire()
            cls._last_acquire_time = time.time()

    @classmethod
    def release(cls) -> None:
        """释放 Session 启动许可"""
        if cls._global_semaphore is not None:
            try:
                cls._global_semaphore.release()
            except ValueError:
                pass


class WebSocketClient(BaseWebSocketClient):
    """
    WebSocket 客户端

    提供 WebSocket 连接管理，包括：
    - 连接建立和维护
    - 心跳维护
    - 消息收发
    - 断线重连
    - Resume 机制
    - Session 启动限制
    """

    def __init__(self, bot: "Bot", protocol):
        """
        初始化 WebSocket 客户端

        Args:
            bot: Bot 实例
            protocol: WebSocketProtocol 实例
        """
        super().__init__(
            bot=bot,
            logger=bot.logger.with_module("websocket"),
            connect_timeout=protocol.connect_timeout,
            heartbeat_interval=41.25,
            no_msg_timeout=protocol.disable_reconnect_on_not_recv_msg,
        )
        self._protocol = protocol

        self._session_id: str | None = None
        self._seq: int = 0
        self._gateway_info: GatewayInfo | None = None

        self._logger.debug(
            f"WebSocketClient 初始化: shard_no={protocol.shard_no}, "
            f"total_shard={protocol.total_shard}, timeout={self._connect_timeout}s"
        )

    async def run(self) -> None:
        """运行 WebSocket 连接"""
        while not self._stop_event.is_set():
            try:
                await self._connect()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.exception(f"WebSocket 连接错误: {e}")
                self._reconnect_count += 1
                wait_time = min(5 * self._reconnect_count, 60)
                await asyncio.sleep(wait_time)

    async def _connect(self) -> None:
        """建立 WebSocket 连接"""
        self._gateway_info = await self._get_gateway_info()

        await self._check_session_limit()

        SessionLimiter.set_max_concurrency(self._gateway_info.max_concurrency)
        await SessionLimiter.acquire()

        try:
            session = await self._get_session()

            self._logger.debug(f"正在连接到 Gateway: {self._gateway_info.url}")
            self._logger.debug(
                f"Gateway 详情: shards={self._gateway_info.shards}, "
                f"session={self._gateway_info.session_remaining}/{self._gateway_info.session_total}, "
                f"max_concurrency={self._gateway_info.max_concurrency}"
            )

            timeout = aiohttp.ClientTimeout(total=self._connect_timeout)
            async with session.ws_connect(
                self._gateway_info.url,
                heartbeat=self._protocol.disable_reconnect_on_not_recv_msg,
                timeout=timeout,
            ) as ws:
                self._ws = ws
                self._connected = True
                self._last_message_time = time.time()
                self._logger.debug("WebSocket 连接已建立，等待 Hello 消息...")

                await self._receive_messages()
        except asyncio.CancelledError:
            raise
        except aiohttp.ClientError as e:
            self._logger.error(f"WebSocket 连接失败: {e}")
            raise NetworkError(f"WebSocket 连接失败: {e}")
        finally:
            SessionLimiter.release()
            self._connected = False
            await cleanup_task(self._heartbeat_task, "心跳任务")
            self._heartbeat_task = None

    async def _get_gateway_info(self) -> GatewayInfo:
        """
        获取 Gateway 完整信息

        Returns:
            GatewayInfo: 包含 URL、分片数、Session 限制等信息
        """
        http_client = await self._bot.api._get_http()

        try:
            data = await http_client.get("/gateway/bot")
            gateway_info = GatewayInfo.from_dict(data)

            if not gateway_info.url:
                raise NetworkError("获取 Gateway 地址失败")

            self._logger.debug(
                f"Gateway 信息: 建议分片数={gateway_info.shards}, "
                f"剩余Session={gateway_info.session_remaining}/{gateway_info.session_total}"
            )

            if self._protocol.total_shard == 1 and gateway_info.shards > 1:
                self._logger.warning(
                    f"官方建议使用 {gateway_info.shards} 个分片，当前仅使用 1 个分片。"
                    f"如需多分片部署，请配置 Proto.websocket(shard_no=X, total_shard={gateway_info.shards})"
                )

            return gateway_info
        except Exception:
            raise

    async def _check_session_limit(self) -> None:
        """
        检查 Session 启动限制

        如果剩余 Session 数为 0，则等待 reset_after 毫秒后重置。
        """
        if self._gateway_info is None:
            return

        if self._gateway_info.session_remaining <= 0:
            wait_seconds = self._gateway_info.session_reset_after / 1000.0
            self._logger.warning(
                f"Session 启动次数已用尽 ({self._gateway_info.session_total}/{self._gateway_info.session_total})，"
                f"等待 {wait_seconds:.1f} 秒后重置"
            )
            await asyncio.sleep(wait_seconds)
            self._gateway_info = await self._get_gateway_info()

    async def _receive_messages(self) -> None:
        """接收并处理 WebSocket 消息"""
        receive_timeout = self._no_msg_timeout
        try:
            while self._connected:
                try:
                    message = await asyncio.wait_for(
                        self._ws.receive(), timeout=receive_timeout
                    )
                except asyncio.TimeoutError:
                    self._logger.warning(
                        f"超过 {receive_timeout} 秒未收到消息，连接可能已断开"
                    )
                    break

                self._last_message_time = time.time()

                if message.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(message.data)
                    await self._handle_message(data)

                elif message.type == aiohttp.WSMsgType.ERROR:
                    self._logger.error(f"WebSocket 错误: {self._ws.exception()}")
                    break

                elif message.type == aiohttp.WSMsgType.CLOSED:
                    close_code = self._ws.close_code or 0
                    self._logger.warning(f"WebSocket 连接已关闭，代码: {close_code}")
                    break

                elif message.type == aiohttp.WSMsgType.PING:
                    await self._ws.pong()

                elif message.type == aiohttp.WSMsgType.PONG:
                    pass

        except asyncio.CancelledError:
            self._logger.info("WebSocket 接收任务被取消")
            raise
        except Exception as e:
            self._logger.exception(f"WebSocket 接收消息错误: {e}")
        finally:
            self._connected = False

    async def _handle_message(self, data: dict[str, Any]) -> None:
        """处理 WebSocket 消息"""
        payload = Model.Payload.from_dict(data)
        if payload is None:
            self._logger.warning(f"收到无效的 Payload 数据: {data!r}")
            return

        if payload.s is not None:
            self._seq = payload.s

        match payload.op:
            case Model.OpCode.HELLO:
                self._heartbeat_interval = (
                    payload.d.get("heartbeat_interval", 41250) / 1000
                )
                if self._session_id:
                    await self._resume()
                else:
                    await self._identify()
                self._start_heartbeat()

            case Model.OpCode.HEARTBEAT_ACK:
                self._last_heartbeat_ack = time.time()
                self._logger.debug("收到心跳 ACK")

            case Model.OpCode.HEARTBEAT:
                await self._send_heartbeat()
                self._logger.debug("收到服务端心跳，已回复")

            case Model.OpCode.DISPATCH:
                await self._handle_dispatch(
                    payload.t,
                    payload.d,
                    event_id=payload.id,
                    seq=payload.s,
                    opcode=payload.op,
                )

            case Model.OpCode.RECONNECT:
                self._logger.debug("收到重连请求，将重新连接")
                await self._reconnect()

            case Model.OpCode.INVALID_SESSION:
                await self._handle_invalid_session(payload.d)

    async def _handle_invalid_session(self, can_resume: bool) -> None:
        """
        处理 Invalid Session 事件

        Args:
            can_resume: 是否可以 Resume
        """
        if can_resume:
            self._logger.warning("收到 Invalid Session (可 Resume)，尝试恢复连接")
            await asyncio.sleep(1)
            await self._resume()
        else:
            self._logger.warning(
                "收到 Invalid Session (不可 Resume)，清除 Session 并重新连接"
            )
            self._session_id = None
            self._seq = 0
            await self._reconnect()

    async def _handle_dispatch(
        self,
        event_type: str,
        data: dict[str, Any],
        event_id: str | None = None,
        seq: int | None = None,
        opcode: int = 0,
    ) -> None:
        """处理分发事件"""
        if event_type == "READY":
            self._session_id = data.get("session_id")
            self._reconnect_count = 0
            self._logger.debug(
                f"WebSocket 鉴权成功，session_id: {self._session_id[:8]}..."
            )
            self._logger.debug(
                f"READY 事件: version={data.get('version')}, shard={data.get('shard')}"
            )
            self._logger.info("【认证阶段】完成")
            await self._bot._trigger_startup()
            return

        if event_type == "RESUMED":
            self._logger.debug("WebSocket 连接恢复成功 (Resume)")
            return

        self._logger.debug(
            f"收到事件: {event_type}, id={data.get('id', 'N/A')}, event_id={event_id}"
        )
        self._dispatch_event(
            event_type, data, event_id=event_id, seq=seq, opcode=opcode
        )

    async def _send_heartbeat(self) -> None:
        """发送心跳"""
        payload = {"op": 1, "d": self._seq}
        await self._ws.send_json(payload)
        self._logger.debug("已发送心跳")

    async def _identify(self) -> None:
        """发送 Identify 鉴权"""
        http_client = await self._bot.api._get_http()
        access_token = await http_client.get_access_token()

        intents = self._bot._intents
        if intents == 0:
            for event_type in self._bot._event_handlers.keys():
                self._bot._intent_calculator.register_event(event_type)
            intents = self._bot._intent_calculator.get_intent_value()

        payload = {
            "op": 2,
            "d": {
                "token": f"QQBot {access_token}",
                "intents": intents,
                "shard": [self._protocol.shard_no, self._protocol.total_shard],
                "properties": {
                    "$os": "windows",
                    "$browser": "easybot",
                    "$device": "easybot",
                },
            },
        }

        await self._ws.send_json(payload)
        self._logger.debug("已发送 Identify 鉴权")

    async def _resume(self) -> None:
        """发送 Resume 恢复连接"""
        http_client = await self._bot.api._get_http()
        access_token = await http_client.get_access_token()

        payload = {
            "op": 6,
            "d": {
                "token": f"QQBot {access_token}",
                "session_id": self._session_id,
                "seq": self._seq,
            },
        }

        await self._ws.send_json(payload)
        self._logger.debug("已发送 Resume 请求")


class RemoteWebhookClient(BaseWebSocketClient):
    """
    远程 Webhook 客户端

    通过 WebSocket 连接到远程 Webhook 服务器。
    """

    def __init__(self, bot: "Bot", protocol):
        """
        初始化远程 Webhook 客户端

        Args:
            bot: Bot 实例
            protocol: RemoteWebhookProtocol 实例
        """
        super().__init__(
            bot=bot,
            logger=bot.logger.with_module("remote-webhook"),
            connect_timeout=protocol.connect_timeout,
            heartbeat_interval=protocol.heartbeat_interval,
            no_msg_timeout=protocol.no_msg_timeout,
        )
        self._protocol = protocol
        self._startup_logged: bool = False

        self._logger.debug(
            f"RemoteWebhookClient 初始化: ws_url={protocol.ws_url}, "
            f"timeout={self._connect_timeout}s, heartbeat={self._heartbeat_interval}s"
        )

    async def run(self) -> None:
        """运行远程 Webhook 连接"""
        while not self._stop_event.is_set():
            try:
                await self._connect()
            except asyncio.CancelledError:
                break
            except AuthenticationError:
                raise
            except NetworkError as e:
                if self._stop_event.is_set():
                    break
                self._reconnect_count += 1
                wait_time = min(5 * self._reconnect_count, 60)
                self._logger.warning(f"与 Webhook 服务器连接中断: {e}")
                self._logger.info(f"将在 {wait_time} 秒后重连...")
                await asyncio.sleep(wait_time)
            except Exception as e:
                if self._stop_event.is_set():
                    break
                self._reconnect_count += 1
                wait_time = min(5 * self._reconnect_count, 60)
                self._logger.warning(f"与 Webhook 服务器连接中断: {e}")
                self._logger.info(f"将在 {wait_time} 秒后重连...")
                await asyncio.sleep(wait_time)

    async def _connect(self) -> None:
        """建立远程 Webhook 连接"""
        session = await self._get_session()

        signature = generate_remote_signature(self._bot.app_id, self._bot.app_secret)

        ping_url = f"{self._protocol.ws_url}/ping?sign={signature}"
        ping_url = ping_url.replace("ws://", "http://").replace("wss://", "https://")

        self._logger.debug(f"正在验证连接参数: {ping_url.split('?')[0]}")

        try:
            async with session.get(
                ping_url, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 401:
                    raise AuthenticationError(
                        "远程 Webhook 签名验证失败，请检查 app_id 和 app_secret"
                    )
                if resp.status != 200:
                    raise NetworkError(
                        f"远程 Webhook 服务器返回错误: HTTP {resp.status}"
                    )
        except aiohttp.ClientConnectorError as e:
            raise NetworkError(f"无法连接到远程 Webhook 服务器: {e.host}:{e.port}")
        except aiohttp.ClientError as e:
            raise NetworkError(f"远程 Webhook 连接检查失败: {e}")

        ws_url_with_sign = f"{self._protocol.ws_url}?sign={signature}"

        self._logger.debug(f"正在连接到远程 Webhook: {self._protocol.ws_url}")

        try:
            timeout = aiohttp.ClientTimeout(total=self._connect_timeout)
            async with session.ws_connect(
                ws_url_with_sign,
                timeout=timeout,
            ) as ws:
                self._ws = ws
                self._connected = True
                self._reconnect_count = 0
                self._last_message_time = time.time()

                if not self._startup_logged:
                    self._startup_logged = True
                    await self._bot._trigger_startup()

                self._logger.info("远程 Webhook 连接成功")

                self._start_heartbeat()

                receive_timeout = self._no_msg_timeout
                while self._connected:
                    try:
                        message = await asyncio.wait_for(
                            ws.receive(), timeout=receive_timeout
                        )
                    except asyncio.TimeoutError:
                        self._logger.warning(
                            f"超过 {receive_timeout} 秒未收到消息，连接可能已断开"
                        )
                        break

                    self._last_message_time = time.time()

                    if message.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(message.data)
                        await self._handle_message(data)

                    elif message.type == aiohttp.WSMsgType.PONG:
                        self._last_heartbeat_ack = time.time()

                    elif message.type == aiohttp.WSMsgType.ERROR:
                        exc = ws.exception()
                        if exc:
                            self._logger.warning(f"远程 Webhook 连接错误: {exc}")
                        else:
                            self._logger.warning("远程 Webhook 连接发生错误")
                        break

                    elif message.type == aiohttp.WSMsgType.CLOSED:
                        close_code = ws.close_code or 0
                        self._logger.debug(f"Webhook 服务器断开连接: code={close_code}")
                        break

        except aiohttp.ServerDisconnectedError:
            self._logger.debug("Webhook 服务器断开连接")
        except asyncio.CancelledError:
            raise
        except aiohttp.ClientConnectorError as e:
            self._logger.error(f"无法连接到远程 Webhook 服务器: {e.host}:{e.port}")
            raise NetworkError(f"无法连接到远程 Webhook 服务器: {e.host}:{e.port}")
        except aiohttp.WSServerHandshakeError as e:
            raise NetworkError(
                f"握手失败 (HTTP {e.status}): "
                f"{'服务器未正确配置 WebSocket 支持' if e.status == 200 else '请检查服务端配置'}"
            )
        except aiohttp.ClientError as e:
            self._logger.warning(f"远程 Webhook 连接失败: {e}")
            raise NetworkError(f"远程 Webhook 连接失败: {e}")
        finally:
            self._connected = False
            await cleanup_task(self._heartbeat_task, "心跳任务")
            self._heartbeat_task = None

    async def _handle_message(self, data: dict[str, Any]) -> None:
        """处理消息"""
        payload = Model.Payload.from_dict(data)
        if payload is None:
            self._logger.warning(f"收到无效的 Payload 数据: {data!r}")
            return

        match payload.op:
            case Model.OpCode.HEARTBEAT_ACK:
                self._last_heartbeat_ack = time.time()
                self._logger.debug("收到心跳 ACK")

            case Model.OpCode.RECONNECT:
                self._logger.debug("收到重连请求，将重新连接")
                await self._reconnect()

            case Model.OpCode.DISPATCH:
                if payload.t:
                    self._dispatch_event(
                        payload.t,
                        payload.d,
                        event_id=payload.id,
                        seq=payload.s,
                        opcode=payload.op,
                    )

    async def _send_heartbeat(self) -> None:
        """发送应用层心跳"""
        await self._ws.send_json({"op": 1})
        self._logger.debug("已发送心跳 (op=1)")
