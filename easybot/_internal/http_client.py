#!/usr/bin/env python3
"""
EasyBot SDK HTTP 客户端模块

提供 HTTP 请求封装和 Webhook 服务器。
"""

import asyncio
import hmac
import json
import socket
import ssl
import time
from functools import lru_cache
from typing import TYPE_CHECKING, Any

import aiohttp
from aiohttp import web

from ..crypto.ed25519 import SigningKey, VerifyKey
from ..exceptions import APIError, AuthenticationError, NetworkError
from ..models import Model
from .constants import (
    API_BASE_URL,
    PERMISSION_DENIED_CODES,
    RETRYABLE_CODES,
    SANDBOX_API_BASE_URL,
    TOKEN_API_URL,
)

if TYPE_CHECKING:
    from ..bot import Bot


@lru_cache(maxsize=128)
def _get_signing_key(seed_bytes: bytes) -> SigningKey:
    """
    缓存 Ed25519 签名密钥，避免重复创建

    Args:
        seed_bytes: 种子字节

    Returns:
        SigningKey: 签名密钥对象
    """
    return SigningKey.from_seed(seed_bytes)


def sign_message(seed: bytes, message: bytes) -> bytes:
    """
    使用 Ed25519 对消息进行签名

    Args:
        seed: 种子字节（用于生成私钥）
        message: 要签名的消息

    Returns:
        64 字节签名
    """
    signing_key = _get_signing_key(seed)
    return signing_key.sign(message)


async def get_local_ip_async() -> str:
    """
    异步获取本机局域网 IP 地址

    在线程池中执行阻塞的 socket 操作，避免阻塞事件循环。

    Returns:
        本机 IP 地址，如果获取失败则返回 127.0.0.1
    """
    loop = asyncio.get_running_loop()
    try:
        return await loop.run_in_executor(None, _get_local_ip_sync)
    except Exception:
        return "127.0.0.1"


