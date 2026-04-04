#!/usr/bin/env python3
"""
EasyBot SDK Bot 主类模块

提供机器人核心功能，包括：
- 生命周期管理
- 事件处理器注册
- 协议管理
"""

import asyncio
import importlib.util
import os
import sys
from collections.abc import Callable
from pathlib import Path

from ._internal.constants import EVENT_DISPLAY_NAMES
from ._internal.event_dispatcher import EventDispatcher
from ._internal.intent import (
    EVENT_INTENT_MAP,
    Intent,
    IntentCalculator,
    get_event_types_by_intent,
)
from ._internal.lifecycle import LifecycleManager
from .api import API
from .logger import Logger
from .plugins import BotAdminManager, CommandValidScenes, Plugins
from .protocol import Proto, Protocol
from .sandbox import SandBox
from .session import SessionManager
from .version import __version__


class Bot:
    """
    QQ 机器人主类

    示例:
        # WebSocket 模式（默认）
        bot = Bot(
            app_id="your_appid",
            app_secret="your_secret"
        )

        # Webhook 模式
        bot = Bot(
            app_id="your_appid",
            app_secret="your_secret",
            protocol=Proto.webhook(port=8080)
        )

        @bot.on_guild_message
        async def handle_message(msg):
            await bot.api.send_guild_message(
                channel_id=msg.channel_id,
                content="收到消息！"
            )

        bot.start()
    """

    def __init__(
        self,
        app_id: str,
        app_secret: str,
        is_private: bool = False,
        is_sandbox: bool = False,
        sandbox: SandBox | None = None,
        protocol: Protocol | None = None,
        is_retry: int = 3,
        is_log_error: bool = True,
        no_permission_warning: bool = True,
        api_timeout: int = 20,
        is_debug: bool = False,
        auto_load_plugins: bool = False,
        plugins_dir: str = "plugins",
        plugins_recursive: bool = False,
    ):
        """
        初始化机器人

        Args:
            app_id: 机器人 AppID
            app_secret: 机器人密钥
            is_private: 是否私域机器人，默认为公域
            is_sandbox: 是否开启沙箱环境测试
            sandbox: 沙箱环境配置
            protocol: 协议配置，默认为 Proto.websocket()
            is_retry: API 重试次数，默认 3 次
            is_log_error: 是否自动记录 API 错误，默认开启
            no_permission_warning: 是否开启权限不足警告，默认开启
            api_timeout: API 请求超时时间（秒），默认 20 秒
            is_debug: 是否开启调试模式，默认关闭
            auto_load_plugins: 是否自动加载插件目录中的插件，默认False
            plugins_dir: 插件目录路径，默认"plugins"
            plugins_recursive: 是否递归扫描子目录加载插件，默认False
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.is_private = is_private
        self.is_sandbox = is_sandbox
        self.sandbox = sandbox
        self.is_retry = is_retry
        self.is_log_error = is_log_error
        self.no_permission_warning = no_permission_warning
        self.api_timeout = api_timeout
        self.is_debug = is_debug
        self.auto_load_plugins = auto_load_plugins
        self.plugins_dir = plugins_dir
        self.plugins_recursive = plugins_recursive

        self._bot_id: str | None = None
        self._bot_admin_manager = BotAdminManager()

        self.logger = Logger(bot_id=app_id, is_debug=is_debug, module_name="bot")

        self.logger.info(
            f"本次程序进程ID：{os.getpid()} | SDK版本：{__version__} | 即将开始运行机器人……"
        )

        self.protocol = protocol or Proto.websocket()

        self._event_handlers: dict[str, Callable] = {}
        self._intents = 0
        self._intent_calculator = IntentCalculator()
        self._running = False
        self._event_dispatcher = EventDispatcher(self, self.logger)

        self.api: API = API(self)

        self._session_manager = SessionManager(self)
        self._session_manager.set_api(self.api)

        self._lifecycle = LifecycleManager(self, self.logger)

        self.logger.debug(
            f"Bot 初始化完成: is_private={is_private}, is_sandbox={is_sandbox}, "
            f"protocol={type(self.protocol).__name__}, retry={is_retry}, timeout={api_timeout}s"
        )

    def start(self) -> None:
        """
        启动机器人

        使用初始化时配置的协议（WebSocket/Webhook/Remote Webhook）
        这是一个阻塞方法，会一直运行直到机器人停止
        """
        self.logger.info(f"正在启动机器人 (AppID: {self.app_id})")
        try:
            asyncio.run(self.start_async())
        except KeyboardInterrupt:
            self.logger.info("收到中断信号 (Ctrl+C)，正在停止...")
        except Exception as e:
            self.logger.exception(f"机器人运行时发生未捕获异常: {e}")
        finally:
            asyncio.run(self.stop_async())

    async def start_async(self) -> None:
        """
        异步启动机器人

        适用于需要在外部管理事件循环的场景
        """
        self._running = True
        self.logger.info(f"机器人正在启动... (AppID: {self.app_id})")

        if self.is_debug:
            self.logger.debug("调试模式已开启，将输出详细调试信息")
            self.logger.debug(
                f"计算后的 Intent 值: {self._intents} (0x{self._intents:X})"
            )

        # 启动会话管理器
        self._session_manager.start(asyncio.get_event_loop())

        await self.protocol.run(self)

    def stop(self) -> None:
        """
        停止机器人（同步版本）

        注意：此方法仅设置停止标志，实际资源清理需要调用 stop_async()
        """
        self._running = False
        self.logger.info("机器人停止标志已设置")

    async def stop_async(self) -> None:
        """
        异步停止机器人并清理所有资源

        包括：
        - 触发关闭事件
        - 关闭 API HTTP 客户端
        - 停止协议连接
        - 释放所有网络资源
        """
        self._running = False

        try:
            await self._lifecycle.close()
        except Exception as e:
            self.logger.error(f"关闭生命周期管理器时出错: {e}")

        try:
            await self.api.close()
        except Exception as e:
            self.logger.error(f"关闭 API 客户端时出错: {e}")

        try:
            await self.protocol.stop()
        except Exception as e:
            self.logger.error(f"停止协议时出错: {e}")

        self.logger.info("机器人已完全停止，所有资源已释放")

    async def __aenter__(self) -> "Bot":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        await self.stop_async()
        return False

    def _register_handler(
        self,
        event_type: str,
        func: Callable,
        intent: int,
    ) -> None:
        """
        注册事件处理器

        Args:
            event_type: 事件类型
            func: 处理函数
            intent: Intent 值
        """
        self._event_handlers[event_type] = func
        self._intents |= intent
        self._intent_calculator.register_event(event_type)
        display_name = EVENT_DISPLAY_NAMES.get(event_type, event_type)
        self.logger.info(f"{display_name}事件订阅成功")

    @property
    def on_guild_message(self):
        """
        频道@机器人消息事件

        事件类型: AT_MESSAGE_CREATE
        Intent: PUBLIC_GUILD_MESSAGES (1<<30)

        示例:
            @bot.on_guild_message
            async def handle_message(msg: Model.GuildMessage):
                await bot.api.send_guild_message(
                    channel_id=msg.channel_id,
                    content=f"收到：{msg.content}"
                )
        """

        def decorator(func: Callable):
            self._register_handler(
                "AT_MESSAGE_CREATE", func, Intent.PUBLIC_GUILD_MESSAGES
            )
            return func

        return decorator

    @property
    def on_group_message(self):
        """
        群聊@机器人消息事件

        事件类型: GROUP_AT_MESSAGE_CREATE
        Intent: GROUP_AND_C2C_EVENT (1<<25)
        """

        def decorator(func: Callable):
            self._register_handler(
                "GROUP_AT_MESSAGE_CREATE", func, Intent.GROUP_AND_C2C_EVENT
            )
            return func

        return decorator

    @property
    def on_c2c_message(self):
        """
        单聊消息事件

        事件类型: C2C_MESSAGE_CREATE
        Intent: GROUP_AND_C2C_EVENT (1<<25)
        """

        def decorator(func: Callable):
            self._register_handler(
                "C2C_MESSAGE_CREATE", func, Intent.GROUP_AND_C2C_EVENT
            )
            return func

        return decorator

    @property
    def on_direct_message(self):
        """
        频道私信消息事件

        事件类型: DIRECT_MESSAGE_CREATE
        Intent: DIRECT_MESSAGE (1<<12)
        """

        def decorator(func: Callable):
            self._register_handler("DIRECT_MESSAGE_CREATE", func, Intent.DIRECT_MESSAGE)
            return func

        return decorator

    @property
    def on_guild_full_message(self):
        """
        频道全量消息事件（私域机器人）

        事件类型: MESSAGE_CREATE
        Intent: GUILD_MESSAGES (1<<9)

        注意: 仅私域机器人可用
        """

        def decorator(func: Callable):
            if not self.is_private:
                self.logger.warning(
                    f"on_guild_full_message 仅私域机器人可用，当前为公域机器人，"
                    f"事件处理器 {func.__name__} 可能无法正常接收事件"
                )
            self._register_handler("MESSAGE_CREATE", func, Intent.GUILD_MESSAGES)
            return func

        return decorator

    @property
    def on_message_delete(self):
        """
        消息删除事件（私域机器人）

        事件类型: MESSAGE_DELETE
        Intent: GUILD_MESSAGES (1<<9)

        注意: 仅私域机器人可用
        """

        def decorator(func: Callable):
            if not self.is_private:
                self.logger.warning(
                    f"on_message_delete 仅私域机器人可用，当前为公域机器人，"
                    f"事件处理器 {func.__name__} 可能无法正常接收事件"
                )
            self._register_handler("MESSAGE_DELETE", func, Intent.GUILD_MESSAGES)
            return func

        return decorator

    @property
    def on_public_message_delete(self):
        """
        公域消息删除事件

        事件类型: PUBLIC_MESSAGE_DELETE
        Intent: PUBLIC_GUILD_MESSAGES (1<<30)
        """

        def decorator(func: Callable):
            self._register_handler(
                "PUBLIC_MESSAGE_DELETE", func, Intent.PUBLIC_GUILD_MESSAGES
            )
            return func

        return decorator

    @property
    def on_direct_message_delete(self):
        """
        私信消息删除事件

        事件类型: DIRECT_MESSAGE_DELETE
        Intent: DIRECT_MESSAGE (1<<12)
        """

        def decorator(func: Callable):
            self._register_handler("DIRECT_MESSAGE_DELETE", func, Intent.DIRECT_MESSAGE)
            return func

        return decorator

    @property
    def on_guild_create(self):
        """加入频道事件 (GUILD_CREATE)"""

        def decorator(func: Callable):
            self._register_handler("GUILD_CREATE", func, Intent.GUILDS)
            return func

        return decorator

    @property
    def on_guild_update(self):
        """频道更新事件 (GUILD_UPDATE)"""

        def decorator(func: Callable):
            self._register_handler("GUILD_UPDATE", func, Intent.GUILDS)
            return func

        return decorator

    @property
    def on_guild_delete(self):
        """退出频道事件 (GUILD_DELETE)"""

        def decorator(func: Callable):
            self._register_handler("GUILD_DELETE", func, Intent.GUILDS)
            return func

        return decorator

    @property
    def on_channel_create(self):
        """子频道创建事件 (CHANNEL_CREATE)"""

        def decorator(func: Callable):
            self._register_handler("CHANNEL_CREATE", func, Intent.GUILDS)
            return func

        return decorator

    @property
    def on_channel_update(self):
        """子频道更新事件 (CHANNEL_UPDATE)"""

        def decorator(func: Callable):
            self._register_handler("CHANNEL_UPDATE", func, Intent.GUILDS)
            return func

        return decorator

    @property
    def on_channel_delete(self):
        """子频道删除事件 (CHANNEL_DELETE)"""

        def decorator(func: Callable):
            self._register_handler("CHANNEL_DELETE", func, Intent.GUILDS)
            return func

        return decorator

    @property
    def on_guild_member_add(self):
        """成员加入频道事件 (GUILD_MEMBER_ADD)"""

        def decorator(func: Callable):
            self._register_handler("GUILD_MEMBER_ADD", func, Intent.GUILD_MEMBERS)
            return func

        return decorator

    @property
    def on_guild_member_update(self):
        """成员更新事件 (GUILD_MEMBER_UPDATE)"""

        def decorator(func: Callable):
            self._register_handler("GUILD_MEMBER_UPDATE", func, Intent.GUILD_MEMBERS)
            return func

        return decorator

    @property
    def on_guild_member_remove(self):
        """成员退出频道事件 (GUILD_MEMBER_REMOVE)"""

        def decorator(func: Callable):
            self._register_handler("GUILD_MEMBER_REMOVE", func, Intent.GUILD_MEMBERS)
            return func

        return decorator

    @property
    def on_group_add(self):
        """加入群聊事件 (GROUP_ADD_ROBOT)"""

        def decorator(func: Callable):
            self._register_handler("GROUP_ADD_ROBOT", func, Intent.GROUP_AND_C2C_EVENT)
            return func

        return decorator

    @property
    def on_group_delete(self):
        """退出群聊事件 (GROUP_DEL_ROBOT)"""

        def decorator(func: Callable):
            self._register_handler("GROUP_DEL_ROBOT", func, Intent.GROUP_AND_C2C_EVENT)
            return func

        return decorator

    @property
    def on_group_msg_reject(self):
        """群聊拒绝消息事件 (GROUP_MSG_REJECT)"""

        def decorator(func: Callable):
            self._register_handler("GROUP_MSG_REJECT", func, Intent.GROUP_AND_C2C_EVENT)
            return func

        return decorator

    @property
    def on_group_msg_receive(self):
        """群聊接受消息事件 (GROUP_MSG_RECEIVE)"""

        def decorator(func: Callable):
            self._register_handler(
                "GROUP_MSG_RECEIVE", func, Intent.GROUP_AND_C2C_EVENT
            )
            return func

        return decorator

    @property
    def on_friend_add(self):
        """添加好友事件 (FRIEND_ADD)"""

        def decorator(func: Callable):
            self._register_handler("FRIEND_ADD", func, Intent.GROUP_AND_C2C_EVENT)
            return func

        return decorator

    @property
    def on_friend_delete(self):
        """删除好友事件 (FRIEND_DEL)"""

        def decorator(func: Callable):
            self._register_handler("FRIEND_DEL", func, Intent.GROUP_AND_C2C_EVENT)
            return func

        return decorator

    @property
    def on_c2c_msg_reject(self):
        """拒绝消息事件 (C2C_MSG_REJECT)"""

        def decorator(func: Callable):
            self._register_handler("C2C_MSG_REJECT", func, Intent.GROUP_AND_C2C_EVENT)
            return func

        return decorator

    @property
    def on_c2c_msg_receive(self):
        """接受消息事件 (C2C_MSG_RECEIVE)"""

        def decorator(func: Callable):
            self._register_handler("C2C_MSG_RECEIVE", func, Intent.GROUP_AND_C2C_EVENT)
            return func

        return decorator

    @property
    def on_message_audit_pass(self):
        """消息审核通过事件 (MESSAGE_AUDIT_PASS)"""

        def decorator(func: Callable):
            self._register_handler("MESSAGE_AUDIT_PASS", func, Intent.MESSAGE_AUDIT)
            return func

        return decorator

    @property
    def on_message_audit_reject(self):
        """消息审核拒绝事件 (MESSAGE_AUDIT_REJECT)"""

        def decorator(func: Callable):
            self._register_handler("MESSAGE_AUDIT_REJECT", func, Intent.MESSAGE_AUDIT)
            return func

        return decorator

    @property
    def on_reaction_add(self):
        """表情表态添加事件 (MESSAGE_REACTION_ADD)"""

        def decorator(func: Callable):
            self._register_handler(
                "MESSAGE_REACTION_ADD", func, Intent.GUILD_MESSAGE_REACTIONS
            )
            return func

        return decorator

    @property
    def on_reaction_remove(self):
        """表情表态移除事件 (MESSAGE_REACTION_REMOVE)"""

        def decorator(func: Callable):
            self._register_handler(
                "MESSAGE_REACTION_REMOVE", func, Intent.GUILD_MESSAGE_REACTIONS
            )
            return func

        return decorator

    @property
    def on_interaction(self):
        """互动按钮回调事件 (INTERACTION_CREATE)"""

        def decorator(func: Callable):
            self._register_handler("INTERACTION_CREATE", func, Intent.INTERACTION)
            return func

        return decorator

    @property
    def on_forum_thread_create(self):
        """帖子创建事件 (FORUM_THREAD_CREATE) - 仅私域"""

        def decorator(func: Callable):
            if not self.is_private:
                self.logger.warning(
                    f"on_forum_thread_create 仅私域机器人可用，当前为公域机器人，"
                    f"事件处理器 {func.__name__} 可能无法正常接收事件"
                )
            self._register_handler("FORUM_THREAD_CREATE", func, Intent.FORUMS_EVENT)
            return func

        return decorator

    @property
    def on_forum_thread_update(self):
        """帖子更新事件 (FORUM_THREAD_UPDATE)"""

        def decorator(func: Callable):
            self._register_handler("FORUM_THREAD_UPDATE", func, Intent.FORUMS_EVENT)
            return func

        return decorator

    @property
    def on_forum_thread_delete(self):
        """帖子删除事件 (FORUM_THREAD_DELETE)"""

        def decorator(func: Callable):
            self._register_handler("FORUM_THREAD_DELETE", func, Intent.FORUMS_EVENT)
            return func

        return decorator

    @property
    def on_forum_post_create(self):
        """评论创建事件 (FORUM_POST_CREATE)"""

        def decorator(func: Callable):
            self._register_handler("FORUM_POST_CREATE", func, Intent.FORUMS_EVENT)
            return func

        return decorator

    @property
    def on_forum_post_delete(self):
        """评论删除事件 (FORUM_POST_DELETE)"""

        def decorator(func: Callable):
            self._register_handler("FORUM_POST_DELETE", func, Intent.FORUMS_EVENT)
            return func

        return decorator

    @property
    def on_forum_reply_create(self):
        """回复创建事件 (FORUM_REPLY_CREATE)"""

        def decorator(func: Callable):
            self._register_handler("FORUM_REPLY_CREATE", func, Intent.FORUMS_EVENT)
            return func

        return decorator

    @property
    def on_forum_reply_delete(self):
        """回复删除事件 (FORUM_REPLY_DELETE)"""

        def decorator(func: Callable):
            self._register_handler("FORUM_REPLY_DELETE", func, Intent.FORUMS_EVENT)
            return func

        return decorator

    @property
    def on_forum_publish_audit_result(self):
        """论坛帖子审核结果事件 (FORUM_PUBLISH_AUDIT_RESULT)"""

        def decorator(func: Callable):
            self._register_handler(
                "FORUM_PUBLISH_AUDIT_RESULT", func, Intent.FORUMS_EVENT
            )
            return func

        return decorator

    @property
    def on_open_forum_thread_create(self):
        """开放论坛主题创建事件 (OPEN_FORUM_THREAD_CREATE) - 公域机器人可用"""

        def decorator(func: Callable):
            self._register_handler(
                "OPEN_FORUM_THREAD_CREATE", func, Intent.OPEN_FORUM_EVENT
            )
            return func

        return decorator

    @property
    def on_open_forum_thread_update(self):
        """开放论坛主题更新事件 (OPEN_FORUM_THREAD_UPDATE) - 公域机器人可用"""

        def decorator(func: Callable):
            self._register_handler(
                "OPEN_FORUM_THREAD_UPDATE", func, Intent.OPEN_FORUM_EVENT
            )
            return func

        return decorator

    @property
    def on_open_forum_thread_delete(self):
        """开放论坛主题删除事件 (OPEN_FORUM_THREAD_DELETE) - 公域机器人可用"""

        def decorator(func: Callable):
            self._register_handler(
                "OPEN_FORUM_THREAD_DELETE", func, Intent.OPEN_FORUM_EVENT
            )
            return func

        return decorator

    @property
    def on_open_forum_post_create(self):
        """开放论坛帖子创建事件 (OPEN_FORUM_POST_CREATE) - 公域机器人可用"""

        def decorator(func: Callable):
            self._register_handler(
                "OPEN_FORUM_POST_CREATE", func, Intent.OPEN_FORUM_EVENT
            )
            return func

        return decorator

    @property
    def on_open_forum_post_delete(self):
        """开放论坛帖子删除事件 (OPEN_FORUM_POST_DELETE) - 公域机器人可用"""

        def decorator(func: Callable):
            self._register_handler(
                "OPEN_FORUM_POST_DELETE", func, Intent.OPEN_FORUM_EVENT
            )
            return func

        return decorator

    @property
    def on_open_forum_reply_create(self):
        """开放论坛回复创建事件 (OPEN_FORUM_REPLY_CREATE) - 公域机器人可用"""

        def decorator(func: Callable):
            self._register_handler(
                "OPEN_FORUM_REPLY_CREATE", func, Intent.OPEN_FORUM_EVENT
            )
            return func

        return decorator

    @property
    def on_open_forum_reply_delete(self):
        """开放论坛回复删除事件 (OPEN_FORUM_REPLY_DELETE) - 公域机器人可用"""

        def decorator(func: Callable):
            self._register_handler(
                "OPEN_FORUM_REPLY_DELETE", func, Intent.OPEN_FORUM_EVENT
            )
            return func

        return decorator

    @property
    def on_audio_or_live_channel_member_enter(self):
        """进入音视频/直播子频道事件"""

        def decorator(func: Callable):
            self._register_handler(
                "AUDIO_OR_LIVE_CHANNEL_MEMBER_ENTER", func, Intent.AUDIO_ACTION
            )
            return func

        return decorator

    @property
    def on_audio_or_live_channel_member_exit(self):
        """离开音视频/直播子频道事件"""

        def decorator(func: Callable):
            self._register_handler(
                "AUDIO_OR_LIVE_CHANNEL_MEMBER_EXIT", func, Intent.AUDIO_ACTION
            )
            return func

        return decorator

    @property
    def on_audio_start(self):
        """
        音频开始播放事件

        事件类型: AUDIO_START
        Intent: AUDIO_ACTION (1<<29)
        """

        def decorator(func: Callable):
            self._register_handler("AUDIO_START", func, Intent.AUDIO_ACTION)
            return func

        return decorator

    @property
    def on_audio_finish(self):
        """
        音频播放结束事件

        事件类型: AUDIO_FINISH
        Intent: AUDIO_ACTION (1<<29)
        """

        def decorator(func: Callable):
            self._register_handler("AUDIO_FINISH", func, Intent.AUDIO_ACTION)
            return func

        return decorator

    @property
    def on_audio_on_mic(self):
        """
        上麦事件

        事件类型: AUDIO_ON_MIC
        Intent: AUDIO_ACTION (1<<29)
        """

        def decorator(func: Callable):
            self._register_handler("AUDIO_ON_MIC", func, Intent.AUDIO_ACTION)
            return func

        return decorator

    @property
    def on_audio_off_mic(self):
        """
        下麦事件

        事件类型: AUDIO_OFF_MIC
        Intent: AUDIO_ACTION (1<<29)
        """

        def decorator(func: Callable):
            self._register_handler("AUDIO_OFF_MIC", func, Intent.AUDIO_ACTION)
            return func

        return decorator

    @property
    def on_all_intent_events(self):
        """
        订阅所有机器人事件

        包含以下 Intent 的所有事件：
        - GUILDS (频道相关)
        - GUILD_MEMBERS (成员相关)
        - GUILD_MESSAGES (消息相关，私域)
        - GUILD_MESSAGE_REACTIONS (表情表态)
        - DIRECT_MESSAGE (私信)
        - MESSAGE_AUDIT (消息审核)
        - FORUMS_EVENT (论坛事件，私域)
        - AUDIO_ACTION (音频操作)
        - PUBLIC_GUILD_MESSAGES (公域消息)
        - INTERACTION (互动按钮)
        - GROUP_AND_C2C_EVENT (群聊和单聊)
        - OPEN_FORUM_EVENT (开放论坛)

        注意: 部分事件需要私域机器人权限才能接收

        示例:
            @bot.on_all_intent_events
            async def handle_all_intent_events(event):
                print(f"收到事件: {event}")
        """

        def decorator(func: Callable):
            event_types = get_event_types_by_intent(Intent.ALL_INTENT_EVENT)
            for event_type in event_types:
                self._register_handler(event_type, func, EVENT_INTENT_MAP[event_type])
            return func

        return decorator

    @property
    def on_default_public_events(self):
        """
        订阅公域机器人默认事件

        包含以下 Intent 的事件：
        - GUILDS (频道相关)
        - PUBLIC_GUILD_MESSAGES (公域消息，@机器人)
        - GROUP_AND_C2C_EVENT (群聊和单聊)
        - OPEN_FORUM_EVENT (开放论坛)

        适用于大多数公域机器人场景。

        示例:
            @bot.on_default_public_events
            async def handle_default_events(event):
                print(f"收到事件: {event}")
        """

        def decorator(func: Callable):
            event_types = get_event_types_by_intent(Intent.DEFAULT_PUBLIC)
            for event_type in event_types:
                self._register_handler(event_type, func, EVENT_INTENT_MAP[event_type])
            return func

        return decorator

    @property
    def on_default_private_events(self):
        """
        订阅私域机器人默认事件

        包含以下 Intent 的事件：
        - GUILDS (频道相关)
        - GUILD_MEMBERS (成员相关)
        - GUILD_MESSAGES (全量消息)
        - GUILD_MESSAGE_REACTIONS (表情表态)
        - DIRECT_MESSAGE (私信)
        - MESSAGE_AUDIT (消息审核)
        - INTERACTION (互动按钮)
        - GROUP_AND_C2C_EVENT (群聊和单聊)

        适用于私域机器人场景。

        注意: 仅私域机器人可用

        示例:
            @bot.on_default_private_events
            async def handle_private_events(event):
                print(f"收到事件: {event}")
        """

        def decorator(func: Callable):
            if not self.is_private:
                self.logger.warning(
                    f"on_default_private_events 仅私域机器人可用，当前为公域机器人，"
                    f"事件处理器 {func.__name__} 可能无法正常接收部分事件"
                )
            event_types = get_event_types_by_intent(Intent.DEFAULT_PRIVATE)
            for event_type in event_types:
                self._register_handler(event_type, func, EVENT_INTENT_MAP[event_type])
            return func

        return decorator

    def on_startup(self, func: Callable) -> Callable:
        """
        注册机器人启动事件处理器

        当机器人成功连接并准备好后触发。

        Args:
            func: 异步处理函数，接收 StartupEvent 参数

        Returns:
            原函数

        示例:
            @bot.on_startup
            async def handle_startup(event):
                print(f"机器人启动成功，时间: {event.timestamp}")
        """
        self._lifecycle.register_startup(func)
        return func

    def on_shutdown(self, func: Callable) -> Callable:
        """
        注册机器人关闭事件处理器

        当机器人即将关闭时触发。

        Args:
            func: 异步处理函数，接收 ShutdownEvent 参数

        Returns:
            原函数

        示例:
            @bot.on_shutdown
            async def handle_shutdown(event):
                print(f"机器人正在关闭，时间: {event.timestamp}")
        """
        self._lifecycle.register_shutdown(func)
        return func

    def load_plugins(self) -> None:
        """
        加载插件目录中的插件

        扫描插件目录，加载所有 Python 模块，并调用每个模块中的 register() 函数
        """
        if not self.auto_load_plugins:
            return

        plugins_path = Path(self.plugins_dir)
        if not plugins_path.exists():
            self.logger.warning(f"插件目录不存在: {plugins_path.absolute()}")
            return

        if not plugins_path.is_dir():
            self.logger.warning(f"插件路径不是目录: {plugins_path.absolute()}")
            return

        self.logger.info(f"开始加载插件目录: {plugins_path.absolute()}")

        plugins_dir_str = str(plugins_path.absolute())
        if plugins_dir_str not in sys.path:
            sys.path.insert(0, plugins_dir_str)

        pattern = "**/*.py" if self.plugins_recursive else "*.py"
        plugin_files = list(plugins_path.glob(pattern))

        loaded_count = 0
        for plugin_file in plugin_files:
            if plugin_file.name.startswith("_") or plugin_file.name == "__init__.py":
                continue

            try:
                module_name = plugin_file.stem
                spec = importlib.util.spec_from_file_location(module_name, plugin_file)
                if spec and spec.loader:
                    commands_before = len(Plugins._commands)
                    preprocessors_before = sum(
                        len(v) for v in Plugins._preprocessors.values()
                    )

                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    commands_after = len(Plugins._commands)
                    preprocessors_after = sum(
                        len(v) for v in Plugins._preprocessors.values()
                    )

                    has_new_commands = commands_after > commands_before
                    has_new_preprocessors = preprocessors_after > preprocessors_before

                    if hasattr(module, "register"):
                        register_func = getattr(module, "register")
                        if callable(register_func):
                            register_func(self)
                            loaded_count += 1
                            self.logger.info(
                                f"成功加载插件 (register): {plugin_file.name}"
                            )
                        else:
                            self.logger.warning(
                                f"插件 {plugin_file.name} 的 register 不是可调用对象"
                            )
                    elif has_new_commands or has_new_preprocessors:
                        loaded_count += 1
                        self.logger.info(f"成功加载插件 (装饰器): {plugin_file.name}")
                    else:
                        self.logger.debug(
                            f"插件 {plugin_file.name} 没有 register 函数且未使用装饰器，跳过"
                        )
            except Exception as e:
                self.logger.error(f"加载插件 {plugin_file.name} 时出错: {e}")

        if loaded_count > 0:
            self._log_registered_plugins()
            self._register_plugin_intents()
        else:
            self.logger.info("没有找到可加载的插件")

    def _log_registered_plugins(self) -> None:
        enabled_commands = [cmd for cmd in Plugins._commands if cmd.enabled]
        for cmd in enabled_commands:
            if cmd.command:
                cmd_names = ", ".join(cmd.command)
                self.logger.info(
                    f"从Plugins注册指令：[{cmd_names}] -> {cmd.func.__name__}"
                )
            elif cmd.regex:
                regex_patterns = [r.pattern for r in cmd.regex]
                self.logger.info(
                    f"从Plugins注册正则指令：[{', '.join(regex_patterns)}] -> {cmd.func.__name__}"
                )
            else:
                self.logger.info(f"从Plugins注册指令：{cmd.func.__name__}")

        preprocessor_count = sum(len(v) for v in Plugins._preprocessors.values())
        for intents, v in Plugins._preprocessors.items():
            scope = CommandValidScenes.get_name(intents)
            for func in v:
                self.logger.info(f"从Plugins注册 {scope} 预处理器：{func.__name__}")

        command_count = len(enabled_commands)
        if command_count or preprocessor_count > 0:
            self.logger.info(
                f"插件注册完成：{command_count} 个指令，{preprocessor_count} 个预处理器"
            )

    def _register_plugin_intents(self) -> None:
        for cmd in Plugins._commands:
            self._update_intents_for_scenes(cmd.valid_scenes, source="Plugins")

    async def _trigger_startup(self) -> None:
        """
        触发启动事件（内部方法）

        由协议客户端在成功连接后调用。
        """
        self.load_plugins()
        await self._initialize_bot_info()
        await self._lifecycle.trigger_startup()
        self._lifecycle.start_timer()

    async def _initialize_bot_info(self) -> None:
        """初始化机器人信息"""
        try:
            bot_info = await self.api.get_me()
            if bot_info and bot_info.id:
                self._bot_id = bot_info.id
                self._bot_name = bot_info.username
                self.logger.info(
                    f"机器人ID: {self._bot_id}，机器人名称: {self._bot_name}"
                )
        except Exception as e:
            self.logger.warning(f"获取机器人信息失败: {e}")

    def on_timer(self, interval: float):
        """
        注册周期定时器事件处理器

        按指定间隔周期性触发。

        Args:
            interval: 定时间隔（秒）

        Returns:
            装饰器函数

        示例:
            @bot.on_timer(interval=60)
            async def handle_timer(event):
                print(f"定时器触发，第 {event.tick_count} 次")
        """

        def decorator(func: Callable) -> Callable:
            self._lifecycle.register_timer(func, interval)
            return func

        return decorator

    @property
    def bot_admin_manager(self) -> BotAdminManager:
        """获取机器人管理员管理器"""
        return self._bot_admin_manager

    @property
    def bot_id(self) -> str | None:
        """获取机器人ID"""
        return self._bot_id

    @property
    def session(self) -> SessionManager:
        """获取会话管理器"""
        return self._session_manager

    def before_command(
        self,
        valid_scenes: CommandValidScenes = CommandValidScenes.ALL,
    ):
        """
        注册预处理器，将在检查所有commands前执行

        :param valid_scenes: 此处理器的有效场景，可传入多个场景，默认 CommandValidScenes.ALL
        """

        def wrap(func: Callable):
            Plugins.before_command(valid_scenes)(func)
            return func

        return wrap

    def on_command(
        self,
        command: list[str] | str | None = None,
        regex: None = None,
        is_treat: bool = True,
        is_require_at: bool = False,
        is_short_circuit: bool = True,
        is_custom_short_circuit: bool = False,
        is_require_admin: bool = False,
        admin_error_msg: str | None = None,
        valid_scenes: CommandValidScenes = CommandValidScenes.ALL,
        enabled: bool = True,
        is_require_bot_admin: bool = False,
        bot_admin_error_msg: str | None = None,
    ):
        """
        指令装饰器。用于快速注册消息事件

        :param command: 可触发事件的指令列表，与正则regex互斥，优先使用此项
        :param regex: 可触发指令的正则compile实例或正则表达式，与指令表互斥
        :param is_treat: 是否在treated_msg中同时处理指令，如正则将返回.groups()，默认是
        :param is_require_at: 是否要求必须艾特机器人才能触发指令，默认否
        :param is_short_circuit: 如果触发指令成功是否短路不运行后续指令（将根据注册顺序排序指令的短路机制），默认是
        :param is_custom_short_circuit: 如果触发指令成功而回调函数返回True则不运行后续指令，存在时优先于is_short_circuit，默认否
        :param is_require_admin: 是否要求频道主或或管理才可触发指令，默认否 (在群聊和单聊中不生效，可使用全局机器人管理员控制)
        :param admin_error_msg: 当is_require_admin为True，而触发用户的权限不足时，如此项不为None，返回此消息并短路；否则不进行短路
        :param valid_scenes: 此机器人命令的有效场景，可传入多个场景，默认 CommandValidScenes.ALL
        :param enabled: 是否启用此指令，默认True
        :param is_require_bot_admin: 是否要求机器人管理员才可触发指令，默认否
        :param bot_admin_error_msg: 当is_require_bot_admin为True，而触发用户的权限不足时，如此项不为None，返回此消息并短路；否则不进行短路
        """

        def wrap(func: Callable):
            Plugins.on_command(
                command,
                regex,
                is_treat,
                is_require_at,
                is_short_circuit,
                is_custom_short_circuit,
                is_require_admin,
                admin_error_msg,
                valid_scenes,
                enabled,
                is_require_bot_admin,
                bot_admin_error_msg,
            )(func)
            self._update_intents_for_scenes(valid_scenes)
            return func

        return wrap

    def _update_intents_for_scenes(
        self, valid_scenes: CommandValidScenes, source: str = "on_command"
    ) -> None:
        """
        根据命令的有效场景更新 Intent 值

        必须在 WebSocket Identify 之前调用，确保 intents 值正确。

        Args:
            valid_scenes: 命令的有效场景位掩码
            source: 调用来源标识，用于日志记录
        """
        if valid_scenes & CommandValidScenes.GUILD:
            if not (self._intents & Intent.GUILD_MESSAGES) and not (
                self._intents & Intent.PUBLIC_GUILD_MESSAGES
            ):
                if self.is_private:
                    self._intents = self._intents | Intent.GUILD_MESSAGES
                    self.logger.debug(
                        f"[{source}] 注册私域频道消息 Intent (GUILD_MESSAGES)"
                    )
                else:
                    self._intents = self._intents | Intent.PUBLIC_GUILD_MESSAGES
                    self.logger.debug(
                        f"[{source}] 注册公域频道消息 Intent (PUBLIC_GUILD_MESSAGES)"
                    )
        if valid_scenes & CommandValidScenes.DM:
            if not (self._intents & Intent.DIRECT_MESSAGE):
                self._intents = self._intents | Intent.DIRECT_MESSAGE
                self.logger.debug(f"[{source}] 注册私信 Intent (DIRECT_MESSAGE)")
        if (valid_scenes & CommandValidScenes.GROUP) or (
            valid_scenes & CommandValidScenes.C2C
        ):
            if not (self._intents & Intent.GROUP_AND_C2C_EVENT):
                self._intents = self._intents | Intent.GROUP_AND_C2C_EVENT
                self.logger.debug(
                    f"[{source}] 注册群聊/单聊 Intent (GROUP_AND_C2C_EVENT)"
                )
