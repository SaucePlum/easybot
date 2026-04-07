#!/usr/bin/env python3
"""
EasyBot SDK 插件系统模块

提供预处理器、命令插件系统和权限管理功能。
"""

import asyncio
import importlib
import inspect
import os
import re
import sys
from collections import defaultdict
from collections.abc import Callable, Iterable
from pathlib import Path
from re import Pattern
from typing import Any, Set, Union

import yaml


class CommandValidScenes(int):
    """
    机器人命令的有效场景，用于限制机器人命令的有效场景，可传入多个场景，如 CommandValidScenes.GUILD | CommandValidScenes.DM

    - GUILD - 代表只在频道有效
    - DM - 代表只在频道私信有效
    - GROUP - 代表只在qq群聊场景有效
    - C2C - 代表只在qq私聊场景有效
    """

    GUILD = 1
    DM = 2
    GROUP = 4
    C2C = 8
    ALL = GUILD | DM | GROUP | C2C

    _name_cache = {1: "GUILD", 2: "DM", 4: "GROUP", 8: "C2C", 15: "ALL"}

    @classmethod
    def get_name(cls, value: int) -> str:
        return cls._name_cache.get(value, "")


class BotAdminManager:
    """
    机器人管理员管理器（单例），用于管理全局机器人管理员（超管）

    管理员数据自动持久化到 YAML 文件（默认 sdk_data/bot_admins.yaml），
    启动时自动加载，增删操作后自动保存。

    使用单例模式确保所有实例共享同一份数据。

    注意：所有修改操作都是异步方法，需要在异步上下文中调用。

    使用示例:
        admin_manager = BotAdminManager()
        await admin_manager.initialize()

        # 批量设置管理员列表（合并式，会持久化）
        await admin_manager.set_bot_admins(["user_id_1", "user_id_2"])

        # 增量添加/移除
        await admin_manager.add_admin("user_id_3")
        await admin_manager.remove_admin("user_id_1")

        if admin_manager.is_admin("user_id_1"):
            print("是机器人管理员")
    """

    _DEFAULT_DATA_DIR = "sdk_data"
    _DEFAULT_FILE_NAME = "bot_admins.yaml"
    _instance: "BotAdminManager | None" = None
    _instances: dict[str, "BotAdminManager"] = {}

    def __new__(cls, data_dir: str | None = None):
        actual_dir = data_dir or os.path.join(os.getcwd(), cls._DEFAULT_DATA_DIR)
        if actual_dir not in cls._instances:
            instance = super().__new__(cls)
            cls._instances[actual_dir] = instance
        return cls._instances[actual_dir]

    def __init__(self, data_dir: str | None = None):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._data_dir = data_dir or os.path.join(os.getcwd(), self._DEFAULT_DATA_DIR)
        self._file_path = Path(self._data_dir) / self._DEFAULT_FILE_NAME
        self._admins: Set[str] = set()
        self._data_loaded = False
        self._initialized = True

    async def initialize(self) -> None:
        """
        异步初始化，加载持久化的管理员数据

        应在事件循环启动后调用，通常由 Bot 启动时自动调用。
        """
        if not self._data_loaded:
            await self._load()
            self._data_loaded = True

    @property
    def bot_admins(self) -> list[str]:
        """获取当前管理员列表（只读）"""
        return list(self._admins)

    async def set_bot_admins(self, value: Iterable[str]) -> None:
        """
        设置管理员列表（合并式，与现有数据取并集，不会丢失已有管理员）

        Args:
            value: 管理员ID列表
        """
        for user_id in value:
            if not isinstance(user_id, str):
                raise TypeError(f"user_id 必须是字符串类型，实际为 {type(user_id)}")
            self._admins.add(user_id)
        await self._save()

    async def add_admin(self, *user_ids: str) -> None:
        """
        添加机器人管理员

        Args:
            user_ids: 用户ID，可传入多个
        """
        for user_id in user_ids:
            if not isinstance(user_id, str):
                raise TypeError(f"user_id 必须是字符串类型，实际为 {type(user_id)}")
            self._admins.add(user_id)
        await self._save()

    async def remove_admin(self, *user_ids: str) -> None:
        """
        移除机器人管理员

        Args:
            user_ids: 用户ID，可传入多个
        """
        for user_id in user_ids:
            self._admins.discard(user_id)
        await self._save()

    def is_admin(self, user_id: str) -> bool:
        """
        检查用户是否为机器人管理员

        Args:
            user_id: 用户ID

        Returns:
            是否为机器人管理员
        """
        return user_id in self._admins

    def get_all_admins(self) -> set:
        """
        获取所有机器人管理员

        Returns:
            机器人管理员ID集合的副本
        """
        return self._admins.copy()

    async def clear_admins(self) -> None:
        """
        清空所有机器人管理员
        """
        self._admins.clear()
        await self._save()

    async def _load(self) -> None:
        """从 YAML 文件加载管理员数据（异步）"""
        try:
            if self._file_path.exists():

                def _sync_read():
                    return self._file_path.read_text(encoding="utf-8")

                content = await asyncio.to_thread(_sync_read)
                data = yaml.safe_load(content)
                if isinstance(data, dict) and "admins" in data:
                    admins = data["admins"]
                    if isinstance(admins, list):
                        self._admins = {str(a) for a in admins}
        except Exception:
            pass

    async def _save(self) -> None:
        """将管理员数据持久化到 YAML 文件（异步）"""
        try:
            self._file_path.parent.mkdir(parents=True, exist_ok=True)

            def _sync_write():
                self._file_path.write_text(
                    yaml.dump(
                        {"admins": list(self._admins)},
                        allow_unicode=True,
                        default_flow_style=False,
                    ),
                    encoding="utf-8",
                )

            await asyncio.to_thread(_sync_write)
        except Exception:
            pass

    def __contains__(self, user_id: str) -> bool:
        return self.is_admin(user_id)

    def __len__(self) -> int:
        return len(self._admins)

    def __repr__(self) -> str:
        return f"<BotAdminManager admins_count={len(self._admins)}>"


