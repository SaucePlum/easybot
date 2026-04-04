#!/usr/bin/env python3
"""
EasyBot SDK 日志模块

提供按机器人分目录、按天轮转的日志系统，支持控制台彩色输出。
统一日志格式: [(asctime)] [levelname] [module] message

优化特性：
- 共享handler机制，避免重复创建文件和控制台处理器
- 使用extra参数传递module_name，而非创建新Logger实例
"""

import logging
import os
import sys
import threading
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import ClassVar

DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL


class ColorCodes:
    """ANSI 颜色码定义"""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    LEVEL_DEBUG = "\033[1;36m"
    LEVEL_INFO = "\033[1;32m"
    LEVEL_WARNING = "\033[1;33m"
    LEVEL_ERROR = "\033[1;31m"
    LEVEL_CRITICAL = "\033[1;41m"


LEVEL_COLORS = {
    logging.DEBUG: ColorCodes.LEVEL_DEBUG,
    logging.INFO: ColorCodes.LEVEL_INFO,
    logging.WARNING: ColorCodes.LEVEL_WARNING,
    logging.ERROR: ColorCodes.LEVEL_ERROR,
    logging.CRITICAL: ColorCodes.LEVEL_CRITICAL,
}


class ColoredFormatter(logging.Formatter):
    """
    支持彩色输出的日志格式器

    根据日志级别自动着色，仅在支持 ANSI 颜色的终端生效。
    Windows 环境下自动检测终端支持情况。
    """

    def __init__(
        self,
        fmt: str | None = None,
        datefmt: str | None = None,
        use_color: bool = True,
    ):
        super().__init__(fmt, datefmt)
        self.use_color = use_color and self._supports_color()

    @staticmethod
    def _supports_color() -> bool:
        """
        检测终端是否支持 ANSI 颜色

        Returns:
            True 如果终端支持颜色输出
        """
        if sys.platform == "win32":
            return (
                os.environ.get("ANSICON") is not None
                or "WT_SESSION" in os.environ
                or os.environ.get("TERM_PROGRAM") == "vscode"
                or os.environ.get("TERM") == "xterm-256color"
            )
        return hasattr(sys.stderr, "isatty") and sys.stderr.isatty()

    def format(self, record: logging.LogRecord) -> str:
        """
        格式化日志记录

        Args:
            record: 日志记录对象

        Returns:
            格式化后的日志字符串
        """
        module_name = getattr(record, "module_name", record.module)

        if self.use_color:
            level_color = LEVEL_COLORS.get(record.levelno, ColorCodes.RESET)
            timestamp = f"{level_color}[{self.formatTime(record, self.datefmt)}]{ColorCodes.RESET}"
            levelname = f"{level_color}[{record.levelname}]{ColorCodes.RESET}"
            module = f"[{module_name}]"
            message = f"{record.getMessage()}"

            return f"{timestamp} {levelname} {module} {message}"
        else:
            return f"[{self.formatTime(record, self.datefmt)}] [{record.levelname}] [{module_name}] {record.getMessage()}"


