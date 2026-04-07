#!/usr/bin/env python3
"""
EasyBot SDK 会话管理模块

提供会话管理和 WaitFor 命令检查功能。
"""

import asyncio
import os
import pickle
from asyncio import AbstractEventLoop, sleep
from collections import namedtuple
from collections.abc import Sequence as ABCSequence
from contextlib import contextmanager
from functools import wraps
from re import Pattern
from time import time
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Hashable,
    List,
    Optional,
    Sequence,
    Union,
)

from .builders import MessagesModel
from .exceptions import WaitError, WaitTimeoutError
from .models import (
    C2CMessage,
    DirectMessage,
    GroupMessage,
    GuildMessage,
    Model,
    SessionStatus,
)
from .plugins import BotCommandObject, CommandValidScenes

if TYPE_CHECKING:
    from .bot import Bot


class WaitForCommandCallback:
    """
    等待命令回调封装类

    当收到消息时，系统会检查是否有匹配的 wait_for 注册，
    如果有则创建此对象保存命令、回调和谓词，供后续触发使用。
    """

    def __init__(self, command, callback, predicate=None):
        self.command = command
        self.callback = callback
        self.predicate = predicate


class SessionObject:
    """
    对外暴露的会话对象

    这是一个只读的会话视图，用户通过 get/new/update 方法获得此对象。
    它不包含内部实现细节（如超时回复参数），只暴露用户关心的数据。
    """

    def __init__(self, scope, status, key, data, identify):
        self.scope = scope
        self.status = status
        self.key = key
        self.data = data
        self.identify = identify

    def __repr__(self):
        return f"<SessionObject scope={self.scope} status={self.status} key={self.key} identify={self.identify}>"


class Scope:
    """
    会话作用域枚举

    作用域决定了会话的隔离级别和生命周期：
    - USER: 用户级别，同一用户在不同频道/群的会话隔离
    - GUILD: 频道级别，同一频道内所有用户共享
    - CHANNEL: 子频道级别，同一子频道内共享
    - GROUP: 群聊级别，同一群内共享
    - GLOBAL: 全局级别，整个机器人实例共享

    作用域越小，会话越隔离；作用域越大，会话共享范围越广。
    """

    USER = "USER"
    GUILD = "GUILD"
    CHANNEL = "CHANNEL"
    GROUP = "GROUP"
    GLOBAL = "GLOBAL"


_AllScopeStr = (Scope.USER, Scope.GUILD, Scope.CHANNEL, Scope.GROUP, Scope.GLOBAL)
ScopeRegisterKey = namedtuple("ScopeRegisterKey", _AllScopeStr)


class _SessionObject:
    """
    内部会话对象

    这是实际存储在内存中的会话数据结构，包含所有内部状态。
    与 SessionObject 不同，它包含了超时处理、GC 回收等实现细节。

    超时机制说明：
    1. timeout: 会话超时时间（秒），从 last_operate 开始计算，默认 1800 秒（30 分钟）
    2. inactive_gc_timeout: 会话变为 INACTIVE 后，等待多久才真正删除
    3. gc_timeout_stamp: 预计被 GC 清理的时间戳

    这样设计是为了让用户在会话刚超时时还有机会"恢复"会话，
    比如用户可能只是回复慢了一点，不应该立即删除会话数据。
    """

    DEFAULT_TIMEOUT = 1800  # 默认会话超时时间：30 分钟

    def __init__(
        self,
        status: SessionStatus,
        data: Dict,
        timeout: Optional[float] = None,
        last_operate: float = 0,
        timeout_reply: Union[
            str,
            MessagesModel.Message,
            MessagesModel.MessageEmbed,
            MessagesModel.MessageArk23,
            MessagesModel.MessageArk24,
            MessagesModel.MessageArk37,
            MessagesModel.MessageMarkdown,
        ] = None,
        inactive_gc_timeout: float = 0,
        gc_timeout_stamp: Optional[float] = None,
        timeout_reply_api: Optional[str] = None,
        timeout_reply_params: Optional[Dict[str, Any]] = None,
        timeout_reply_message_id_expire: Optional[float] = None,
        send_reply_on_msg_id_expired: bool = False,
    ):
        self.status = status
        self.data = data
        self.timeout = timeout if timeout is not None else self.DEFAULT_TIMEOUT
        self.last_operate = last_operate
        self.timeout_reply = timeout_reply
        self.inactive_gc_timeout = inactive_gc_timeout
        self.gc_timeout_stamp = gc_timeout_stamp
        self.timeout_reply_api = timeout_reply_api
        self.timeout_reply_params = timeout_reply_params
        self.timeout_reply_message_id_expire = timeout_reply_message_id_expire
        self.send_reply_on_msg_id_expired = send_reply_on_msg_id_expired

    def __repr__(self):
        return (
            f"<_SessionObject status={self.status} data={self.data} timeout={self.timeout} "
            f"last_operate={self.last_operate} timeout_reply={self.timeout_reply} "
            f"inactive_gc_timeout={self.inactive_gc_timeout} gc_timeout_stamp={self.gc_timeout_stamp} "
            f"timeout_reply_api={self.timeout_reply_api} timeout_reply_params={self.timeout_reply_params}>"
        )