class BotCommandObject:
    """
    机器人的on_command命令对象，用于存储机器人命令的数据

    :param command: 可触发事件的指令列表，与正则 regex 互斥，优先使用此项
    :param regex: 可触发指令的正则 compile 实例或正则表达式，与指令表互斥
    :param func: 指令触发后的回调函数
    :param treat: 是否返回处理后的消息
    :param at: 是否要求必须艾特机器人才能触发指令
    :param short_circuit: 如果触发指令成功是否短路不运行后续指令（将根据注册顺序和 command 先 regex 后排序指令的短路机制）
    :param is_custom_short_circuit: 如果触发指令成功而回调函数返回True则不运行后续指令，存在时优先于short_circuit
    :param admin: 是否要求频道主或或管理才可触发指令
    :param admin_error_msg: 当admin为True，而触发用户的权限不足时，如此项不为None，返回此消息并短路；否则不进行短路
    :param valid_scenes: 此机器人命令的有效场景，可传入多个场景，如 CommandValidScenes.GUILD|CommandValidScenes.DM，默认全部
    :param enabled: 是否启用此指令，默认True
    :param is_require_bot_admin: 是否要求机器人管理员才可触发指令，默认False
    :param bot_admin_error_msg: 当is_require_bot_admin为True，而触发用户的权限不足时，如此项不为None，返回此消息并短路；否则不进行短路
    """

    def _validate_bool_param(self, name: str, value: Any) -> None:
        """验证布尔类型参数"""
        if not isinstance(value, bool):
            raise TypeError(f"{name} must be of type bool")

    def __init__(
        self,
        command: Iterable[str] = None,
        regex: Iterable[Pattern] = None,
        func: Callable = None,
        treat: bool = True,
        at: bool = False,
        short_circuit: bool = True,
        is_custom_short_circuit: bool = False,
        admin: bool = False,
        admin_error_msg: str | None = None,
        valid_scenes: CommandValidScenes = CommandValidScenes.ALL,
        enabled: bool = True,
        is_require_bot_admin: bool = False,
        bot_admin_error_msg: str | None = None,
    ):
        # 处理 command 参数（支持 None，表示接受任意输入）
        _command = None
        if command is not None:
            if isinstance(command, str):
                _command = (command,)
            elif isinstance(command, Iterable):
                _command = []
                for i in command:
                    if not isinstance(i, str):
                        raise TypeError("command must be of type Iterable[str]")
                    _command.append(i)
            else:
                raise TypeError("command must be of type Iterable[str]")

        # 处理 regex 参数（支持 None）
        _regex = None
        if regex is not None:
            if isinstance(regex, Pattern):
                _regex = (regex,)
            elif isinstance(regex, str):
                _regex = (re.compile(regex),)
            elif isinstance(regex, Iterable):
                _regex = []
                for x in regex:
                    if isinstance(x, str):
                        _regex.append(re.compile(x))
                    elif isinstance(x, Pattern):
                        _regex.append(x)
                    else:
                        raise TypeError("regex must be of type Iterable[Pattern]")
            else:
                raise TypeError("regex must be of type Iterable[Pattern]")

        # 验证布尔类型参数
        self._validate_bool_param("treat", treat)
        self._validate_bool_param("at", at)
        self._validate_bool_param("short_circuit", short_circuit)
        self._validate_bool_param("enabled", enabled)
        self._validate_bool_param("is_require_bot_admin", is_require_bot_admin)

        # 设置属性
        self.command: Iterable[str] | None = _command
        self.regex: Iterable[Pattern] | None = _regex
        self.func: Callable = func
        self.treat: bool = treat
        self.at: bool = at
        self.short_circuit: bool = short_circuit
        self.is_custom_short_circuit: bool = is_custom_short_circuit
        self.admin: bool = admin
        self.admin_error_msg: str | None = admin_error_msg
        self.valid_scenes: CommandValidScenes = valid_scenes
        self.enabled: bool = enabled
        self.is_require_bot_admin: bool = is_require_bot_admin
        self.bot_admin_error_msg: str | None = bot_admin_error_msg

    def __hash__(self) -> int:
        """计算哈希值，用于字典键和集合元素"""
        return hash(
            (
                tuple(self.command) if self.command is not None else None,
                tuple(self.regex) if self.regex is not None else None,
                self.treat,
                self.at,
                self.short_circuit,
                self.is_custom_short_circuit,
                self.admin,
                self.valid_scenes,
                self.enabled,
                self.is_require_bot_admin,
            )
        )

    def __eq__(self, other: Any) -> bool:
        """比较两个 BotCommandObject 是否相等"""
        if not isinstance(other, BotCommandObject):
            return NotImplemented
        return (
            self.command == other.command
            and self.regex == other.regex
            and self.treat == other.treat
            and self.at == other.at
            and self.short_circuit == other.short_circuit
            and self.is_custom_short_circuit == other.is_custom_short_circuit
            and self.admin == other.admin
            and self.valid_scenes == other.valid_scenes
            and self.enabled == other.enabled
            and self.is_require_bot_admin == other.is_require_bot_admin
        )

    def __repr__(self):
        if self.command:
            return f"<BotCommandObject command={self.command} func={self.func} valid_scenes={self.valid_scenes}>"
        else:
            return f"<BotCommandObject regex={self.regex} func={self.func} valid_scenes={self.valid_scenes}>"


