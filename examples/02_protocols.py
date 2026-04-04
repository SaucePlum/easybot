#!/usr/bin/env python3
"""
EasyBot SDK 示例 02：三种协议的使用方法

展示 EasyBot 支持的三种连接协议：
1. WebSocket - 最常用，自动维持长连接
2. Webhook - 需要公网IP或内网穿透
3. 远程 Webhook - 连接远程 Webhook 服务器

运行前请将 app_id 和 app_secret 替换为你的机器人凭证
"""

from easybot import Bot, Model, Proto


def websocket_example() -> Bot:
    """
    WebSocket 协议（推荐，最简单）

    适用场景：
    - 本地开发测试
    - 小型机器人项目
    - 不需要公网IP的场景

    Returns:
        Bot: 配置好的 Bot 实例
    """
    # 方式1：不指定 protocol 参数，默认就是 WebSocket
    bot_default = Bot(
        app_id="your_app_id",
        app_secret="your_app_secret",
    )

    # 方式2：显式指定 WebSocket 参数
    bot_explicit = Bot(
        app_id="your_app_id",
        app_secret="your_app_secret",
        protocol=Proto.websocket(
            shard_no=0,  # 当前分片编号（从 0 开始）
            total_shard=1,  # 总分片数
            connect_timeout=30.0,  # WebSocket 连接超时时间（秒）
            disable_reconnect_on_not_recv_msg=1000,  # 长时间未收到消息后重连时间
        ),
    )

    return bot_default


def webhook_example() -> Bot:
    """
    Webhook 协议（需要公网访问）

    适用场景：
    - 有公网IP的服务器
    - 使用反向代理（如 nginx）处理 HTTPS
    - 需要与其他服务共享端口的场景

    注意：需要在 QQ 开发者平台配置 Webhook 地址

    Returns:
        Bot: 配置好的 Bot 实例
    """
    bot = Bot(
        app_id="your_app_id",
        app_secret="your_app_secret",
        protocol=Proto.webhook(
            port=8080,  # Webhook 监听端口
            path="/",  # Webhook 路径
            # SSL 证书配置（如使用反向代理可留空）
            # path_to_ssl_cert="/path/to/cert.pem",
            # path_to_ssl_cert_key="/path/to/key.pem",
        ),
    )
    return bot


def remote_webhook_example() -> Bot:
    """
    远程 Webhook 协议（连接远程服务器）

    适用场景：
    - 远程 Webhook 服务器已部署
    - 需要在本地连接远程服务
    - 安全考虑（避免在本地传输敏感信息）

    注意：需要在远程服务端配置机器人基本信息

    Returns:
        Bot: 配置好的 Bot 实例
    """
    bot = Bot(
        app_id="your_app_id",
        app_secret="your_app_secret",
        protocol=Proto.remote_webhook(
            url="wss://your-server.com",  # 远程服务器地址
            connect_timeout=15.0,  # 连接超时时间
            heartbeat_interval=40.0,  # 心跳间隔
            no_msg_timeout=180.0,  # 无消息超时时间
        ),
    )
    return bot


def main() -> None:
    """
    选择一种协议运行示例
    """
    # 取消注释你想使用的协议示例

    # bot = websocket_example()
    # bot = webhook_example()
    bot = remote_webhook_example()

    # 添加事件处理器
    @bot.on_group_message
    async def handle_group(msg: Model.GroupMessage) -> None:
        await msg.reply("Hello from EasyBot!")

    # 启动机器人
    bot.start()


if __name__ == "__main__":
    main()