class BoundSession:
    """
    绑定了消息对象的 Session 包装器

    通过 session.bind(msg) 上下文管理器获得此对象。
    它自动从绑定的消息对象中提取 identify（用户ID/频道ID等），
    这样用户就不需要在每次调用时手动传入 identify。

    注意：所有修改操作都是异步方法，需要在异步上下文中调用。

    使用示例：
        with session.bind(msg) as s:
            await s.new(Scope.USER, "key", {"step": 1})
            data = await s.get(Scope.USER, "key")
    """

    def __init__(self, manager: "SessionManager", obj: Any):
        self._manager: "SessionManager" = manager
        self._obj: Any = obj

    async def new(
        self,
        scope: str,
        key: Hashable,
        data: Optional[Dict] = None,
        identify: Optional[Hashable] = None,
        is_replace: bool = True,
        timeout: Optional[float] = None,
        timeout_reply: Optional[
            Union[
                str,
                MessagesModel.Message,
                MessagesModel.MessageEmbed,
                MessagesModel.MessageArk23,
                MessagesModel.MessageArk24,
                MessagesModel.MessageArk37,
                MessagesModel.MessageMarkdown,
            ]
        ] = None,
        inactive_gc_timeout: Optional[float] = 0,
        send_reply_on_msg_id_expired: bool = False,
    ) -> SessionObject:
        """
        创建新会话

        Args:
            scope: 作用域，使用 Scope 常量
            key: 会话键，用于区分同一 identify 下的不同会话
            data: 会话数据字典
            identify: 标识符（通常不需要传，会自动从绑定的消息对象提取）
            is_replace: 如果会话已存在是否替换，False 时会抛出 KeyError
            timeout: 超时时间（秒），超时后会话变为 INACTIVE，默认 1800 秒（30 分钟）
            timeout_reply: 超时时发送的回复消息
            inactive_gc_timeout: 变为 INACTIVE 后多久被 GC 清理（秒）
            send_reply_on_msg_id_expired: 当 msg_id 过期（超过5分钟）时是否仍发送消息
                - False（默认）: 不发送，避免消耗主动消息配额
                - True: 发送主动消息（非回复形式，消耗主动消息配额）

        Returns:
            SessionObject: 创建的会话对象
        """
        return await self._manager._new(
            self._obj,
            scope,
            key,
            data,
            identify,
            is_replace,
            timeout,
            timeout_reply,
            inactive_gc_timeout,
            send_reply_on_msg_id_expired,
        )

    async def get(
        self,
        scope: str,
        key: Hashable,
        identify: Optional[Hashable] = None,
        default: Any = None,
        skip_update_last_op: bool = False,
    ) -> SessionObject:
        """
        获取会话

        Args:
            scope: 作用域
            key: 会话键
            identify: 标识符（通常不需要传）
            default: 会话不存在时返回的默认值
            skip_update_last_op: 是否跳过更新最后操作时间
                - False（默认）: 更新时间，重置超时计时器
                - True: 不更新时间，用于"窥视"会话状态

        Returns:
            SessionObject 或 default: 会话对象或默认值
        """
        return await self._manager._get(
            self._obj, scope, key, identify, default, skip_update_last_op
        )

    async def update(
        self,
        scope: str,
        key: Hashable,
        data: Dict,
        identify: Optional[Hashable] = None,
    ) -> SessionObject:
        """
        更新会话数据

        使用 dict.update() 语义合并数据，已存在的键会被覆盖，
        新的键会被添加。同时会更新最后操作时间。

        Args:
            scope: 作用域
            key: 会话键
            data: 要合并的数据字典
            identify: 标识符（通常不需要传）

        Returns:
            SessionObject: 更新后的会话对象

        Raises:
            KeyError: 会话不存在时抛出
        """
        return await self._manager._update(self._obj, scope, key, data, identify)

    async def remove(
        self,
        scope: Optional[str] = None,
        identify: Optional[Hashable] = None,
        key: Optional[Hashable] = None,
    ) -> None:
        """
        删除会话

        支持不同粒度的删除：
        - 不传参数：清空所有会话
        - 只传 scope：清空该作用域的所有会话
        - 传 scope + identify：清空该标识符的所有会话
        - 传 scope + identify + key：删除特定会话

        Args:
            scope: 作用域
            identify: 标识符
            key: 会话键
        """
        return await self._manager.remove(scope, identify, key)

    async def wait_for(
        self,
        scopes: Union[str, Sequence[str]],
        command: Union[str, Sequence[str], Pattern[str], None] = None,
        timeout: Optional[int] = None,
        predicate: Optional[Callable[[Any], bool]] = None,
        on_timeout: Optional[Callable[[], Any]] = None,
    ) -> Union[GuildMessage, GroupMessage, C2CMessage, DirectMessage]:
        """
        等待用户发送匹配的消息

        这是一个异步方法，会阻塞当前协程直到收到匹配的消息。
        常用于实现多轮对话、表单填写等需要用户连续输入的场景。

        Args:
            scopes: 等待的作用域，可以是单个或多个。只有来自匹配作用域的消息才会被处理
            command: 期望的命令，支持多种类型：
                - None: 接受任何消息
                - str: 精确匹配消息内容
                - list/tuple: 匹配列表中的任意一个
                - 正则表达式: 正则匹配
            timeout: 超时时间（秒），None 表示无限等待
            predicate: 自定义过滤函数，接收消息对象返回布尔值
            on_timeout: 超时时的回调函数

        Returns:
            匹配的消息对象，类型取决于消息来源场景：
                - GuildMessage: 频道消息
                - GroupMessage: 群聊消息
                - C2CMessage: 单聊消息
                - DirectMessage: 频道私信消息

        Raises:
            WaitError: 等待任务被意外删除
            WaitTimeoutError: 等待超时

        使用示例：
            # 等待用户回复 "yes" 或 "no"
            reply = await session.wait_for(Scope.USER, ["yes", "no"], timeout=60)

            # 使用正则匹配数字
            reply = await session.wait_for(Scope.USER, re.compile(r'\\d+'), timeout=30)
        """
        return await self._manager.wait_for(
            scopes, command, timeout, predicate, on_timeout
        )