def _get_local_ip_sync() -> str:
    """同步获取IP的内部函数"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.1)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    finally:
        try:
            s.close()
        except Exception:
            pass


@lru_cache(maxsize=128)
def _get_verify_key(public_key_bytes: bytes) -> VerifyKey:
    """
    缓存 Ed25519 验证密钥，避免重复创建

    Args:
        public_key_bytes: 公钥字节

    Returns:
        VerifyKey: 验证密钥对象
    """
    return VerifyKey(public_key_bytes)


def verify_signature(public_key: bytes, message: bytes, signature: bytes) -> bool:
    """
    验证 Ed25519 签名

    Args:
        public_key: 公钥字节（32字节）
        message: 原始消息
        signature: 64 字节签名

    Returns:
        签名是否有效
    """
    try:
        verify_key = _get_verify_key(public_key)
        return verify_key.verify(message, signature)
    except Exception:
        return False


@lru_cache(maxsize=32)
def generate_remote_signature(app_id: str, app_secret: str) -> str:
    """
    生成远程 Webhook 客户端连接签名

    使用 Ed25519 对 app_id 进行签名，用于远程客户端鉴权。

    Args:
        app_id: 机器人 App ID
        app_secret: 机器人 App Secret

    Returns:
        签名的十六进制字符串
    """
    signing_key = _get_signing_key(app_secret.encode("utf-8"))
    signature = signing_key.sign(app_id.encode("utf-8"))
    return signature.hex()


def verify_remote_signature(signature: str, app_id: str, app_secret: str) -> bool:
    """
    验证远程 Webhook 客户端签名

    Args:
        signature: 客户端提供的签名（十六进制字符串）
        app_id: 机器人 App ID
        app_secret: 机器人 App Secret

    Returns:
        签名是否有效
    """
    try:
        expected_signature = generate_remote_signature(app_id, app_secret)
        return hmac.compare_digest(signature, expected_signature)
    except Exception:
        return False


class _ConnectorState:
    """
    每个 Bot 实例独立的连接器状态

    将 asyncio 原语和连接器从类变量移到实例中，
    避免多 Bot 实例共享同一组原语导致互相干扰。
    """

    __slots__ = ("lock", "connector", "loop_id", "ref_count")

    def __init__(self):
        self.lock: asyncio.Lock | None = None
        self.connector: aiohttp.TCPConnector | None = None
        self.loop_id: int | None = None
        self.ref_count: int = 0


class HTTPClient:
    """
    HTTP 客户端

    提供 API 请求封装，包括：
    - 自动获取和刷新 access_token
    - 自动重试机制
    - 连接池管理
    - 错误处理和日志记录

    使用按 bot_id 隔离的连接器状态，避免多 Bot 实例共享 asyncio 原语。
    """

    _instances: dict[str, _ConnectorState] = {}

    def __init__(self, bot: "Bot"):
        """
        初始化 HTTP 客户端

        Args:
            bot: Bot 实例
        """
        self._bot = bot
        self._session: aiohttp.ClientSession | None = None
        self._access_token: str | None = None
        self._token_expires_at: float = 0
        self._logger = bot.logger.with_module("http")
        self._has_connector_ref: bool = False

    @classmethod
    def _get_state(cls, bot_id: str) -> _ConnectorState:
        """获取指定 Bot 的连接器状态"""
        if bot_id not in cls._instances:
            cls._instances[bot_id] = _ConnectorState()
        return cls._instances[bot_id]

    async def _get_shared_connector(self) -> aiohttp.TCPConnector:
        """
        获取共享的 TCP 连接器

        使用共享连接器可以在多个 HTTPClient 实例之间复用连接。
        检测事件循环切换时直接创建新 Lock 替换旧的（不经过 None 中间态），
        避免跨循环异常和竞态条件。

        Returns:
            TCPConnector 实例
        """
        state = self._get_state(self._bot.app_id)
        current_loop_id = id(asyncio.get_running_loop())
        if state.loop_id != current_loop_id:
            state.lock = asyncio.Lock()
            state.connector = None
            state.ref_count = 0
            state.loop_id = current_loop_id

        async with state.lock:
            if state.connector is None or state.connector.closed:
                state.connector = aiohttp.TCPConnector(
                    limit=100,
                    limit_per_host=30,
                    ttl_dns_cache=30,
                    enable_cleanup_closed=True,
                    force_close=False,
                    keepalive_timeout=10,
                )
            state.ref_count += 1
            return state.connector

    async def _release_connector(self) -> None:
        """释放连接器引用"""
        state = self._instances.get(self._bot.app_id)
        if state is None:
            return
        current_loop_id = id(asyncio.get_running_loop())
        if state.loop_id != current_loop_id:
            state.lock = asyncio.Lock()
            state.connector = None
            state.ref_count = 0
            state.loop_id = current_loop_id
            return
        async with state.lock:
            state.ref_count -= 1
            if state.ref_count <= 0 and state.connector:
                await state.connector.close()
                state.connector = None
                state.ref_count = 0

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建 aiohttp session"""
        if self._session is None or self._session.closed:
            connector = await self._get_shared_connector()
            self._has_connector_ref = True
            timeout = aiohttp.ClientTimeout(total=self._bot.api_timeout)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                connector_owner=False,
            )
        return self._session

    async def close(self) -> None:
        """关闭 HTTP 客户端"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
        if self._has_connector_ref:
            await self._release_connector()
            self._has_connector_ref = False

    async def __aenter__(self) -> "HTTPClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        await self.close()
        return False

    async def get_access_token(self) -> str:
        """
        获取 access_token

        Returns:
            access_token 字符串

        Raises:
            AuthenticationError: 认证失败时抛出
        """
        if self._access_token and time.time() < self._token_expires_at - 60:
            self._logger.debug(
                f"使用缓存的 access_token，剩余有效时间: {int(self._token_expires_at - time.time())}秒"
            )
            return self._access_token

        session = await self._get_session()

        url = TOKEN_API_URL

        payload = {
            "appId": self._bot.app_id,
            "clientSecret": self._bot._app_secret,
        }

        headers = {"Content-Type": "application/json"}

        self._logger.debug("正在获取新的 access_token...")

        try:
            async with session.post(url, json=payload, headers=headers) as response:
                data = await response.json()

                if response.status != 200:
                    self._logger.error(
                        f"获取 access_token 失败: HTTP {response.status}, response={data}"
                    )
                    raise AuthenticationError(f"获取 access_token 失败: {data}")

                if data.get("code", 0) != 0:
                    self._logger.error(
                        f"获取 access_token 失败: code={data.get('code')}, message={data.get('message')}"
                    )
                    raise AuthenticationError(
                        f"获取 access_token 失败: [{data.get('code')}] {data.get('message')}"
                    )

                self._access_token = data["access_token"]
                expires_in = data.get("expires_in", 7200)
                if isinstance(expires_in, str):
                    expires_in = int(expires_in)
                self._token_expires_at = time.time() + expires_in

                self._logger.debug(f"access_token 获取成功，有效期: {expires_in}秒")
                return self._access_token

        except aiohttp.ClientError as e:
            self._logger.error(f"获取 access_token 网络错误: {e}")
            raise NetworkError(f"网络错误: {e}")

    async def request(
        self,
        method: str,
        endpoint: str,
        **kwargs,
    ) -> dict[str, Any]:
        """
        发送 HTTP 请求

        Args:
            method: HTTP 方法
            endpoint: API 端点
            **kwargs: 其他请求参数

        Returns:
            响应数据

        Raises:
            APIError: API 错误时抛出
            NetworkError: 网络错误时抛出
        """
        session = await self._get_session()
        base_url = SANDBOX_API_BASE_URL if self._bot.is_sandbox else API_BASE_URL
        url = f"{base_url}{endpoint}"

        access_token = await self.get_access_token()
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"QQBot {access_token}"
        headers["X-Union-Appid"] = self._bot.app_id

        # FormData 类型不设置 Content-Type，让 aiohttp 自动处理
        is_form_data = isinstance(kwargs.get("data"), aiohttp.FormData)
        if (
            "Content-Type" not in headers
            and method in ("POST", "PUT", "PATCH")
            and not is_form_data
        ):
            headers["Content-Type"] = "application/json"

        retry_count = 0
        max_retry = self._bot.is_retry

        self._logger.debug(f"API 请求: {method} {endpoint}")

        while retry_count <= max_retry:
            try:
                async with session.request(
                    method, url, headers=headers, **kwargs
                ) as response:
                    trace_id = response.headers.get("X-Tps-trace-ID")

                    if response.status == 204:
                        self._logger.debug(
                            f"API 响应: {method} {endpoint} -> 204 No Content"
                        )
                        return {}

                    try:
                        data = await response.json()
                    except Exception:
                        data = {}

                    if response.status == 200:
                        self._logger.debug(f"API 响应: {method} {endpoint} -> 200 OK")
                        return data

                    code = data.get("code", response.status)
                    message = data.get("message", "Unknown error")

                    if code in RETRYABLE_CODES and retry_count < max_retry:
                        retry_count += 1
                        wait_time = 1 * retry_count
                        self._logger.warning(
                            f"API 请求失败 (可重试): [{code}] {message}, "
                            f"第 {retry_count}/{max_retry} 次重试，等待 {wait_time}秒"
                        )
                        await asyncio.sleep(wait_time)
                        continue

                    if (
                        self._bot.no_permission_warning
                        and code in PERMISSION_DENIED_CODES
                    ):
                        self._logger.warning(
                            f"权限不足: 机器人缺少执行此操作的权限 [{code}] {message} (endpoint: {endpoint})"
                        )

                    if self._bot.is_log_error:
                        self._logger.error(
                            f"API Error: [{code}] {message} (TraceID: {trace_id})"
                        )

                    raise APIError(code, message, trace_id)

            except aiohttp.ClientError as e:
                if retry_count < max_retry:
                    retry_count += 1
                    wait_time = 1 * retry_count
                    self._logger.warning(
                        f"网络错误: {e}, 第 {retry_count}/{max_retry} 次重试，等待 {wait_time}秒"
                    )
                    await asyncio.sleep(wait_time)
                    continue
                self._logger.error(f"网络错误 (已达最大重试次数): {e}")
                raise NetworkError(f"网络错误: {e}")

        self._logger.error("请求重试次数已达上限")
        raise NetworkError("请求重试次数已达上限")

    async def get(self, endpoint: str, **kwargs) -> dict[str, Any]:
        """发送 GET 请求"""
        return await self.request("GET", endpoint, **kwargs)

    async def post(self, endpoint: str, **kwargs) -> dict[str, Any]:
        """发送 POST 请求"""
        return await self.request("POST", endpoint, **kwargs)

    async def put(self, endpoint: str, **kwargs) -> dict[str, Any]:
        """发送 PUT 请求"""
        return await self.request("PUT", endpoint, **kwargs)

    async def patch(self, endpoint: str, **kwargs) -> dict[str, Any]:
        """发送 PATCH 请求"""
        return await self.request("PATCH", endpoint, **kwargs)

    async def delete(self, endpoint: str, **kwargs) -> dict[str, Any]:
        """发送 DELETE 请求"""
        return await self.request("DELETE", endpoint, **kwargs)


class WebhookServer:
    """
    Webhook 服务器

    用于接收 QQ 机器人平台的 Webhook 回调。
    同时提供 WebSocket 端点供远程客户端连接，实现事件转发。
    """

    def __init__(self, bot: "Bot", protocol):
        """
        初始化 Webhook 服务器

        Args:
            bot: Bot 实例
            protocol: WebhookProtocol 实例
        """
        self._bot = bot
        self._protocol = protocol
        self._logger = bot.logger.with_module("webhook")
        self._runner: Any | None = None
        self._site: Any | None = None
        self._stop_event: asyncio.Event = asyncio.Event()

        self._ws_clients: set = set()
        self._ws_clients_lock: asyncio.Lock = asyncio.Lock()

    async def run(self) -> None:
        """运行 Webhook 服务器"""
        app = web.Application()
        app.router.add_post(self._protocol.webhook_path, self._handle_webhook)
        app.router.add_get(self._protocol.ws_path, self._handle_websocket)
        app.router.add_get(f"{self._protocol.ws_path}/ping", self._handle_ping)

        self._runner = web.AppRunner(app)
        await self._runner.setup()

        ssl_context = None
        if self._protocol.path_to_ssl_cert and self._protocol.path_to_ssl_cert_key:
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(
                self._protocol.path_to_ssl_cert,
                self._protocol.path_to_ssl_cert_key,
            )

        self._site = web.TCPSite(
            self._runner,
            "0.0.0.0",
            self._protocol.port,
            ssl_context=ssl_context,
        )

        await self._site.start()

        local_ip = await get_local_ip_async()

        self._logger.info(f"Webhook 服务器已启动，监听端口 {self._protocol.port}")
        self._logger.info(
            f"Webhook 端点: http://{local_ip}:{self._protocol.port}{self._protocol.webhook_path} | https://{local_ip}:{self._protocol.port}{self._protocol.webhook_path}"
        )
        self._logger.info(
            "如果需要使用https或wss，请在配置中指定证书路径和密钥路径，或者反向代理绑定域名到本程序监听的端口"
        )

        await self._bot._trigger_startup()
        self._logger.info("机器人启动成功")

        while not self._stop_event.is_set():
            await self._stop_event.wait()

    async def stop(self) -> None:
        """停止 Webhook 服务器"""
        self._stop_event.set()

        async with self._ws_clients_lock:
            for ws in list(self._ws_clients):
                try:
                    await ws.close(code=1001, message=b"Server shutting down")
                except Exception:
                    pass
            self._ws_clients.clear()

        if self._site is not None:
            try:
                await self._site.stop()
            except Exception:
                pass
            finally:
                self._site = None

        if self._runner is not None:
            try:
                await self._runner.cleanup()
            except (AttributeError, TypeError):
                pass
            except Exception:
                pass
            finally:
                self._runner = None

        self._logger.info("Webhook 服务器已停止")

    async def _handle_webhook(self, request: web.Request) -> web.Response:
        """处理 Webhook 回调"""
        request_time = time.strftime("%Y-%m-%d %H:%M:%S")
        client_ip = request.remote or "unknown"
        self._logger.debug(f"收到 Webhook 请求: ip={client_ip}, time={request_time}")

        try:
            body = await request.read()
            signature = request.headers.get("X-Signature-Ed25519", "")
            timestamp = request.headers.get("X-Signature-Timestamp", "")

            self._logger.debug(
                f"请求头: X-Signature-Ed25519={'(存在)' if signature else '(不存在)'}, "
                f"X-Signature-Timestamp={'(存在)' if timestamp else '(不存在)'}"
            )

            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                self._logger.error("无效的 JSON 数据")
                return web.Response(status=400, text="Invalid JSON")

            payload = Model.Payload.from_dict(data)
            if payload is None:
                self._logger.warning(f"收到无效的 Webhook Payload: {data!r}")
                return web.Response(status=400, text="Invalid payload")

            if payload.op == Model.OpCode.WEBHOOK_VALIDATION:
                self._logger.debug("识别为回调地址验证请求 (op=13)")
                return await self._handle_validation(data, body)

            self._logger.debug("识别为普通事件回调，开始签名验证")
            if not self._verify_signature(body, signature, timestamp):
                self._logger.warning("签名验证失败")
                return web.Response(status=401, text="Invalid signature")

            event_type = payload.t or "UNKNOWN"
            self._logger.debug(f"签名验证通过，分发事件: {event_type}")
            task = asyncio.create_task(self._dispatch_event(payload))
            task.add_done_callback(self._on_dispatch_task_done)

            return web.Response(status=200)

        except Exception as e:
            self._logger.exception(f"处理 Webhook 回调失败: {e}")
            return web.Response(status=500, text="Internal Server Error")

    async def _handle_websocket(self, request: web.Request) -> web.WebSocketResponse:
        """
        处理 WebSocket 连接

        远程客户端通过 WebSocket 连接，接收转发的事件。
        使用首条消息鉴权：客户端连接后发送 {"op": 0, "d": {"sign": "..."}},
        服务端验证签名后才开始转发事件。
        """
        ws = web.WebSocketResponse(heartbeat=30, autoping=True)
        await ws.prepare(request)

        client_ip = request.remote or "unknown"

        try:
            auth_msg = await asyncio.wait_for(ws.receive(), timeout=10)
        except asyncio.TimeoutError:
            self._logger.warning(f"远程客户端鉴权超时: ip={client_ip}")
            await ws.close(code=4002, message=b"Auth timeout")
            return ws

        if auth_msg.type != aiohttp.WSMsgType.TEXT:
            self._logger.warning(f"远程客户端未发送鉴权消息: ip={client_ip}")
            await ws.close(code=4001, message=b"Missing authentication")
            return ws

        try:
            auth_data = json.loads(auth_msg.data)
        except json.JSONDecodeError:
            self._logger.warning(f"远程客户端鉴权消息格式错误: ip={client_ip}")
            await ws.close(code=4001, message=b"Invalid auth message")
            return ws

        if auth_data.get("op") != 0:
            self._logger.warning(f"远程客户端未发送鉴权操作: ip={client_ip}")
            await ws.close(code=4001, message=b"Missing authentication")
            return ws

        signature = auth_data.get("d", {}).get("sign")
        if not signature:
            self._logger.warning(f"远程客户端缺少签名参数: ip={client_ip}")
            await ws.close(code=4001, message=b"Missing signature")
            return ws

        if not verify_remote_signature(
            signature, self._bot.app_id, self._bot._app_secret
        ):
            self._logger.warning(f"远程客户端签名验证失败: ip={client_ip}")
            await ws.close(code=4001, message=b"Invalid signature")
            return ws

        async with self._ws_clients_lock:
            self._ws_clients.add(ws)

        self._logger.info(f"远程 Webhook 客户端连接成功: ip={client_ip}")
        await ws.send_json({"op": 0, "d": {"message": "Authenticated"}})

        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    if data.get("op") == 1:
                        await ws.send_json({"op": 11})
                except json.JSONDecodeError:
                    pass
            elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                break

        async with self._ws_clients_lock:
            self._ws_clients.discard(ws)

        self._logger.debug(f"远程 Webhook 客户端断开: ip={client_ip}")
        return ws

    async def _handle_ping(self, request: web.Request) -> web.Response:
        """
        健康检查端点

        用于远程客户端验证连接参数是否正确。
        客户端通过 /ws/ping 端点，在请求头 X-Signature 中传递签名来验证。

        Returns:
            200 OK 如果签名有效
            401 Unauthorized 如果签名无效
        """
        signature = request.headers.get("X-Signature")
        if not signature:
            return web.Response(status=400, text="Missing signature")

        if verify_remote_signature(signature, self._bot.app_id, self._bot._app_secret):
            return web.Response(status=200, text="OK")

        return web.Response(status=401, text="Invalid signature")

    async def _broadcast_event(self, data: dict) -> None:
        """
        广播事件到所有连接的 WebSocket 客户端

        Args:
            data: 事件数据
        """
        if not self._ws_clients:
            return

        message = json.dumps(data)
        dead_clients = set()

        async with self._ws_clients_lock:
            for ws in self._ws_clients:
                try:
                    await ws.send_str(message)
                except Exception:
                    dead_clients.add(ws)

            for ws in dead_clients:
                self._ws_clients.discard(ws)

    def _verify_signature(self, body: bytes, signature: str, timestamp: str) -> bool:
        """
        验证回调签名

        根据官方文档，验证流程：
        1. 从 app_secret 生成 Ed25519 密钥对
        2. 使用公钥验证签名

        Args:
            body: 请求体
            signature: 签名
            timestamp: 时间戳

        Returns:
            签名是否有效
        """
        if not signature or not timestamp:
            self._logger.warning("签名验证失败: 缺少签名或时间戳头")
            return False

        try:
            seed = self._bot._app_secret.encode("utf-8")
            while len(seed) < 32:
                seed = seed + seed
            seed = seed[:32]

            signing_key = _get_signing_key(seed)
            public_key = bytes(signing_key.get_public_key())

            message = timestamp.encode() + body
            sig_bytes = bytes.fromhex(signature)

            verify_key = _get_verify_key(public_key)
            result = verify_key.verify(message, sig_bytes)

            if not result:
                self._logger.warning("签名验证失败")

            return result
        except Exception as e:
            self._logger.error(f"签名验证异常: {type(e).__name__}: {e}")
            return False

    async def _handle_validation(self, data: dict, body: bytes) -> web.Response:
        """
        处理回调地址验证

        根据官方文档，验证流程：
        1. 收到 op=13 的验证请求，包含 plain_token 和 event_ts
        2. 使用 bot_secret 生成 Ed25519 私钥
        3. 对 event_ts + plain_token 进行签名
        4. 返回 plain_token 和 signature

        Args:
            data: 请求数据
            body: 原始请求体

        Returns:
            验证响应
        """
        self._logger.info("收到回调地址验证请求")
        self._logger.debug(f"原始请求体: {body.decode('utf-8', errors='replace')}")

        d = data.get("d", {})
        plain_token = d.get("plain_token", "")
        event_ts = d.get("event_ts", "")

        self._logger.debug(
            f"解析验证参数: plain_token={plain_token}, event_ts={event_ts}"
        )

        secret = self._bot._app_secret.encode("utf-8")
        self._logger.debug(f"Seed 生成: 原始 secret 长度={len(secret)} 字节")

        seed = secret
        while len(seed) < 32:
            seed = seed + seed
        seed = seed[:32]
        self._logger.debug(
            f"Seed 生成: repeat 后长度={len(seed)} 字节, seed(hex)={seed.hex()[:32]}..."
        )

        msg = (event_ts + plain_token).encode("utf-8")
        self._logger.debug(
            f"签名消息组合: event_ts + plain_token = '{event_ts} + {plain_token}' = {msg!r}"
        )

        signature = sign_message(seed, msg)
        signature_hex = signature.hex()

        self._logger.info(f"生成签名: {signature_hex}")

        response_data = {
            "plain_token": plain_token,
            "signature": signature_hex,
        }
        self._logger.debug(f"返回验证响应: {json.dumps(response_data)}")

        return web.Response(
            status=200,
            content_type="application/json",
            text=json.dumps(response_data),
        )

    async def _dispatch_event(self, payload: Model.Payload) -> None:
        """
        分发事件

        Args:
            payload: Gateway Payload 对象（包含 id, op, d, s, t 字段）
        """
        event_type = payload.t
        if not event_type:
            return

        await self._broadcast_event(payload._raw_data)

        await self._bot._event_dispatcher.dispatch(
            event_type, payload.d, event_id=payload.id, seq=payload.s, opcode=payload.op
        )

    def _on_dispatch_task_done(self, task: asyncio.Task) -> None:
        """Webhook 事件分发任务完成回调，捕获并记录未处理的异常"""
        if task.cancelled():
            return
        if exc := task.exception():
            self._logger.exception(f"Webhook 事件分发任务执行失败: {exc}")
