#!/usr/bin/env python3
"""
EasyBot SDK 插件系统模块

提供预处理器、命令插件系统和权限管理功能。
"""

import os
import re
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
    机器人管理员管理器，用于管理全局机器人管理员（超管）

    管理员数据自动持久化到 YAML 文件（默认 sdk_data/bot_admins.yaml），
    启动时自动加载，增删操作后自动保存。

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

    def __init__(self, data_dir: str | None = None):
        self._data_dir = data_dir or os.path.join(os.getcwd(), self._DEFAULT_DATA_DIR)
        self._file_path = Path(self._data_dir) / self._DEFAULT_FILE_NAME
        self._admins: Set[str] = set()
        self._load()

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

    @classmethod
    def get_commands_and_preprocessors(
        cls,
    ) -> tuple[list[BotCommandObject], dict[int, list[Callable]]]:
        """
        获取启用的命令和预处理器

        Returns:
            启用的命令列表和预处理器字典
        """
        commands = [cmd for cmd in Plugins._commands if cmd.enabled]
        preprocessors = Plugins._preprocessors
        return commands, preprocessors

    @classmethod
    def get_preprocessor_names(cls):
        """
        获取所有预处理器的名称

        Returns:
            预处理器名称的生成器
        """
        return (
            func.__name__ for funcs in Plugins._preprocessors.values() for func in funcs
        )

    @classmethod
    def get_commands_names(cls):
        """
        获取所有命令的名称

        Returns:
            命令名称的生成器
        """
        return (x.func.__name__ for x in Plugins._commands)

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
            for bit in range(CommandValidScenes.ALL.bit_length()):
                current_bit = 1 << bit
                if current_bit & valid_scenes:
                    Plugins._preprocessors[current_bit].append(func)
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
            return func

        return wrap