class SessionManager:
    """
    会话管理器

    核心职责：
    1. 管理不同作用域的会话数据（创建、获取、更新、删除）
    2. 处理会话超时和垃圾回收
    3. 支持 wait_for 机制实现多轮对话
    4. 持久化会话数据到文件

    线程安全说明：
    - 本类不是线程安全的，应在单个异步事件循环中使用
    - 所有会话操作都是内存操作，性能开销很小

    使用模式：
    1. 通过 bind() 绑定消息对象后使用
    2. 通过 with_session 装饰器自动绑定
    """

    def __init__(
        self,
        bot: "Bot",
        commit_path: Optional[str] = None,
        is_auto_commit: bool = True,
    ):
        """
        初始化会话管理器

        Args:
            bot: Bot 实例，用于获取日志器和 API
            commit_path: 会话数据持久化路径，默认为当前目录下的 sdk_data
            is_auto_commit: 是否在每次会话变更后自动持久化
                - True: 每次操作后自动保存，数据安全但性能略低
                - False: 需要手动调用 commit_data()，适合高频操作场景
        """
        self.__sessions: Dict = {x: {} for x in _AllScopeStr}
        self.__wait_for_registers: Dict = {}
        self.__logger = bot.logger.with_module("session")
        self.__commit_path: str = commit_path or os.path.join(os.getcwd(), "sdk_data")
        self.__check_path(self.__commit_path)
        self.__is_auto_commit = is_auto_commit
        self.__is_running = False
        self.__data_loaded = False
        self.api = None
        self._current_obj = None

    def __check_path(self, path: str):
        """检查路径是否存在，不存在则创建"""
        if not os.path.exists(path):
            os.makedirs(path)

    async def fetch_data(self):
        """
        从文件加载会话数据（异步）

        在初始化时自动调用，用于恢复之前的会话状态。
        使用 asyncio.to_thread() 将同步 I/O 操作卸载到线程池。
        如果文件不存在或加载失败，会使用空的会话字典。
        加载完成后会自动清理已过期的会话。
        """
        try:
            data_path = os.path.join(self.__commit_path, "sessions.pickle")

            def _sync_read():
                if os.path.exists(data_path):
                    with open(data_path, "rb") as f:
                        return pickle.load(f)
                return None

            data = await asyncio.to_thread(_sync_read)
            if data is not None:
                self.__sessions = data
                self.__logger.debug("加载session会话数据成功")
                await self._cleanup_expired_sessions_on_startup()
        except Exception as e:
            self.__logger.error(f"加载session会话数据失败: {e}")

    async def _cleanup_expired_sessions_on_startup(self):
        """
        启动时清理已过期的会话（异步）

        程序停机期间可能已有会话超时，需要在启动时清理，
        避免用户 get() 到本该过期的会话，或重复发送 timeout_reply。
        """
        current_time = time()
        cleaned_count = 0

        for scope, scope_sessions in self.__sessions.items():
            if scope == Scope.GLOBAL:
                keys_to_delete = []
                for key, session in scope_sessions.items():
                    if self._is_session_expired(session, current_time):
                        keys_to_delete.append(key)
                for key in keys_to_delete:
                    del scope_sessions[key]
                    cleaned_count += 1
            else:
                identify_to_delete = []
                for identify, identify_sessions in scope_sessions.items():
                    keys_to_delete = []
                    for key, session in identify_sessions.items():
                        if self._is_session_expired(session, current_time):
                            keys_to_delete.append(key)
                    for key in keys_to_delete:
                        del identify_sessions[key]
                        cleaned_count += 1
                    if not identify_sessions:
                        identify_to_delete.append(identify)
                for identify in identify_to_delete:
                    del scope_sessions[identify]

        if cleaned_count > 0:
            self.__logger.info(f"启动时清理了 {cleaned_count} 个过期会话")
            await self.commit_data(is_info=False)

    def _is_session_expired(self, session: _SessionObject, current_time: float) -> bool:
        """
        判断会话是否已过期需要清理

        会话需要清理的条件：
        1. 状态为 INACTIVE 且 gc_timeout_stamp 已过期
        2. 或者状态为 ACTIVE 但已超时，且 inactive_gc_timeout 也已过期

        Args:
            session: 会话对象
            current_time: 当前时间戳

        Returns:
            bool: 是否需要清理
        """
        if session.status == SessionStatus.INACTIVE:
            if session.gc_timeout_stamp and current_time > session.gc_timeout_stamp:
                return True
        elif session.status == SessionStatus.ACTIVE:
            timeout = (
                session.timeout
                if session.timeout is not None
                else _SessionObject.DEFAULT_TIMEOUT
            )
            elapsed = current_time - session.last_operate
            if elapsed > timeout:
                if session.inactive_gc_timeout > 0:
                    if elapsed > timeout + session.inactive_gc_timeout:
                        return True
                else:
                    return True
        return False

    async def commit_data(self, is_info: bool = True):
        """
        持久化会话数据到文件（异步）

        将当前所有会话数据序列化保存到 sessions.pickle 文件。
        使用 asyncio.to_thread() 将同步 I/O 操作卸载到线程池，避免阻塞事件循环。

        Args:
            is_info: 是否记录日志，批量操作时可设为 False 减少日志量
        """
        try:
            data_path = os.path.join(self.__commit_path, "sessions.pickle")

            def _sync_write():
                with open(data_path, "wb") as f:
                    pickle.dump(self.__sessions, f)

            await asyncio.to_thread(_sync_write)
            if is_info:
                self.__logger.debug("持久化session会话数据成功")
        except Exception as e:
            self.__logger.error(f"持久化session会话数据失败: {e}")

    def __check_identify(self, scope: str, obj) -> Hashable:
        """
        从消息对象中提取指定作用域的标识符

        不同平台和事件类型的标识符字段名不同，这里按优先级依次尝试。
        例如 QQ 频道的用户标识可能是 id、user_openid、member_openid 等。

        Args:
            scope: 作用域类型
            obj: 消息或事件对象

        Returns:
            标识符（通常是字符串 ID），如果无法提取则返回 None
        """
        if scope == Scope.USER:
            if hasattr(obj, "author") and obj.author:
                author = obj.author
                if hasattr(author, "id") and author.id:
                    return author.id
                if hasattr(author, "user_openid") and author.user_openid:
                    return author.user_openid
                if hasattr(author, "member_openid") and author.member_openid:
                    return author.member_openid
                if hasattr(author, "union_openid") and author.union_openid:
                    return author.union_openid
                if hasattr(author, "union_user_account") and author.union_user_account:
                    return author.union_user_account

            if hasattr(obj, "user_openid") and obj.user_openid:
                return obj.user_openid
            if hasattr(obj, "group_member_openid") and obj.group_member_openid:
                return obj.group_member_openid
        elif scope == Scope.GUILD:
            if hasattr(obj, "guild_id") and obj.guild_id:
                return obj.guild_id
        elif scope == Scope.CHANNEL:
            if hasattr(obj, "channel_id") and obj.channel_id:
                return obj.channel_id
        elif scope == Scope.GROUP:
            if hasattr(obj, "group_openid") and obj.group_openid:
                return obj.group_openid

        return None

    def __valid_scope(self, scope: str) -> str:
        """验证作用域是否有效，无效时抛出 ValueError"""
        if scope not in _AllScopeStr:
            raise ValueError(f"无效的作用域: {scope}")
        return scope

    def __check_scope(self, scope: str) -> Dict:
        """获取指定作用域的会话字典，如果不存在则创建空字典"""
        if scope not in self.__sessions:
            self.__sessions[scope] = {}
        return self.__sessions[scope]

    async def __update_last_op(self, session: _SessionObject):
        """
        更新会话的最后操作时间

        每次对会话进行读写操作时都应调用此方法，
        以确保超时计时器能正确重置。
        """
        session.last_operate = time()
        if self.__is_auto_commit:
            await self.commit_data(is_info=False)

    def __get_reply_params(self, obj) -> Dict:
        """
        从消息对象中提取超时回复所需的参数

        超时回复需要知道往哪里发消息，这些信息从原始消息对象中提取。
        不同场景使用不同的 API：
        - 频道消息: send_guild_message
        - 私信: send_direct_message
        - 群聊: send_group_message
        - C2C: send_c2c_message

        msg_id 有 5 分钟的有效期，超时后需要移除该参数，
        否则 API 调用会失败。
        """
        timeout_reply_api = None
        timeout_reply_params = {}

        try:

            if hasattr(obj, "id"):
                timeout_reply_params["msg_id"] = obj.id
            elif hasattr(obj, "event_id"):
                timeout_reply_params["event_id"] = obj.event_id

            if hasattr(obj, "channel_id"):
                timeout_reply_params["channel_id"] = obj.channel_id
                timeout_reply_api = "send_guild_message"
            elif hasattr(obj, "guild_id"):
                timeout_reply_params["guild_id"] = obj.guild_id
                timeout_reply_api = "send_direct_message"
            elif hasattr(obj, "group_openid"):
                timeout_reply_params["group_openid"] = obj.group_openid
                timeout_reply_api = "send_group_message"
            elif hasattr(obj, "author") and hasattr(obj.author, "id"):
                timeout_reply_params["openid"] = obj.author.id
                timeout_reply_api = "send_c2c_message"
        except Exception as e:
            self.__logger.error(f"获取回复参数时出现错误：{e}")

        return {
            "timeout_reply_api": timeout_reply_api,
            "timeout_reply_params": timeout_reply_params,
            "timeout_reply_message_id_expire": time() + 300,
        }

    def set_api(self, api):
        """设置 API 实例，用于发送超时回复"""
        self.api = api

    async def __check_session_timeouts(self):
        """
        检查所有会话的超时状态

        遍历所有作用域的所有会话，检查是否超时。
        使用 yield_threshold 机制定期让出事件循环，
        避免在会话数量很大时阻塞其他协程。
        """
        current_time = time()
        processed_count = 0
        yield_threshold = 100

        for scope, scope_sessions in self.__sessions.items():
            if scope == Scope.GLOBAL:
                for key, session in scope_sessions.items():
                    self.__handle_session_timeout(session)
                    processed_count += 1
                    if processed_count % yield_threshold == 0:
                        await sleep(0)
            else:
                for identify, identify_sessions in scope_sessions.items():
                    for key, session in identify_sessions.items():
                        self.__handle_session_timeout(session)
                        processed_count += 1
                        if processed_count % yield_threshold == 0:
                            await sleep(0)

    def __handle_session_timeout(self, session: _SessionObject):
        """
        处理单个会话的超时逻辑

        当会话超时时：
        1. 如果设置了 timeout_reply，发送超时提示消息
        2. 将会话状态改为 INACTIVE
        3. 设置 gc_timeout_stamp，等待 GC 清理

        注意：msg_id 有 5 分钟有效期，超时后根据 send_reply_on_msg_id_expired
        参数决定是否仍发送消息。
        """
        current_time = time()

        if session.status == SessionStatus.ACTIVE and session.timeout:
            if current_time - session.last_operate > session.timeout:
                if session.timeout_reply and session.timeout_reply_api and self.api:
                    try:
                        msg_id_expired = (
                            session.timeout_reply_message_id_expire
                            and time() > session.timeout_reply_message_id_expire
                        )

                        if msg_id_expired:
                            if session.send_reply_on_msg_id_expired:
                                if "msg_id" in session.timeout_reply_params:
                                    del session.timeout_reply_params["msg_id"]
                                    self.__logger.warning(
                                        "msg_id 已过期（超过5分钟），超时回复将以主动消息形式发送（消耗主动消息配额）"
                                    )
                            else:
                                self.__logger.warning(
                                    "msg_id 已过期（超过5分钟），且 send_reply_on_msg_id_expired=False，"
                                    "跳过发送超时回复以避免消耗主动消息配额"
                                )
                                return

                        if isinstance(session.timeout_reply, str):
                            params = {
                                "content": session.timeout_reply,
                                **session.timeout_reply_params,
                            }
                        else:
                            api_model_data = session.timeout_reply.build()
                            params = {**api_model_data, **session.timeout_reply_params}

                        api_method = getattr(self.api, session.timeout_reply_api, None)
                        if api_method:
                            import asyncio

                            asyncio.create_task(api_method(**params))
                    except Exception as e:
                        self.__logger.error(f"发送超时回复时出现错误：{e}")

                if session.inactive_gc_timeout > 0:
                    session.status = SessionStatus.INACTIVE
                    session.gc_timeout_stamp = time() + session.inactive_gc_timeout
                else:
                    session.status = SessionStatus.INACTIVE
                    session.gc_timeout_stamp = time()

    def start(self, loop: AbstractEventLoop):
        """
        启动会话管理器的后台任务

        在 Bot 启动时调用，创建会话管理循环协程。
        该循环负责定期检查超时和执行垃圾回收。
        同时在启动时异步加载持久化的会话数据。
        """
        if not self.__is_running:
            loop.create_task(self.__manager_loop(loop))
            if not self.__data_loaded:
                loop.create_task(self.fetch_data())
                self.__data_loaded = True
            self.__is_running = True

    async def __manager_loop(self, loop: AbstractEventLoop):
        """
        会话管理主循环

        执行两个周期性任务：
        1. 每 5 秒检查一次会话超时
        2. 每 30 秒执行一次垃圾回收

        这个循环会一直运行，直到程序退出。
        """
        gc_counter = 0
        while True:
            await sleep(5)
            await self.__check_session_timeouts()
            gc_counter += 1
            if gc_counter >= 6:
                await self.__gc_sessions()
                gc_counter = 0

    async def __gc_sessions(self):
        """
        垃圾回收：清理已过期的 INACTIVE 会话

        只删除同时满足以下条件的会话：
        1. 状态为 INACTIVE
        2. gc_timeout_stamp 已过期

        使用 yield_threshold 机制避免阻塞事件循环。
        清理完成后如果 is_auto_commit=True 会自动持久化。
        """
        current_time = time()
        processed_count = 0
        deleted_count = 0
        yield_threshold = 100

        for scope, scope_sessions in self.__sessions.items():
            if scope == Scope.GLOBAL:
                keys_to_delete = []
                for key, session in scope_sessions.items():
                    if session.status == SessionStatus.INACTIVE:
                        if (
                            session.gc_timeout_stamp
                            and current_time > session.gc_timeout_stamp
                        ):
                            keys_to_delete.append(key)
                    processed_count += 1
                    if processed_count % yield_threshold == 0:
                        await sleep(0)
                for key in keys_to_delete:
                    del scope_sessions[key]
                    deleted_count += 1
            else:
                identify_to_delete = []
                for identify, identify_sessions in scope_sessions.items():
                    keys_to_delete = []
                    for key, session in identify_sessions.items():
                        if session.status == SessionStatus.INACTIVE:
                            if (
                                session.gc_timeout_stamp
                                and current_time > session.gc_timeout_stamp
                            ):
                                keys_to_delete.append(key)
                        processed_count += 1
                        if processed_count % yield_threshold == 0:
                            await sleep(0)
                    for key in keys_to_delete:
                        del identify_sessions[key]
                        deleted_count += 1
                    if not identify_sessions:
                        identify_to_delete.append(identify)
                for identify in identify_to_delete:
                    del scope_sessions[identify]

        if deleted_count > 0:
            self.__logger.debug(f"GC清理完成：删除了 {deleted_count} 个过期会话")

        if self.__is_auto_commit:
            await self.commit_data(is_info=False)

    # -*- 会话管理方法（内部实现） -*-

    async def _new(
        self,
        obj,
        scope: str,
        key: Hashable,
        data: Dict | None = None,
        identify: Hashable | None = None,
        is_replace: bool = True,
        timeout: Optional[float] = None,
        timeout_reply: Optional[
            Union[
                str,
                MessagesModel.Message,
                MessagesModel.MessageEmbed,
                MessagesModel.MessageArk23,
                MessagesModel.MessageArk24,
                MessagesModel.MessageArk37,
                MessagesModel.MessageMarkdown,
            ]
        ] = None,
        inactive_gc_timeout: Optional[float] = 0,
        send_reply_on_msg_id_expired: bool = False,
    ) -> SessionObject:
        """
        创建新会话

        Args:
            obj: 消息对象
            scope: 作用域
            key: 会话键
            data: 会话数据
            identify: 标识
            is_replace: 是否替换现有会话
            timeout: 超时时间（秒），默认 1800 秒（30 分钟）
            timeout_reply: 超时回复
            inactive_gc_timeout: 非活动会话回收时间
            send_reply_on_msg_id_expired: msg_id 过期后是否仍发送消息

        Returns:
            SessionObject: 会话对象
        """
        if not identify:
            identify = self.__check_identify(scope, obj)
        scope = self.__valid_scope(scope)
        target_sessions = self.__check_scope(scope)

        if identify:
            if identify not in target_sessions:
                target_sessions[identify] = {}
            target_sessions = target_sessions[identify]

        if key in target_sessions and not is_replace:
            if identify:
                raise KeyError(f"Scope {scope} 中已存在 {identify}::{key} 的session")
            else:
                raise KeyError(f"Scope {scope} 中已存在 {key} 的session")

        reply_params = self.__get_reply_params(obj)

        actual_timeout = (
            timeout if timeout is not None else _SessionObject.DEFAULT_TIMEOUT
        )

        target_sessions[key] = _SessionObject(
            status=SessionStatus.ACTIVE,
            data=data if data is not None else {},
            timeout=actual_timeout,
            last_operate=time(),
            timeout_reply=timeout_reply,
            inactive_gc_timeout=inactive_gc_timeout,
            gc_timeout_stamp=(
                time() + inactive_gc_timeout if inactive_gc_timeout > 0 else None
            ),
            send_reply_on_msg_id_expired=send_reply_on_msg_id_expired,
            **reply_params,
        )

        if self.__is_auto_commit:
            await self.commit_data(is_info=False)

        return SessionObject(scope, SessionStatus.ACTIVE, key, data, identify)

    async def _get(
        self,
        obj,
        scope: str,
        key: Hashable,
        identify: Hashable = None,
        default=None,
        skip_update_last_op: bool = False,
    ) -> SessionObject:
        """
        获取会话

        Args:
            obj: 消息对象
            scope: 作用域
            key: 会话键
            identify: 标识
            default: 默认值
            skip_update_last_op: 是否跳过更新最后操作时间（默认 False，会重置超时计时器）

        Returns:
            SessionObject: 会话对象或默认值
        """
        if not identify:
            identify = self.__check_identify(scope, obj)
        scope = self.__valid_scope(scope)
        target_sessions = self.__check_scope(scope)

        if identify:
            if identify not in target_sessions or key not in target_sessions[identify]:
                return default
            target_session = target_sessions[identify][key]
        else:
            if key not in target_sessions:
                return default
            target_session = target_sessions[key]

        if target_session.status == SessionStatus.INACTIVE:
            return default

        if not skip_update_last_op:
            await self.__update_last_op(target_session)

        return SessionObject(
            scope, target_session.status, key, target_session.data, identify
        )

    async def _update(
        self,
        obj,
        scope: str,
        key: Hashable,
        data: Dict,
        identify: Hashable = None,
    ) -> SessionObject:
        """
        更新会话

        Args:
            obj: 消息对象
            scope: 作用域
            key: 会话键
            data: 会话数据
            identify: 标识

        Returns:
            SessionObject: 会话对象
        """
        if not identify:
            identify = self.__check_identify(scope, obj)
        scope = self.__valid_scope(scope)
        target_sessions = self.__check_scope(scope)

        if identify:
            if identify not in target_sessions or key not in target_sessions[identify]:
                raise KeyError(f"Scope {scope} 中不存在 {identify}::{key} 的session")
            target_sessions = target_sessions[identify]
        else:
            if key not in target_sessions:
                raise KeyError(f"Scope {scope} 中不存在 {key} 的session")

        target_session = target_sessions[key]
        target_session.data.update(data)
        await self.__update_last_op(target_session)

        return SessionObject(
            scope, target_session.status, key, target_session.data, identify
        )

    def register_wait_for(
        self, obj: Any, scopes: Union[str, Sequence[str]], command: Any
    ) -> ScopeRegisterKey:
        """
        注册一个 wait_for 等待任务

        当收到匹配的消息时，会触发对应的 wait_for 返回。
        scope_key 是一个包含所有作用域标识符的命名元组，
        用于精确匹配来自特定用户/频道/群的消息。

        Args:
            obj: 消息对象，用于提取作用域标识符
            scopes: 等待的作用域，可以是单个或多个
            command: 命令对象，用于匹配消息内容

        Returns:
            ScopeRegisterKey: 作用域键，用于后续检查和删除
        """
        _scope_value = {x: None for x in _AllScopeStr}
        if isinstance(scopes, ABCSequence) and not isinstance(scopes, str):
            for scope in scopes:
                _scope_value[scope] = self.__check_identify(scope, obj)
        else:
            _scope_value[scopes] = self.__check_identify(scopes, obj)

        scope_key = ScopeRegisterKey(**_scope_value)
        if scope_key not in self.__wait_for_registers:
            self.__wait_for_registers[scope_key] = {}
        self.__wait_for_registers[scope_key][command] = None
        return scope_key

    def check_wait_for(
        self, scope_key: ScopeRegisterKey, command: Any
    ) -> tuple[bool, Any]:
        """
        检查 wait_for 任务是否有结果

        如果消息已到达，result 会是非 None 的消息对象。
        获取结果后会自动清理注册信息。

        Args:
            scope_key: 注册时返回的作用域键
            command: 注册的命令对象

        Returns:
            Tuple[bool, Any]: (注册是否存在, 结果数据)
                - (False, None): 注册已被删除
                - (True, None): 注册存在但还没收到消息
                - (True, data): 收到了消息，data 是消息对象
        """
        if (
            scope_key not in self.__wait_for_registers
            or command not in self.__wait_for_registers[scope_key]
        ):
            return False, None
        data = self.__wait_for_registers[scope_key][command]
        if data:
            del self.__wait_for_registers[scope_key][command]
            if not self.__wait_for_registers[scope_key]:
                del self.__wait_for_registers[scope_key]
        return True, data

    def del_wait_for(self, scope_key: ScopeRegisterKey, command: Any) -> None:
        """
        删除 wait_for 注册

        用于取消等待或超时后清理。删除后对应的 wait_for 会抛出 WaitError。

        Args:
            scope_key: 注册时返回的作用域键
            command: 注册的命令对象
        """
        if scope_key not in self.__wait_for_registers:
            return
        if command in self.__wait_for_registers[scope_key]:
            del self.__wait_for_registers[scope_key][command]
        if not self.__wait_for_registers[scope_key]:
            del self.__wait_for_registers[scope_key]

    async def wait_for(
        self,
        scopes: Union[str, Sequence[str]],
        command: Union[str, Sequence[str], Pattern[str], None] = None,
        timeout: Optional[int] = None,
        predicate: Optional[Callable[[Any], bool]] = None,
        on_timeout: Optional[Callable[[], Any]] = None,
    ) -> Union[GuildMessage, GroupMessage, C2CMessage, DirectMessage]:
        """
        等待指定的命令被触发

        这是一个阻塞式异步方法，会持续轮询直到收到匹配的消息或超时。
        轮询间隔为 0.5 秒，在大多数场景下响应足够及时。

        Args:
            scopes: 作用域或作用域列表，只有来自匹配作用域的消息才会被处理
            command: 命令匹配规则，支持多种类型：
                - None: 接受任何消息
                - str: 精确匹配消息内容
                - list/tuple: 匹配列表中的任意一个
                - 正则表达式: 正则匹配
            timeout: 超时时间（秒），None 表示无限等待
            predicate: 自定义过滤函数，接收消息对象返回布尔值，
                可以实现更复杂的匹配逻辑
            on_timeout: 超时回调函数，在抛出异常前调用

        Returns:
            匹配的消息对象，类型取决于消息来源场景：
                - GuildMessage: 频道消息
                - GroupMessage: 群聊消息
                - C2CMessage: 单聊消息
                - DirectMessage: 频道私信消息

        Raises:
            ValueError: 未绑定消息对象
            WaitError: 等待任务被意外删除
            WaitTimeoutError: 等待超时
        """

        if self._current_obj is None:
            raise ValueError("请先使用 with session.bind(obj) 绑定消息对象")

        if command is None:
            command_obj = BotCommandObject(valid_scenes=CommandValidScenes.ALL)
        elif isinstance(command, (str, list, tuple)):
            command_obj = BotCommandObject(
                command=command, valid_scenes=CommandValidScenes.ALL
            )
        elif hasattr(command, "pattern"):
            command_obj = BotCommandObject(
                regex=[command], valid_scenes=CommandValidScenes.ALL
            )
        else:
            command_obj = command

        if predicate is not None:
            setattr(command_obj, "_predicate", predicate)

        scope_key = self.register_wait_for(self._current_obj, scopes, command_obj)
        _timeout_stamp = time() + timeout if timeout else None

        while True:
            check, result = self.check_wait_for(scope_key, command_obj)
            if not check:
                self.del_wait_for(scope_key, command_obj)
                raise WaitError("找不到对应的wait_for()等待任务")
            if result is not None:
                break
            if _timeout_stamp and time() > _timeout_stamp:
                self.del_wait_for(scope_key, command_obj)
                if on_timeout is not None:
                    on_timeout()
                raise WaitTimeoutError(f"wait_for()等待超时： {command_obj}")
            await sleep(0.5)
        return result

    # -*- 公共 API（上下文管理器和装饰器支持） -*-

    @contextmanager
    def bind(self, obj):
        """
        绑定消息对象的上下文管理器

        这是使用 SessionManager 的推荐方式。绑定后，所有会话操作
        都会自动从绑定的消息对象中提取 identify，无需手动传入。

        注意：所有修改操作都是异步方法，需要在异步上下文中调用。

        使用示例：
            with session.bind(msg) as s:
                await s.new(Scope.USER, "key", {"data": "value"})
                data = await s.get(Scope.USER, "key")

        Args:
            obj: 消息或事件对象

        Yields:
            BoundSession: 绑定了消息对象的会话操作器
        """
        old_obj = self._current_obj
        self._current_obj = obj
        try:
            yield BoundSession(self, obj)
        finally:
            self._current_obj = old_obj

    async def new(
        self,
        scope: str,
        key: Hashable,
        data: Dict | None = None,
        identify: Hashable = None,
        is_replace: bool = True,
        timeout: Optional[float] = None,
        timeout_reply: Optional[
            Union[
                str,
                MessagesModel.Message,
                MessagesModel.MessageEmbed,
                MessagesModel.MessageArk23,
                MessagesModel.MessageArk24,
                MessagesModel.MessageArk37,
                MessagesModel.MessageMarkdown,
            ]
        ] = None,
        inactive_gc_timeout: Optional[float] = 0,
        send_reply_on_msg_id_expired: bool = False,
    ) -> SessionObject:
        """
        创建新会话

        Args:
            scope: 作用域
            key: 会话键
            data: 会话数据
            identify: 标识
            is_replace: 是否替换现有会话
            timeout: 超时时间（秒），默认 1800 秒（30 分钟）
            timeout_reply: 超时回复
            inactive_gc_timeout: 非活动会话回收时间
            send_reply_on_msg_id_expired: msg_id 过期后是否仍发送消息

        Returns:
            SessionObject: 会话对象
        """
        if self._current_obj is None:
            raise ValueError("请先使用 with session.bind(obj) 绑定消息对象")
        return await self._new(
            self._current_obj,
            scope,
            key,
            data,
            identify,
            is_replace,
            timeout,
            timeout_reply,
            inactive_gc_timeout,
            send_reply_on_msg_id_expired,
        )

    async def get(
        self,
        scope: str,
        key: Hashable,
        identify: Hashable = None,
        default=None,
        skip_update_last_op: bool = False,
    ) -> SessionObject:
        """
        获取会话

        Args:
            scope: 作用域
            key: 会话键
            identify: 标识
            default: 默认值
            skip_update_last_op: 是否跳过更新最后操作时间（默认 False，会重置超时计时器）

        Returns:
            SessionObject: 会话对象或默认值
        """
        if self._current_obj is None:
            return default
        return await self._get(
            self._current_obj, scope, key, identify, default, skip_update_last_op
        )

    async def update(
        self,
        scope: str,
        key: Hashable,
        data: Dict,
        identify: Hashable = None,
    ) -> SessionObject:
        """
        更新会话

        Args:
            scope: 作用域
            key: 会话键
            data: 会话数据
            identify: 标识

        Returns:
            SessionObject: 会话对象
        """
        if self._current_obj is None:
            raise ValueError("请先使用 with session.bind(obj) 绑定消息对象")
        return await self._update(self._current_obj, scope, key, data, identify)

    async def remove(
        self,
        scope: str = None,
        identify: Hashable = None,
        key: Hashable = None,
    ):
        """
        删除会话

        Args:
            scope: 作用域
            identify: 标识
            key: 会话键
        """
        if not scope:
            self.__sessions = {x: {} for x in _AllScopeStr}
            return

        if identify is None and self._current_obj is not None:
            identify = self.__check_identify(scope, self._current_obj)

        scope = self.__valid_scope(scope)
        target_sessions = self.__check_scope(scope)

        if not key and not identify:
            target_sessions.clear()
            if self.__is_auto_commit:
                await self.commit_data(is_info=False)
            return

        if not key and identify:
            if identify in target_sessions:
                target_sessions[identify] = {}
                if self.__is_auto_commit:
                    await self.commit_data(is_info=False)
            return

        if identify:
            if identify not in target_sessions or key not in target_sessions[identify]:
                raise KeyError(f"Scope {scope} 中不存在 {identify}::{key} 的session")
            target_sessions = target_sessions[identify]
        else:
            if key not in target_sessions:
                raise KeyError(f"Scope {scope} 中不存在 {key} 的session")

        target_sessions.pop(key)
        if self.__is_auto_commit:
            await self.commit_data(is_info=False)

    def wait_for_message_checker(
        self, obj: Union[GuildMessage, GroupMessage, C2CMessage, DirectMessage]
    ) -> List[WaitForCommandCallback]:
        """
        检查收到的消息是否匹配任何 wait_for 注册

        这个方法由消息处理器调用，用于检测是否有等待中的 wait_for
        需要被触发。匹配逻辑是：
        1. 消息的作用域标识符必须与注册时的 scope_key 中任意一个匹配
        2. scope_key 中为 None 的作用域表示不限制
        3. 多个 scope 是 OR 关系，只要匹配任意一个即可

        Args:
            obj: 收到的消息对象

        Returns:
            List[WaitForCommandCallback]: 所有匹配的回调列表
                每个回调包含 command、callback 函数和可选的 predicate
        """
        triggered_commands = []
        _scope_value = {
            scope: self.__check_identify(scope, obj) for scope in _AllScopeStr
        }

        for scope_key, command_callback in self.__wait_for_registers.items():
            has_any_scope = False
            matched = False
            for scope in _AllScopeStr:
                scope_key_value = getattr(scope_key, scope)
                if scope_key_value is not None:
                    has_any_scope = True
                    if scope_key_value == _scope_value[scope]:
                        matched = True
                        break

            if not has_any_scope or matched:
                for command in command_callback:
                    predicate = getattr(command, "_predicate", None)
                    triggered_commands.append(
                        WaitForCommandCallback(
                            command=command,
                            callback=lambda data, cmd=command, cbs=command_callback: cbs.__setitem__(
                                cmd, data
                            ),
                            predicate=predicate,
                        )
                    )
        return triggered_commands

    def clear_wait_for(self, scope: str = None, identify: Hashable = None):
        """
        清除 wait_for 注册

        用于强制取消等待，比如用户主动取消操作时。
        清除后对应的 wait_for 会抛出 WaitError。

        Args:
            scope: 作用域，None 表示清除所有
            identify: 标识符，与 scope 配合使用
        """
        if not scope:
            self.__wait_for_registers.clear()
            return

        _scope_value = {s: None for s in _AllScopeStr}
        _scope_value[scope] = identify

        scope_key = ScopeRegisterKey(**_scope_value)

        if scope_key in self.__wait_for_registers:
            del self.__wait_for_registers[scope_key]


def with_session(func):
    """
    装饰器：自动为事件处理函数注入绑定了消息对象的 session

    这个装饰器简化了 session 的使用，无需手动使用 with session.bind()。
    它会检查 kwargs 中是否有 "session" 参数（由框架传入的 SessionManager），
    如果有则绑定消息对象后注入 BoundSession。

    使用示例：
        @bot.on_guild_message
        @with_session
        async def handle_message(msg, session=None):
            # session 已经绑定到 msg，可以直接使用（需要 await）
            await session.new(Scope.USER, "key", {"data": "value"})
            data = await session.get(Scope.USER, "key")

    注意：
        - 装饰器必须在 @bot.on_xxx 之后（先注册事件，再注入 session）
        - 函数签名必须包含 session=None 参数
        - 所有 session 操作都是异步的，需要使用 await
    """

    @wraps(func)
    async def wrapper(msg, *args, **kwargs):
        if "session" in kwargs:
            session_manager = kwargs.pop("session")
            with session_manager.bind(msg) as bound_session:
                kwargs["session"] = bound_session
                return await func(msg, *args, **kwargs)
        return await func(msg, *args, **kwargs)

    return wrapper
