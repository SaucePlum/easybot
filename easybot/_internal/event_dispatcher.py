#!/usr/bin/env python3
"""
EasyBot SDK 统一事件分发器模块

提供统一的事件分发功能，支持沙箱过滤、消息去重、模型转换和事件处理器调用。
"""

import asyncio
import inspect
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ..plugins import CommandValidScenes, Plugins
from .constants import C2C_EVENTS, DIRECT_MESSAGE_EVENTS, GROUP_EVENTS, convert_to_model
from .dedup import DedupConfig, MessageDeduplicator
from .event_utils import check_sandbox
from .message_utils import check_user_is_admin, treat_message_content

if TYPE_CHECKING:
    from ..bot import Bot


@dataclass
class DispatchResult:
    """事件分发结果"""

    dispatched: bool
    event_type: str
    filtered_by_sandbox: bool = False
    filtered_by_dedup: bool = False
    no_handler: bool = False


class EventDispatcher:
    """
    统一事件分发器

    职责：
    - 沙箱过滤
    - 消息去重
    - 模型转换
    - 调用用户注册的事件处理器
    - 异常捕获与日志记录
    """

    __slots__ = ("_bot", "_logger", "_dedup_config", "_deduplicator")

    def __init__(
        self,
        bot: "Bot",
        logger: Any,
        dedup_config: DedupConfig | None = None,
    ):
        self._bot = bot
        self._logger = logger
        self._dedup_config = dedup_config or DedupConfig()
        self._deduplicator = (
            MessageDeduplicator(
                max_size=self._dedup_config.max_size,
                ttl_seconds=self._dedup_config.ttl_seconds,
            )
            if self._dedup_config.enabled
            else None
        )

    async def dispatch(
        self,
        event_type: str,
        data: dict[str, Any],
        *,
        event_id: str | None = None,
        seq: int | None = None,
        opcode: int = 0,
        skip_sandbox: bool = False,
        skip_dedup: bool = False,
    ) -> DispatchResult:
        """
        分发事件到处理器

        Args:
            event_type: 事件类型（如 AT_MESSAGE_CREATE）
            data: 事件原始数据
            event_id: 事件 ID（来自 Payload.id）
            seq: 序列号（来自 Payload.s）
            opcode: 操作码（来自 Payload.op）
            skip_sandbox: 是否跳过沙箱检查
            skip_dedup: 是否跳过去重检查

        Returns:
            DispatchResult: 分发结果
        """
        # 1. 沙箱过滤
        if not skip_sandbox:
            if not check_sandbox(
                self._bot.sandbox, self._bot.is_sandbox, data, event_type
            ):
                return DispatchResult(
                    dispatched=False,
                    event_type=event_type,
                    filtered_by_sandbox=True,
                )

        # 2. 消息去重
        if not skip_dedup and self._deduplicator is not None:
            message_id = data.get("id", "")
            if message_id and not self._deduplicator.check_and_mark(message_id):
                self._logger.debug(f"重复消息被过滤: {event_type}, id={message_id}")
                return DispatchResult(
                    dispatched=False,
                    event_type=event_type,
                    filtered_by_dedup=True,
                )

        # 3. 模型转换
        model = convert_to_model(
            event_type, data, self._bot.api, event_id=event_id, seq=seq, opcode=opcode
        )

        # 4. 插件系统处理
        short_circuited = False
        if model:
            short_circuited = await self._process_plugin_system(event_type, model)

        # 如果插件系统已经短路（比如匹配到了 wait_for 命令），就不继续处理事件处理器了
        if short_circuited:
            return DispatchResult(dispatched=True, event_type=event_type)

        # 5. 事件处理器调用
        handler = self._bot._event_handlers.get(event_type)
        if handler is None:
            return DispatchResult(
                dispatched=False,
                event_type=event_type,
                no_handler=True,
            )

        # 6. 安全调用处理器
        asyncio.create_task(
            self._safe_call_handler(event_type, handler, model if model else data)
        )

        return DispatchResult(dispatched=True, event_type=event_type)

    async def _process_plugin_system(self, event_type: str, model: Any) -> bool:
        """处理插件系统逻辑

        Returns:
            bool: 如果匹配到 wait_for 命令并且短路，返回 True，否则返回 False
        """
        scene_bit = self._get_scene_bit(event_type)
        if scene_bit is None:
            return False

        if hasattr(model, "content"):
            if not hasattr(model, "treated_msg"):
                model.treated_msg = ""
            model.treated_msg = treat_message_content(model.content, self._bot.bot_id)
            if model._raw_data is not None:
                model._raw_data["treated_msg"] = model.treated_msg

        preprocessors = Plugins._preprocessors.get(scene_bit, [])
        for preprocessor in preprocessors:
            try:
                if asyncio.iscoroutinefunction(preprocessor):
                    result = await preprocessor(model)
                else:
                    result = preprocessor(model)
                if result is False:
                    return False
            except Exception as e:
                self._logger.exception(f"预处理器执行错误: {e}")

        return await self._process_commands(scene_bit, model)

    def _get_scene_bit(self, event_type: str) -> int | None:
        """根据事件类型获取场景位"""
        match event_type:
            case "AT_MESSAGE_CREATE" | "MESSAGE_CREATE":
                return CommandValidScenes.GUILD
            case _ if event_type in DIRECT_MESSAGE_EVENTS:
                return CommandValidScenes.DM
            case _ if event_type in GROUP_EVENTS:
                return CommandValidScenes.GROUP
            case _ if event_type in C2C_EVENTS:
                return CommandValidScenes.C2C
            case _:
                return None

    def _get_max_command_length(self, cmd_obj: Any) -> int:
        """
        获取命令对象中命令字符串的最大长度

        支持两种对象类型：
        - WaitFor 命令对象：访问 cmd_obj.command.command
        - 普通命令对象：访问 cmd_obj.command
        """
        inner_cmd = getattr(cmd_obj, "command", None)
        if inner_cmd is None:
            return 0

        # 检查是否是 WaitFor 命令对象
        actual_commands = getattr(inner_cmd, "command", None)
        if actual_commands is None:
            actual_commands = inner_cmd

        # 处理不同类型的命令
        if isinstance(actual_commands, str):
            return len(actual_commands)
        elif hasattr(actual_commands, "__iter__") and not isinstance(
            actual_commands, str
        ):
            return max(len(c) for c in actual_commands) if actual_commands else 0
        return 0

    async def _process_commands(self, scene_bit: int, model: Any) -> bool:
        """
        处理命令匹配和执行

        使用最长匹配优先策略：
        1. 收集所有能匹配的命令及其匹配长度
        2. 按匹配长度降序排序，选择最长的匹配
        3. 执行最佳匹配并处理短路

        Returns:
            bool: 如果匹配到 wait_for 命令并且短路，返回 True，否则返回 False
        """
        # 1. 检查 WaitFor 命令（保持原有逻辑）
        wait_for_commands = self._bot.session.wait_for_message_checker(model)

        sorted_wait_for = sorted(
            wait_for_commands, key=self._get_max_command_length, reverse=True
        )

        for x in sorted_wait_for:
            if x.command.valid_scenes & scene_bit == 0:
                continue

            if x.command.at:
                if not self._check_message_contains_at(model):
                    continue

            if x.predicate is not None:
                try:
                    if not x.predicate(model):
                        continue
                except Exception as e:
                    self._logger.exception(f"wait_for 谓词函数执行错误: {e}")
                    continue

            match_result = self._match_command(x.command, model)

            if (x.command.command is None and x.command.regex is None) or (
                match_result is not None
            ):
                x.callback(model)
                if x.command.short_circuit:
                    return True
                break

        # 2. 处理普通命令 - 使用最长匹配优先策略
        valid_commands = [
            cmd
            for cmd in Plugins._commands
            if cmd.enabled and (cmd.valid_scenes & scene_bit)
        ]

        # 收集所有能匹配的命令及其匹配信息
        candidates: list[tuple[Any, str, int]] = []
        for cmd in valid_commands:
            if cmd.at:
                if not self._check_message_contains_at(model):
                    continue

            match_result = self._match_command(cmd, model)
            if match_result is not None:
                matched_cmd, match_length = match_result
                candidates.append((cmd, matched_cmd, match_length))

        # 没有匹配的命令
        if not candidates:
            return False

        # 按匹配长度降序排序（最长匹配优先），长度相同则保持原始顺序
        candidates.sort(key=lambda x: x[2], reverse=True)

        # 当存在多个候选时输出调试日志
        if len(candidates) > 1:
            raw_content = getattr(model, "content", "")[:50]
            self._logger.debug(
                f"检测到多个命令匹配 [{raw_content}...]："
                f"{[(c[1], c[2]) for c in candidates]}，"
                f"选择最长匹配: {candidates[0][1]}"
            )

        # 只执行最佳匹配（第一个，即最长的）
        best_cmd, best_matched, _ = candidates[0]

        # 权限检查
        if best_cmd.admin:
            if not self._check_user_admin(model):
                if best_cmd.admin_error_msg:
                    await self._reply_error(model, best_cmd.admin_error_msg)
                if best_cmd.short_circuit:
                    return True
                return False

        if best_cmd.is_require_bot_admin:
            user_id = self._get_user_id(model)
            if user_id and not self._bot.bot_admin_manager.is_admin(user_id):
                if best_cmd.bot_admin_error_msg:
                    await self._reply_error(model, best_cmd.bot_admin_error_msg)
                if best_cmd.short_circuit:
                    return True
                return False

        # 执行命令
        try:
            should_short_circuit = False

            if asyncio.iscoroutinefunction(best_cmd.func):
                if best_cmd.is_custom_short_circuit:
                    result = await self._execute_command_with_result(best_cmd, model)
                    should_short_circuit = bool(result)
                else:
                    asyncio.create_task(
                        self._execute_command_with_result(best_cmd, model)
                    )
                    should_short_circuit = best_cmd.short_circuit
            else:
                result = best_cmd.func(model)
                if best_cmd.is_custom_short_circuit:
                    should_short_circuit = bool(result)
                else:
                    should_short_circuit = best_cmd.short_circuit

            if should_short_circuit:
                return True
        except Exception as e:
            self._logger.exception(f"命令执行错误: {e}")

        return False

    async def _execute_command_with_result(self, cmd: Any, model: Any) -> Any:
        """
        异步执行命令回调并返回结果

        用于需要获取命令执行返回值的场景（如自定义短路判断）

        Args:
            cmd: 命令对象
            model: 消息模型

        Returns:
            命令执行的返回值，异常时返回 None
        """
        try:
            sig = inspect.signature(cmd.func)
            if "session" in sig.parameters:
                return await cmd.func(model, session=self._bot.session)
            else:
                return await cmd.func(model)
        except Exception as e:
            self._logger.exception(f"命令执行错误: {e}")
            return None

    def _check_message_contains_at(self, model: Any) -> bool:
        """检查消息是否包含艾特机器人"""
        if not self._bot.bot_id:
            return False
        content = getattr(model, "content", "")
        return (
            f"<@!{self._bot.bot_id}>" in content or f"<@{self._bot.bot_id}>" in content
        )

    def _check_user_admin(self, model: Any) -> bool:
        """检查用户是否为频道管理员"""

        member = getattr(model, "member", None)
        if member:
            roles = getattr(member, "roles", [])
            return check_user_is_admin(roles)
        return False

    def _get_user_id(self, model: Any) -> str | None:
        """获取用户ID"""
        author = getattr(model, "author", None)
        if author:
            return (
                getattr(author, "id", None)
                or getattr(author, "user_openid", None)
                or getattr(author, "member_openid", None)
                or getattr(author, "union_openid", None)
                or getattr(author, "union_user_account", None)
            )
        return None

    async def _reply_error(self, model: Any, error_msg: str) -> None:
        """回复错误消息"""
        reply_method = getattr(model, "reply", None)
        if reply_method:
            try:
                await reply_method(error_msg)
            except Exception as e:
                self._logger.error(f"回复错误消息失败: {e}")

    def _match_command(self, cmd: Any, model: Any) -> tuple[str, int] | None:
        """
        匹配命令，返回 (匹配的命令字符串, 匹配长度) 或 None

        使用最长匹配优先策略：返回实际匹配到的命令及其长度，
        供调用方选择最优匹配。
        """
        raw_content = getattr(model, "content", "")

        if cmd.command:
            for command in cmd.command:
                if command.startswith("/"):
                    if raw_content.strip().startswith(command):
                        if cmd.treat:
                            if hasattr(model, "content"):
                                if not hasattr(model, "treated_msg"):
                                    model.treated_msg = ""
                                model.treated_msg = raw_content.strip()[
                                    len(command) :
                                ].strip()
                                if model._raw_data is not None:
                                    model._raw_data["treated_msg"] = model.treated_msg
                        return (command, len(command))
                else:
                    treated_msg = getattr(model, "treated_msg", raw_content)
                    msg = treated_msg if cmd.treat else raw_content
                    if msg.strip().startswith(command):
                        return (command, len(command))
        elif cmd.regex:
            treated_msg = getattr(model, "treated_msg", raw_content)
            msg = treated_msg if cmd.treat else raw_content
            for regex in cmd.regex:
                match = regex.match(msg)
                if match:
                    if cmd.treat:
                        if not hasattr(model, "treated_msg"):
                            model.treated_msg = ""
                        model.treated_msg = match.groups()
                        if model._raw_data is not None:
                            model._raw_data["treated_msg"] = model.treated_msg
                    matched_str = match.group(0)
                    return (regex.pattern, len(matched_str))

        return None

    async def _safe_call_handler(
        self,
        event_type: str,
        handler: Callable,
        data: Any,
    ) -> None:
        """安全调用事件处理器，捕获异常并记录日志"""
        try:
            await handler(data)
        except Exception as e:
            self._logger.exception(f"事件处理器执行错误 [{event_type}]: {e}")