class Plugins:
    _commands: list[BotCommandObject] = []
    _preprocessors: dict[
        int,
        list[Callable],
    ] = {1 << x: [] for x in range(CommandValidScenes.ALL.bit_length())}
    _module_commands: dict[str, list[str]] = defaultdict(list)
    _module_preprocessors: dict[str, list[str]] = defaultdict(list)
    _command_to_module: dict[str, str] = {}
    _module_paths: dict[str, Path] = {}
    _current_loading_module: str | None = None

    @classmethod
    def _get_caller_module(cls) -> str:
        """
        从调用栈获取调用者模块名

        用于追踪命令和预处理器的归属模块，支持热重载功能。
        跳过 easybot 包内部的模块，返回外部调用者的模块名。
        """
        if cls._current_loading_module is not None:
            return cls._current_loading_module

        frame = inspect.currentframe()
        try:
            for _ in range(15):
                frame = frame.f_back
                if frame is None:
                    break
                module_name = frame.f_globals.get("__name__", "")
                if module_name and not module_name.startswith("_"):
                    if not module_name.startswith("easybot"):
                        return module_name
            return "__main__"
        finally:
            del frame

    @classmethod
    def get_all_commands(cls) -> list[BotCommandObject]:
        """
        获取所有已注册的命令（包括禁用的）

        Returns:
            所有命令对象列表
        """
        return Plugins._commands.copy()

    @classmethod
    def find_command(cls, func_name_or_command: str) -> BotCommandObject | None:
        """
        查找命令对象

        支持两种查找方式：
        - 通过函数名：如 "ping_cmd"
        - 通过命令名：如 "/ping" 或 "ping"（自动去除 / 前缀）

        Args:
            func_name_or_command: 函数名或命令名

        Returns:
            找到的命令对象，未找到返回 None
        """
        cmd_name = func_name_or_command.lstrip("/")
        for cmd in cls._commands:
            if cmd.func.__name__ == func_name_or_command:
                return cmd
            if cmd.command:
                for trigger in cmd.command:
                    if trigger.lstrip("/") == cmd_name:
                        return cmd

        return None

    @classmethod
    def enable_command(cls, func_name_or_command: str) -> bool:
        """
        启用指定的命令

        支持通过函数名或命令名查找。

        Args:
            func_name_or_command: 函数名或命令名

        Returns:
            是否成功启用
        """
        cmd = cls.find_command(func_name_or_command)
        if cmd:
            cmd.enabled = True
            return True
        return False

    @classmethod
    def disable_command(cls, func_name_or_command: str) -> bool:
        """
        禁用指定的命令

        支持通过函数名或命令名查找。

        Args:
            func_name_or_command: 函数名或命令名

        Returns:
            是否成功禁用
        """
        cmd = cls.find_command(func_name_or_command)
        if cmd:
            cmd.enabled = False
            return True
        return False

    @classmethod
    def is_command_enabled(cls, func_name_or_command: str) -> bool | None:
        """
        检查指定的命令是否启用

        支持通过函数名或命令名查找。

        Args:
            func_name_or_command: 函数名或命令名

        Returns:
            是否启用，未找到返回 None
        """
        cmd = cls.find_command(func_name_or_command)
        if cmd:
            return cmd.enabled
        return None

    @classmethod
    def remove_command(cls, func_name_or_command: str) -> bool:
        """
        移除指定的命令

        支持通过函数名或命令名查找。

        Args:
            func_name_or_command: 函数名或命令名

        Returns:
            是否成功移除
        """
        cmd = cls.find_command(func_name_or_command)
        if cmd and cmd in cls._commands:
            cls._commands.remove(cmd)
            return True
        return False

    @classmethod
    def before_command(
        cls,
        valid_scenes: CommandValidScenes = CommandValidScenes.ALL,
    ):
        """
        注册plugins预处理器，将在检查所有commands前执行

        :param valid_scenes: 此处理器的有效场景，可传入多个场景，默认 CommandValidScenes.ALL
        """

        def wrap(func: Callable):
            module_name = cls._get_caller_module()
            for bit in range(CommandValidScenes.ALL.bit_length()):
                current_bit = 1 << bit
                if current_bit & valid_scenes:
                    Plugins._preprocessors[current_bit].append(func)
            Plugins._module_preprocessors[module_name].append(func.__name__)
            return func

        return wrap

    @classmethod
    def on_command(
        cls,
        command: Union[Iterable[str], str, None] = None,
        regex: Union[Pattern, str, Iterable[Union[Pattern, str]], None] = None,
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
        注册plugins指令装饰器，可用于分割式编写指令并注册进机器人

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
            if is_short_circuit and is_custom_short_circuit:
                print(
                    "注意is_short_circuit与is_custom_short_circuit同时存在，将优先使用is_custom_short_circuit"
                )
            module_name = cls._get_caller_module()
            _kwargs = {
                "func": func,
                "treat": is_treat,
                "at": is_require_at,
                "short_circuit": is_short_circuit,
                "is_custom_short_circuit": is_custom_short_circuit,
                "admin": is_require_admin,
                "admin_error_msg": admin_error_msg,
                "valid_scenes": valid_scenes,
                "enabled": enabled,
                "is_require_bot_admin": is_require_bot_admin,
                "bot_admin_error_msg": bot_admin_error_msg,
            }
            if command:
                if isinstance(command, str):
                    command_obj = BotCommandObject(command=[command], **_kwargs)
                elif isinstance(command, Iterable):
                    command_obj = BotCommandObject(command=command, **_kwargs)
                else:
                    raise TypeError("command参数仅接受str或list类型的指令内容")
            else:
                if isinstance(regex, str):
                    command_obj = BotCommandObject(regex=[re.compile(regex)], **_kwargs)
                elif isinstance(regex, Pattern):
                    command_obj = BotCommandObject(regex=[regex], **_kwargs)
                elif isinstance(regex, Iterable):
                    regexs = []
                    for x in regex:
                        if isinstance(x, str):
                            regexs.append(re.compile(x))
                        elif isinstance(x, Pattern):
                            regexs.append(x)
                        else:
                            raise TypeError(
                                "regex参数仅接受re.compile返回的实例或str类型的正则表达式"
                            )
                    command_obj = BotCommandObject(regex=regexs, **_kwargs)
                else:
                    raise TypeError(
                        "regex参数仅接受re.compile返回的实例或str类型的正则表达式"
                    )
            Plugins._commands.append(command_obj)
            Plugins._module_commands[module_name].append(func.__name__)
            if command_obj.command:
                for cmd_name in command_obj.command:
                    Plugins._command_to_module[cmd_name.lstrip("/")] = module_name
            return func

        return wrap

    @classmethod
    def get_loaded_plugins(cls) -> list[str]:
        """
        获取所有已加载插件的模块名列表

        过滤掉非插件模块：
        - SDK 内部模块（easybot.plugins）
        - 主程序模块（__main__）

        Returns:
            插件名列表
        """
        return [
            m
            for m in cls._module_paths.keys()
            if m != "easybot.plugins" and m != "__main__"
        ]

    @classmethod
    def _find_module_by_name(cls, plugin_name: str) -> str | None:
        """
        根据插件名查找匹配的已加载模块名

        支持模糊匹配：
        - 精确匹配: "hot_reload" -> "hot_reload"
        - 后缀匹配: "admin" -> "admin.admin"

        Args:
            plugin_name: 插件名（文件名，不含 .py）

        Returns:
            匹配的模块名，未找到返回 None
        """
        modules = cls.get_loaded_plugins()

        if plugin_name in modules:
            return plugin_name

        for module_name in modules:
            if module_name.endswith(f".{plugin_name}"):
                return module_name

        return None

    @classmethod
    def get_plugin_commands(cls, plugin_name: str) -> list[str]:
        """
        获取指定插件注册的所有命令函数名

        Args:
            plugin_name: 插件名

        Returns:
            命令函数名列表
        """
        return cls._module_commands.get(plugin_name, []).copy()

    @classmethod
    def get_plugin_preprocessors(cls, plugin_name: str) -> list[str]:
        """
        获取指定插件注册的所有预处理器函数名

        Args:
            plugin_name: 插件名

        Returns:
            预处理器函数名列表
        """
        return cls._module_preprocessors.get(plugin_name, []).copy()

    @classmethod
    def reload_plugin(
        cls, plugin_name_or_command: str, plugins_dir: str | Path = "plugins"
    ) -> dict:
        """
        热重载指定插件

        只支持通过 @Plugins.on_command 注册的插件，不支持 @bot.on_command 注册的命令。

        自动识别参数类型：
        - 先尝试从已加载模块获取路径
        - 再尝试作为插件文件名
        - 最后尝试作为命令名查找对应的插件

        Args:
            plugin_name_or_command: 插件名或命令名
            plugins_dir: 插件目录路径

        Returns:
            重载结果信息
        """
        matched_module = cls._find_module_by_name(plugin_name_or_command)
        if matched_module and matched_module in cls._module_paths:
            return cls._reload_module(cls._module_paths[matched_module], plugins_dir)

        plugins_path = Path(plugins_dir)
        plugin_path = plugins_path / f"{plugin_name_or_command}.py"
        if plugin_path.exists():
            return cls._reload_module(plugin_path, plugins_dir)

        plugin_subdir = (
            plugins_path / plugin_name_or_command / f"{plugin_name_or_command}.py"
        )
        if plugin_subdir.exists():
            return cls._reload_module(plugin_subdir, plugins_dir)

        cmd_name = plugin_name_or_command.lstrip("/")
        module_name = cls._command_to_module.get(cmd_name)

        if module_name:
            if module_name in cls._module_paths:
                return cls._reload_module(cls._module_paths[module_name], plugins_dir)
            return {
                "module": module_name,
                "success": False,
                "error": f"插件 {module_name} 未找到文件路径",
            }

        loaded = cls.get_loaded_plugins()
        return {
            "module": plugin_name_or_command,
            "success": False,
            "error": f"未找到插件或命令: {plugin_name_or_command}",
            "loaded_plugins": loaded,
        }

    @classmethod
    def unload_plugin(cls, plugin_name_or_command: str) -> dict[str, int]:
        """
        卸载指定插件的所有命令和预处理器

        只支持通过 @Plugins.on_command 注册的插件，不支持 @bot.on_command 注册的命令。

        自动识别参数类型：
        - 先尝试作为插件名匹配
        - 找不到则尝试作为命令名查找对应的插件

        Args:
            plugin_name_or_command: 插件名或命令名

        Returns:
            包含卸载数量的字典: {"commands": int, "preprocessors": int}
        """
        plugin_name = cls._find_module_by_name(plugin_name_or_command)

        if plugin_name is None:
            cmd_name = plugin_name_or_command.lstrip("/")
            plugin_name = cls._command_to_module.get(cmd_name)

        if plugin_name is None:
            return {"commands": 0, "preprocessors": 0}

        result = {"commands": 0, "preprocessors": 0}

        if (
            plugin_name not in cls._module_commands
            and plugin_name not in cls._module_preprocessors
        ):
            return result

        if plugin_name in cls._module_commands:
            cmd_names = cls._module_commands[plugin_name]
            cls._commands = [
                cmd for cmd in cls._commands if cmd.func.__name__ not in cmd_names
            ]
            result["commands"] = len(cmd_names)
            del cls._module_commands[plugin_name]

            cls._command_to_module = {
                cmd: mod
                for cmd, mod in cls._command_to_module.items()
                if mod != plugin_name
            }

        if plugin_name in cls._module_preprocessors:
            preprocessor_names = cls._module_preprocessors[plugin_name]
            for scene_bit in cls._preprocessors:
                cls._preprocessors[scene_bit] = [
                    func
                    for func in cls._preprocessors[scene_bit]
                    if func.__name__ not in preprocessor_names
                ]
            result["preprocessors"] = len(preprocessor_names)
            del cls._module_preprocessors[plugin_name]

        cls._module_paths.pop(plugin_name, None)

        return result

    @classmethod
    def _reload_module(
        cls, module_path: Path | str, plugins_dir: str | Path = "plugins"
    ) -> dict:
        """
        热重载指定插件模块（内部方法）

        先卸载该模块的所有命令和预处理器，然后重新导入模块。

        Args:
            module_path: 插件文件路径（绝对路径或相对路径）
            plugins_dir: 插件目录路径

        Returns:
            重载结果信息:
            {
                "module": str,       # 模块名
                "unloaded": dict,    # 卸载的命令和预处理器数量
                "loaded": dict,      # 新加载的命令和预处理器数量
                "success": bool,     # 是否成功
                "error": str | None  # 错误信息（如果失败）
            }
        """
        module_path = Path(module_path)
        module_name = module_path.stem

        plugins_path = Path(plugins_dir)
        if module_path.is_relative_to(plugins_path):
            rel_path = module_path.relative_to(plugins_path)
            parts = list(rel_path.parts)
            if len(parts) > 1:
                module_name = ".".join(parts[:-1] + [module_path.stem])

        result = {
            "module": module_name,
            "unloaded": {"commands": 0, "preprocessors": 0},
            "loaded": {"commands": 0, "preprocessors": 0},
            "success": False,
            "error": None,
        }

        try:
            matched_module = cls._find_module_by_name(module_path.stem)
            if matched_module:
                result["unloaded"] = cls.unload_plugin(matched_module)
                if matched_module in sys.modules:
                    del sys.modules[matched_module]

            if module_name in sys.modules:
                del sys.modules[module_name]

            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                cls._current_loading_module = module_name
                try:
                    spec.loader.exec_module(module)
                    cls._module_paths[module_name] = module_path.resolve()
                finally:
                    cls._current_loading_module = None

            result["loaded"]["commands"] = len(
                cls._module_commands.get(module_name, [])
            )
            result["loaded"]["preprocessors"] = len(
                cls._module_preprocessors.get(module_name, [])
            )
            result["success"] = True

        except Exception as e:
            result["error"] = str(e)
            cls._current_loading_module = None

        return result

    @classmethod
    def clear_all_plugins(cls) -> dict[str, int]:
        """
        清空所有已注册的命令和预处理器

        Returns:
            清空的命令和预处理器数量
        """
        result = {
            "commands": len(cls._commands),
            "preprocessors": sum(len(v) for v in cls._preprocessors.values()),
        }
        cls._commands.clear()
        cls._module_commands.clear()
        for scene_bit in cls._preprocessors:
            cls._preprocessors[scene_bit].clear()
        cls._module_preprocessors.clear()
        cls._command_to_module.clear()
        cls._module_paths.clear()
        return result
