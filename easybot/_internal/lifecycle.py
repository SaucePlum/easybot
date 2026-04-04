#!/usr/bin/env python3
"""
EasyBot SDK 生命周期事件管理模块

提供机器人生命周期事件管理，包括：
- 启动事件 (STARTUP)
- 关闭事件 (SHUTDOWN)
- 周期定时器事件 (TIMER)
"""

import asyncio
import inspect
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from ..bot import Bot


INTERNAL_EVENT_STARTUP = "INTERNAL_STARTUP"
INTERNAL_EVENT_SHUTDOWN = "INTERNAL_SHUTDOWN"
INTERNAL_EVENT_TIMER = "INTERNAL_TIMER"


@dataclass
class TimerEvent:
    """
    定时器事件数据

    Attributes:
        bot: Bot 实例
        timestamp: 事件触发时间戳
        tick_count: 第几次触发（从1开始）
    """

    bot: "Bot"
    timestamp: float
    tick_count: int


@dataclass
class StartupEvent:
    """
    启动事件数据

    Attributes:
        bot: Bot 实例
        timestamp: 事件触发时间戳
    """

    bot: "Bot"
    timestamp: float


@dataclass
class ShutdownEvent:
    """
    关闭事件数据

    Attributes:
        bot: Bot 实例
        timestamp: 事件触发时间戳
    """

    bot: "Bot"
    timestamp: float


class LifecycleManager:
    """
    生命周期事件管理器

    管理机器人的生命周期事件，包括启动、关闭和定时器事件。
    """

    def __init__(self, bot: "Bot", logger: Any):
        """
        初始化生命周期管理器

        Args:
            bot: Bot 实例
            logger: 日志记录器
        """
        self._bot = bot
        self._logger = logger

        self._startup_handlers: list[Callable] = []
        self._shutdown_handlers: list[Callable] = []
        self._timer_handlers: list[Callable] = []

        self._timer_task: asyncio.Task | None = None
        self._timer_interval: float = 0
        self._timer_tick_count: int = 0
        self._stop_event: asyncio.Event = asyncio.Event()

    @staticmethod
    def _handler_accepts_arg(handler: Callable) -> bool:
        """
        检查处理器是否接受参数

        Args:
            handler: 处理器函数

        Returns:
            是否接受参数
        """
        sig = inspect.signature(handler)
        params = [
            p
            for p in sig.parameters.values()
            if p.kind
            in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
        ]
        return len(params) > 0

    async def _call_handler(self, handler: Callable, event: Any) -> None:
        """
        调用处理器，根据签名决定是否传递事件参数

        Args:
            handler: 处理器函数
            event: 事件数据
        """
        if self._handler_accepts_arg(handler):
            await handler(event)
        else:
            await handler()

    def register_startup(self, handler: Callable) -> None:
        """
        注册启动事件处理器

        Args:
            handler: 异步处理函数
        """
        self._startup_handlers.append(handler)
        self._logger.debug(f"注册启动事件处理器: {handler.__name__}")

    def register_shutdown(self, handler: Callable) -> None:
        """
        注册关闭事件处理器

        Args:
            handler: 异步处理函数
        """
        self._shutdown_handlers.append(handler)
        self._logger.debug(f"注册关闭事件处理器: {handler.__name__}")

    def register_timer(self, handler: Callable, interval: float) -> None:
        """
        注册定时器事件处理器

        Args:
            handler: 异步处理函数
            interval: 定时间隔（秒）
        """
        self._timer_handlers.append(handler)
        self._timer_interval = interval
        self._logger.debug(
            f"注册定时器事件处理器: {handler.__name__}, 间隔: {interval}秒"
        )

    async def trigger_startup(self) -> None:
        """
        触发启动事件

        在机器人成功连接并准备好后调用。
        """
        if not self._startup_handlers:
            return

        event = StartupEvent(bot=self._bot, timestamp=time.time())

        for handler in self._startup_handlers:
            try:
                await self._call_handler(handler, event)
            except Exception as e:
                self._logger.exception(
                    f"启动事件处理器执行错误 [{handler.__name__}]: {e}"
                )

    async def trigger_shutdown(self) -> None:
        """
        触发关闭事件

        在机器人即将关闭时调用。
        """
        self._stop_event.set()

        if self._timer_task:
            self._timer_task.cancel()
            try:
                await self._timer_task
            except asyncio.CancelledError:
                pass
            self._timer_task = None

        if not self._shutdown_handlers:
            return

        event = ShutdownEvent(bot=self._bot, timestamp=time.time())

        for handler in self._shutdown_handlers:
            try:
                await self._call_handler(handler, event)
            except Exception as e:
                self._logger.exception(
                    f"关闭事件处理器执行错误 [{handler.__name__}]: {e}"
                )

    def start_timer(self) -> None:
        """
        启动定时器

        如果已注册定时器处理器，则启动定时器任务。
        """
        if not self._timer_handlers or self._timer_interval <= 0:
            return

        if self._timer_task is not None and not self._timer_task.done():
            return

        self._stop_event.clear()
        self._timer_tick_count = 0
        self._timer_task = asyncio.create_task(self._timer_loop())
        self._logger.debug(f"定时器已启动，间隔: {self._timer_interval}秒")

    async def _timer_loop(self) -> None:
        """定时器循环"""
        while not self._stop_event.is_set():
            try:
                await asyncio.sleep(self._timer_interval)

                if self._stop_event.is_set():
                    break

                self._timer_tick_count += 1
                event = TimerEvent(
                    bot=self._bot,
                    timestamp=time.time(),
                    tick_count=self._timer_tick_count,
                )

                for handler in self._timer_handlers:
                    try:
                        await self._call_handler(handler, event)
                    except Exception as e:
                        self._logger.exception(
                            f"定时器事件处理器执行错误 [{handler.__name__}]: {e}"
                        )

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.exception(f"定时器循环错误: {e}")

    async def close(self) -> None:
        """
        关闭生命周期管理器

        停止定时器并清理资源。
        """
        await self.trigger_shutdown()