class LoggerManager:
    """
    日志管理器

    管理共享的handler和logger实例，避免重复创建资源。
    使用类变量实现单例模式。
    """

    _instances: ClassVar[dict[str, "LoggerManager"]] = {}
    _file_handlers: ClassVar[dict[str, TimedRotatingFileHandler]] = {}
    _console_handler: ClassVar[logging.StreamHandler | None] = None
    _lock: ClassVar[threading.Lock] = threading.Lock()

    def __new__(cls, bot_id: str, log_dir: str | None = None) -> "LoggerManager":
        key = f"{bot_id}:{log_dir or 'default'}"
        if key not in cls._instances:
            instance = super().__new__(cls)
            instance._bot_id = bot_id
            instance._log_dir = log_dir
            instance._loggers: dict[str, logging.Logger] = {}
            cls._instances[key] = instance
        return cls._instances[key]

    def get_logger(self, module_name: str, level: int = logging.INFO) -> logging.Logger:
        """
        获取或创建指定模块的logger

        Args:
            module_name: 模块名称
            level: 日志级别

        Returns:
            配置好的Logger实例
        """
        logger_name = f"easybot.{self._bot_id}.{module_name}"

        if logger_name in self._loggers:
            return self._loggers[logger_name]

        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        logger.handlers.clear()
        logger.propagate = False

        file_handler = self._get_file_handler(level)
        logger.addHandler(file_handler)

        console_handler = self._get_console_handler(level)
        logger.addHandler(console_handler)

        self._loggers[logger_name] = logger
        return logger

    def _get_file_handler(self, level: int) -> TimedRotatingFileHandler:
        """获取或创建文件handler"""
        base_dir = Path(self._log_dir) if self._log_dir else Path("logs")
        bot_log_dir = base_dir / self._bot_id
        bot_log_dir.mkdir(parents=True, exist_ok=True)

        log_filename = bot_log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"
        handler_key = str(log_filename)

        if handler_key not in LoggerManager._file_handlers:
            handler = TimedRotatingFileHandler(
                str(log_filename),
                when="midnight",
                interval=1,
                encoding="utf-8",
            )
            handler.suffix = "%Y-%m-%d.log"
            handler.setLevel(level)
            formatter = logging.Formatter(
                "[%(asctime)s] [%(levelname)s] [%(module_name)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            handler.setFormatter(formatter)
            LoggerManager._file_handlers[handler_key] = handler

        return LoggerManager._file_handlers[handler_key]

    def _get_console_handler(self, level: int) -> logging.StreamHandler:
        """获取或创建控制台handler（全局共享）"""
        if LoggerManager._console_handler is None:
            handler = logging.StreamHandler()
            handler.setLevel(level)
            formatter = ColoredFormatter(
                fmt="[%(asctime)s] [%(levelname)s] [%(module_name)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
                use_color=True,
            )
            handler.setFormatter(formatter)
            LoggerManager._console_handler = handler

        return LoggerManager._console_handler

    def close(self) -> None:
        """关闭所有handler"""
        for logger in self._loggers.values():
            for handler in logger.handlers[:]:
                try:
                    handler.close()
                except Exception:
                    pass
                logger.removeHandler(handler)
        self._loggers.clear()

    @classmethod
    def cleanup_all(cls) -> None:
        """清理所有实例和handler"""
        for instance in cls._instances.values():
            instance.close()
        cls._instances.clear()

        for handler in cls._file_handlers.values():
            try:
                handler.close()
            except Exception:
                pass
        cls._file_handlers.clear()

        if cls._console_handler:
            try:
                cls._console_handler.close()
            except Exception:
                pass
            cls._console_handler = None


class Logger:
    """
    内置日志系统

    格式: [(asctime)] [levelname] [module] message
    路径: logs/{bot_id}/YYYY-MM-DD.log
    轮转: 按天轮转

    控制台输出支持按日志级别着色:
        - DEBUG: 青色
        - INFO: 绿色
        - WARNING: 黄色
        - ERROR: 红色
        - CRITICAL: 红色背景

    示例:
        logger = Logger(bot_id="123456789")
        logger.info("机器人启动成功")
        logger.error("API 调用失败", exc_info=True)
    """

    DEFAULT_FORMAT = "[%(asctime)s] [%(levelname)s] [%(module_name)s] %(message)s"
    DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(
        self,
        bot_id: str,
        log_dir: str | None = None,
        level: int | None = None,
        is_debug: bool = False,
        console_output: bool = True,
        use_color: bool = True,
        module_name: str = "core",
    ):
        """
        初始化日志系统

        Args:
            bot_id: 机器人 AppID，用于区分不同机器人的日志
            log_dir: 日志根目录，默认为当前目录下的 logs 文件夹
            level: 日志级别，若指定则忽略 is_debug
            is_debug: 是否为调试模式，True 时输出 DEBUG 级别日志，False 时输出 INFO 级别
            console_output: 是否输出到控制台，默认为 True
            use_color: 控制台是否使用彩色输出，默认为 True
            module_name: 模块名称标识，用于区分不同模块的日志
        """
        self.bot_id = bot_id
        self.module_name = module_name
        self.log_dir = log_dir
        self.use_color = use_color

        if level is None:
            level = DEBUG if is_debug else INFO

        self._manager = LoggerManager(bot_id, log_dir)
        self.logger = self._manager.get_logger(module_name, level)

    def _log(self, level: int, msg: str, *args, **kwargs):
        """内部日志方法，自动添加模块名"""
        extra = kwargs.pop("extra", {})
        extra["module_name"] = self.module_name
        self.logger.log(level, msg, *args, extra=extra, **kwargs)

    def debug(self, msg: str, *args, **kwargs):
        """调试日志"""
        self._log(logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs):
        """信息日志"""
        self._log(logging.INFO, msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        """警告日志"""
        self._log(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        """错误日志"""
        self._log(logging.ERROR, msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs):
        """严重错误日志"""
        self._log(logging.CRITICAL, msg, *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs):
        """异常日志（自动包含堆栈信息）"""
        extra = kwargs.pop("extra", {})
        extra["module_name"] = self.module_name
        self.logger.exception(msg, *args, extra=extra, **kwargs)

    def with_module(self, module_name: str) -> "Logger":
        """
        创建带有不同模块名的日志器

        复用现有的handler，避免重复创建资源。

        Args:
            module_name: 模块名称

        Returns:
            新的 Logger 实例（共享handler）
        """
        return Logger(
            bot_id=self.bot_id,
            log_dir=self.log_dir,
            level=self.logger.level,
            console_output=True,
            use_color=self.use_color,
            module_name=module_name,
        )

    def close(self) -> None:
        """
        关闭日志系统并释放所有资源

        包括：
        - 关闭所有文件处理器
        - 关闭所有控制台处理器
        - 移除所有处理器
        """
        self._manager.close()
