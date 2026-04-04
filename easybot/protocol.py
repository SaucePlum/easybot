#!/usr/bin/env python3
"""
EasyBot SDK 协议模块

提供 WebSocket、Webhook 和远程 Webhook 三种连接协议。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ._internal.http_client import WebhookServer
from ._internal.ws_client import RemoteWebhookClient, WebSocketClient

if TYPE_CHECKING:
    from .bot import Bot


class Protocol(ABC):
    """协议基类"""

    _client: Any = None

    @abstractmethod
    async def run(self, bot: "Bot"):
        """运行协议"""
        pass

    async def stop(self):
        """停止协议，释放资源"""
        if self._client is not None:
            try:
                if hasattr(self._client, "close"):
                    await self._client.close()
                elif hasattr(self._client, "stop"):
                    await self._client.stop()
            except Exception:
                pass
            finally:
                self._client = None


@dataclass
class WebSocketProtocol(Protocol):
    """
    WebSocket 连接协议

    Attributes:
        shard_no: 当前分片编号（从 0 开始）
        total_shard: 总分片数
        disable_reconnect_on_not_recv_msg: 长时间未收到消息后重连时间（秒）
        connect_timeout: WebSocket 连接超时时间（秒）
    """

    shard_no: int = 0
    total_shard: int = 1
    disable_reconnect_on_not_recv_msg: float = 1000
    connect_timeout: float = 30.0
    _client: Any = field(default=None, repr=False, compare=False)

    async def run(self, bot: "Bot"):
        """运行 WebSocket 连接"""
        self._client = WebSocketClient(bot, self)
        await self._client.run()


@dataclass
class WebhookProtocol(Protocol):
    """
    Webhook 连接协议

    Attributes:
        port: Webhook 挂载的本机端口
        path: Webhook 挂载的基础路径
        path_to_ssl_cert: SSL 证书路径
        path_to_ssl_cert_key: SSL 证书密钥路径
    """

    port: int
    path: str = "/"
    path_to_ssl_cert: str | None = None
    path_to_ssl_cert_key: str | None = None
    _client: Any = field(default=None, repr=False, compare=False)

    @property
    def webhook_path(self) -> str:
        """Webhook 端点路径"""
        base = self.path.rstrip("/")
        return base if base else "/"

    @property
    def ws_path(self) -> str:
        """WebSocket 端点路径"""
        base = self.path.rstrip("/")
        return f"{base}/ws" if base else "/ws"

    async def run(self, bot: "Bot"):
        """运行 Webhook 服务"""
        self._client = WebhookServer(bot, self)
        await self._client.run()

    async def stop(self):
        """停止 Webhook 服务"""
        if self._client is not None:
            try:
                await self._client.stop()
            except Exception:
                pass
            finally:
                self._client = None


@dataclass
class RemoteWebhookProtocol(Protocol):
    """
    远程 Webhook 连接协议

    Attributes:
        url: 远程 Webhook 服务器地址，SDK 会自动拼接 /ws 路径，支持以下格式：
            - ws://example.com
            - wss://example.com
            - http://example.com (自动转换为 ws://)
            - https://example.com (自动转换为 wss://)
        connect_timeout: WebSocket 连接超时时间（秒）
        heartbeat_interval: 心跳间隔时间（秒）
        no_msg_timeout: 长时间未收到消息后重连时间（秒）
    """

    url: str
    connect_timeout: float = 15.0
    heartbeat_interval: float = 40.0
    no_msg_timeout: float = 180.0
    _client: Any = field(default=None, repr=False, compare=False)

    @property
    def ws_url(self) -> str:
        """
        获取 WebSocket URL，自动转换协议并拼接 /ws 路径

        http:// -> ws://
        https:// -> wss://
        自动在 URL 末尾拼接 /ws
        """
        url = self.url.strip()
        if url.startswith("http://"):
            url = "ws://" + url[7:]
        elif url.startswith("https://"):
            url = "wss://" + url[8:]

        if not url.endswith("/ws"):
            url = url.rstrip("/") + "/ws"
        return url

    async def run(self, bot: "Bot"):
        """运行远程 Webhook 连接"""
        self._client = RemoteWebhookClient(bot, self)
        await self._client.run()


class Proto:
    """
    协议工厂类

    提供三种连接方式的创建方法。
    """

    @staticmethod
    def websocket(
        shard_no: int = 0,
        total_shard: int = 1,
        disable_reconnect_on_not_recv_msg: float = 1000,
        connect_timeout: float = 30.0,
    ) -> WebSocketProtocol:
        """
        创建 WebSocket 连接协议

        Args:
            shard_no: 当前分片编号（从 0 开始），默认 0
            total_shard: 总分片数，默认 1
            disable_reconnect_on_not_recv_msg: 长时间未收到消息后重连时间（秒），默认 1000
            connect_timeout: WebSocket 连接超时时间（秒），默认 30

        Returns:
            WebSocketProtocol 实例

        注意:
            - 分片编号从 0 开始，最大为 total_shard - 1
            - 如果官方建议的分片数大于当前配置，SDK 会输出警告日志
            - 建议通过 /gateway/bot 接口获取官方建议的分片数
        """
        return WebSocketProtocol(
            shard_no=shard_no,
            total_shard=total_shard,
            disable_reconnect_on_not_recv_msg=disable_reconnect_on_not_recv_msg,
            connect_timeout=connect_timeout,
        )

    @staticmethod
    def webhook(
        port: int,
        path: str = "/",
        path_to_ssl_cert: str | None = None,
        path_to_ssl_cert_key: str | None = None,
    ) -> WebhookProtocol:
        """
        创建 Webhook 连接协议

        Args:
            port: Webhook 挂载的本机端口
            path: Webhook 挂载的基础路径，默认 '/'
                - Webhook 端点: {path}
                - WebSocket 端点: {path}/ws
            path_to_ssl_cert: SSL 证书路径，如使用反向代理可填 None
            path_to_ssl_cert_key: SSL 证书密钥路径，如使用反向代理可填 None

        Returns:
            WebhookProtocol 实例

        注意:
            如果使用了 nginx 等反向代理处理 https，SSL 参数可填 None
        """
        return WebhookProtocol(
            port=port,
            path=path,
            path_to_ssl_cert=path_to_ssl_cert,
            path_to_ssl_cert_key=path_to_ssl_cert_key,
        )

    @staticmethod
    def remote_webhook(
        url: str,
        connect_timeout: float = 15.0,
        heartbeat_interval: float = 40.0,
        no_msg_timeout: float = 180.0,
    ) -> RemoteWebhookProtocol:
        """
        创建远程 Webhook 连接协议

        Args:
            url: 远程 Webhook 服务器地址，SDK 会自动拼接 /ws 路径，支持以下格式：
                - ws://example.com
                - wss://example.com
                - http://example.com (自动转换为 ws://)
                - https://example.com (自动转换为 wss://)
            connect_timeout: WebSocket 连接超时时间（秒），默认 15
            heartbeat_interval: 心跳间隔时间（秒），默认 40
            no_msg_timeout: 长时间未收到消息后重连时间（秒），默认 180

        Returns:
            RemoteWebhookProtocol 实例

        注意:
            由于安全理由，需要在远程服务端配置机器人基本信息后，本地进行连接
            避免在非本地环境传输敏感信息
        """
        return RemoteWebhookProtocol(
            url=url,
            connect_timeout=connect_timeout,
            heartbeat_interval=heartbeat_interval,
            no_msg_timeout=no_msg_timeout,
        )
