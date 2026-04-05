#!/usr/bin/env python3
"""
EasyBot SDK - 轻量级 QQ 机器人 SDK

专注于简洁、容易上手且稳定的 QQ 官方机器人 SDK，面向初级开发者。
"""

from ._internal.lifecycle import ShutdownEvent, StartupEvent, TimerEvent
from .api import API
from .bot import Bot
from .builders import Builders, MessagesModel
from .exceptions import (
    APIError,
    AuthenticationError,
    EasyBotException,
    NetworkError,
    PermissionError,
    RateLimitError,
    StopProcessing,
    ValidationError,
)
from .logger import Logger
from .models import Model
from .plugins import BotAdminManager, BotCommandObject, CommandValidScenes, Plugins
from .protocol import Proto
from .sandbox import SandBox
from .session import Scope, SessionManager, WaitError, WaitTimeoutError, with_session
from .version import __version__

__all__ = [
    "Bot",
    "API",
    "Model",
    "MessagesModel",
    "Builders",
    "Proto",
    "SandBox",
    "Logger",
    "EasyBotException",
    "APIError",
    "AuthenticationError",
    "PermissionError",
    "RateLimitError",
    "NetworkError",
    "ValidationError",
    "StartupEvent",
    "ShutdownEvent",
    "TimerEvent",
    "CommandValidScenes",
    "BotAdminManager",
    "BotCommandObject",
    "Plugins",
    "SessionManager",
    "Scope",
    "WaitTimeoutError",
    "WaitError",
    "with_session",
    "StopProcessing",
    "__version__",
]
