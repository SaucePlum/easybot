#!/usr/bin/env python3
"""
EasyBot SDK 插件系统模块

提供预处理器、命令插件系统和权限管理功能。
"""

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

    使用示例:
        admin_manager = BotAdminManager()

        # 批量设置管理员列表（合并式，会持久化）
        admin_manager.bot_admins = ["user_id_1", "user_id_2"]

        # 增量添加/移除
        admin_manager.add_admin("user_id_3")
        admin_manager.remove_admin("user_id_1")

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
        self._load()
        self._initialized = True

    @property
    def bot_admins(self) -> list[str]:
        """获取当前管理员列表"""
        return list(self._admins)

    @bot_admins.setter
    def bot_admins(self, value: Iterable[str]) -> None:
        """设置管理员列表（合并式，与现有数据取并集，不会丢失已有管理员）"""
        for user_id in value:
            if not isinstance(user_id, str):
                raise TypeError(f"user_id 必须是字符串类型，实际为 {type(user_id)}")
            self._admins.add(user_id)
        self._save()

    def add_admin(self, *user_ids: str) -> None:
        """
        添加机器人管理员

        :param user_ids: 用户ID，可传入多个
        """
        for user_id in user_ids:
            if not isinstance(user_id, str):
                raise TypeError(f"user_id 必须是字符串类型，实际为 {type(user_id)}")
            self._admins.add(user_id)
        self._save()

    def remove_admin(self, *user_ids: str) -> None:
        """
        移除机器人管理员

        :param user_ids: 用户ID，可传入多个
        """
        for user_id in user_ids:
            self._admins.discard(user_id)
        self._save()

    def is_admin(self, user_id: str) -> bool:
        """
        检查用户是否为机器人管理员

        :param user_id: 用户ID
        :return: 是否为机器人管理员
        """
        return user_id in self._admins

    def get_all_admins(self) -> set:
        """
        获取所有机器人管理员

        :return: 机器人管理员ID集合的副本
        """
        return self._admins.copy()

    def clear_admins(self) -> None:
        """
        清空所有机器人管理员
        """
        self._admins.clear()
        self._save()

    def _load(self) -> None:
        """从 YAML 文件加载管理员数据"""
        try:
            if self._file_path.exists():
                data = yaml.safe_load(self._file_path.read_text(encoding="utf-8"))
                if isinstance(data, dict) and "admins" in data:
                    admins = data["admins"]
                    if isinstance(admins, list):
                        self._admins = {str(a) for a in admins}
        except Exception:
            pass

    def _save(self) -> None:
        """将管理员数据持久化到 YAML 文件"""
        try:
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
            self._file_path.write_text(
                yaml.dump(
                    {"admins": list(self._admins)},
                    allow_unicode=True,
                    default_flow_style=False,
                ),
                encoding="utf-8",
            )
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
    _current_loading_module: str | None = None

    @classmethod
    def _get_caller_module(cls) -> str:
        """
        从调用栈获取调用者模块名

        用于追踪命令和预处理器的归属模块，支持热重载功能。
        """
        if cls._current_loading_module is not None:
            return cls._current_loading_module

        frame = inspect.currentframe()
        try:
            for _ in range(10):
                frame = frame.f_back
                if frame is None:
                    break
                module_name = frame.f_globals.get("__name__", "")
                if module_name and not module_name.startswith("_"):
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
    def find_command(cls, func_name: str) -> BotCommandObject | None:
        """
        根据函数名查找命令对象

        Args:
            func_name: 命令函数的名称

        Returns:
            找到的命令对象，未找到返回 None
        """
        for cmd in Plugins._commands:
            if cmd.func.__name__ == func_name:
                return cmd
        return None

    @classmethod
    def enable_command(cls, func_name: str) -> bool:
        """
        启用指定的命令

        Args:
            func_name: 命令函数的名称

        Returns:
            是否成功启用
        """
        cmd = cls.find_command(func_name)
        if cmd:
            cmd.enabled = True
            return True
        return False

    @classmethod
    def disable_command(cls, func_name: str) -> bool:
        """
        禁用指定的命令

        Args:
            func_name: 命令函数的名称

        Returns:
            是否成功禁用
        """
        cmd = cls.find_command(func_name)
        if cmd:
            cmd.enabled = False
            return True
        return False

    @classmethod
    def is_command_enabled(cls, func_name: str) -> bool | None:
        """
        检查指定的命令是否启用

        Args:
            func_name: 命令函数的名称

        Returns:
            是否启用，未找到返回 None
        """
        cmd = cls.find_command(func_name)
        if cmd:
            return cmd.enabled
        return None

    @classmethod
    def remove_command(cls, func_name: str) -> bool:
        """
        移除指定的命令

        Args:
            func_name: 命令函数的名称

        Returns:
            是否成功移除
        """
        for i, cmd in enumerate(Plugins._commands):
            if cmd.func.__name__ == func_name:
                del Plugins._commands[i]
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
                    Plugins._command_to_module[cmd_name] = module_name
            return func

        return wrap

    @classmethod
    def get_loaded_plugins(cls) -> list[str]:
        """
        获取所有已加载插件的模块名列表

        过滤掉 SDK 内部模块（easybot.plugins）

        Returns:
            插件名列表
        """
        modules = set(cls._module_commands.keys()) | set(
            cls._module_preprocessors.keys()
        )
        filtered = [m for m in modules if m != "easybot.plugins"]
        return filtered

    @classmethod
    def _find_module_by_name(cls, plugin_name: str) -> str | None:
        """
        根据插件名查找匹配的已加载模块名

        支持模糊匹配：
        - 精确匹配: "hot_reload" -> "hot_reload"
        - 后缀匹配: "hot_reload" -> "plugins.hot_reload"

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
    def _get_module_by_command(cls, command: str) -> str | None:
        """
        根据命令名获取所属模块名（内部方法）

        Args:
            command: 命令名（如 "/ping"）

        Returns:
            模块名，未找到返回 None
        """
        return cls._command_to_module.get(command)

    @classmethod
    def _reload_by_command(cls, command: str) -> dict:
        """
        根据命令名热重载所属插件（内部方法）

        Args:
            command: 命令名（如 "/ping"）

        Returns:
            重载结果信息
        """
        module_name = cls._get_module_by_command(command)
        if not module_name:
            return {
                "module": None,
                "command": command,
                "success": False,
                "error": f"未找到命令 {command} 对应的模块",
            }

        from pathlib import Path

        plugin_path = Path("plugins") / f"{module_name}.py"
        if not plugin_path.exists():
            return {
                "module": module_name,
                "command": command,
                "success": False,
                "error": f"插件文件不存在: {module_name}",
            }

        return cls._reload_module(plugin_path)

    @classmethod
    def reload_plugin(cls, plugin_name_or_command: str) -> dict:
        """
        自动识别并热重载插件

        自动识别参数类型：
        - 先尝试作为插件文件名
        - 找不到则尝试作为命令名

        Args:
            plugin_name_or_command: 插件名或命令名

        Returns:
            重载结果信息
        """
        from pathlib import Path

        plugin_path = Path("plugins") / f"{plugin_name_or_command}.py"

        if plugin_path.exists():
            return cls._reload_module(plugin_path)

        cmd_name = plugin_name_or_command
        if not cmd_name.startswith("/"):
            cmd_name = f"/{cmd_name}"

        module_name = cls._get_module_by_command(cmd_name)
        if module_name:
            return cls._reload_by_command(cmd_name)

        loaded = cls.get_loaded_plugins()
        return {
            "module": plugin_name_or_command,
            "success": False,
            "error": f"未找到插件或命令: {plugin_name_or_command}",
            "loaded_plugins": loaded,
        }

    @classmethod
    def unload_plugin(cls, plugin_name: str) -> dict[str, int]:
        """
        卸载指定插件的所有命令和预处理器

        Args:
            plugin_name: 插件名（不含 .py 后缀）

        Returns:
            包含卸载数量的字典: {"commands": int, "preprocessors": int}
        """
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

        return result

    @classmethod
    def _reload_module(cls, module_path: Path | str) -> dict:
        """
        热重载指定插件模块（内部方法）

        先卸载该模块的所有命令和预处理器，然后重新导入模块。

        Args:
            module_path: 插件文件路径（绝对路径或相对路径）

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

        result = {
            "module": module_name,
            "unloaded": {"commands": 0, "preprocessors": 0},
            "loaded": {"commands": 0, "preprocessors": 0},
            "success": False,
            "error": None,
        }

        try:
            matched_module = cls._find_module_by_name(module_name)
            if matched_module:
                result["unloaded"] = cls.unload_module(matched_module)
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
        return result
