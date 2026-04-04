#!/usr/bin/env python3
"""
EasyBot SDK API 模块

提供所有官方 API 的封装，包括：
- 频道相关 API
- 子频道相关 API
- 消息相关 API
- 群聊相关 API
- 私信相关 API
- 成员管理 API
- 身份组管理 API
- 权限管理 API
- 其他 API
"""

import base64
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Union

import aiohttp

from ._internal import HTTPClient
from .messages_model import MessagesModel
from .models import Model

if TYPE_CHECKING:
    from .bot import Bot

MessageContent = Union[
    str,
    MessagesModel.Message,
    MessagesModel.MessageEmbed,
    MessagesModel.MessageArk23,
    MessagesModel.MessageArk24,
    MessagesModel.MessageArk37,
    MessagesModel.MessageMarkdown,
]


class API:
    """
    API 调用封装类

    所有 API 方法都支持自动重试和错误日志。
    返回值均为对应的响应模型对象，方便开发者使用。
    """

    def __init__(self, bot: "Bot"):
        """
        初始化 API

        Args:
            bot: Bot 实例
        """
        self._bot = bot
        self._http = None
        self._logger = bot.logger.with_module("api")

    async def _get_http(self) -> HTTPClient:
        """获取 HTTP 客户端"""
        if self._http is None:
            self._http = HTTPClient(self._bot)
            self._logger.debug("HTTP 客户端已创建")
        return self._http

    async def close(self) -> None:
        """关闭 HTTP 客户端"""
        if self._http:
            await self._http.close()
            self._logger.debug("HTTP 客户端已关闭")

    async def get_guild(self, guild_id: str) -> Model.Guild:
        """
        获取频道详情

        Args:
            guild_id: 频道 ID

        Returns:
            Model.Guild: 频道对象
        """
        http = await self._get_http()
        data = await http.get(f"/guilds/{guild_id}")
        return Model.Guild.from_dict(data)

    async def get_guild_list(
        self,
        before: str | None = None,
        after: str | None = None,
        limit: int = 100,
    ) -> list[Model.Guild]:
        """
        获取机器人所在频道列表

        Args:
            before: 读此 guild id 之前的数据
            after: 读此 guild id 之后的数据
            limit: 每次拉取数量，默认 100，最大 100

        Returns:
            list[Model.Guild]: 频道对象列表
        """
        http = await self._get_http()
        params = {"limit": limit}
        if before:
            params["before"] = before
        if after:
            params["after"] = after
        data = await http.get("/users/@me/guilds", params=params)
        return [Model.Guild.from_dict(g) for g in data]

    async def get_guild_channels(self, guild_id: str) -> list[Model.Channel]:
        """
        获取频道子频道列表

        Args:
            guild_id: 频道 ID

        Returns:
            list[Model.Channel]: 子频道对象列表
        """
        http = await self._get_http()
        data = await http.get(f"/guilds/{guild_id}/channels")
        return [Model.Channel.from_dict(c) for c in data]

    async def get_me(self) -> Model.Author:
        """
        获取当前用户（机器人）信息

        Returns:
            Model.Author: 用户对象
        """
        http = await self._get_http()
        data = await http.get("/users/@me")
        return Model.Author.from_dict(data)

    async def get_channel(self, channel_id: str) -> Model.Channel:
        """
        获取子频道详情

        Args:
            channel_id: 子频道 ID

        Returns:
            Model.Channel: 子频道对象
        """
        http = await self._get_http()
        data = await http.get(f"/channels/{channel_id}")
        return Model.Channel.from_dict(data)

    async def create_channel(
        self,
        guild_id: str,
        name: str,
        channel_type: int,
        position: int,
        parent_id: str | None = None,
        sub_type: int = 0,
        private_type: int = 0,
        private_user_ids: list[str] | None = None,
        speak_permission: int = 0,
        application_id: str | None = None,
    ) -> Model.Channel:
        """
        创建子频道

        Args:
            guild_id: 频道 ID
            name: 子频道名称
            channel_type: 子频道类型
            position: 排序值
            parent_id: 所属分组 ID
            sub_type: 子频道子类型
            private_type: 子频道私密类型
            private_user_ids: 子频道私密成员 ID 列表
            speak_permission: 子频道发言权限
            application_id: 应用类型子频道 AppID

        Returns:
            Model.Channel: 创建的子频道对象
        """
        http = await self._get_http()
        payload = {
            "name": name,
            "type": channel_type,
            "position": position,
            "sub_type": sub_type,
            "private_type": private_type,
            "speak_permission": speak_permission,
        }
        if parent_id:
            payload["parent_id"] = parent_id
        if private_user_ids:
            payload["private_user_ids"] = private_user_ids
        if application_id:
            payload["application_id"] = application_id
        data = await http.post(f"/guilds/{guild_id}/channels", json=payload)
        return Model.Channel.from_dict(data)

    async def update_channel(
        self,
        channel_id: str,
        name: str | None = None,
        position: int | None = None,
        parent_id: str | None = None,
        private_type: int | None = None,
        speak_permission: int | None = None,
    ) -> Model.Channel:
        """
        修改子频道

        Args:
            channel_id: 子频道 ID
            name: 子频道名称
            position: 排序值
            parent_id: 所属分组 ID
            private_type: 子频道私密类型
            speak_permission: 子频道发言权限

        Returns:
            Model.Channel: 修改后的子频道对象
        """
        http = await self._get_http()
        payload = {}
        if name is not None:
            payload["name"] = name
        if position is not None:
            payload["position"] = position
        if parent_id is not None:
            payload["parent_id"] = parent_id
        if private_type is not None:
            payload["private_type"] = private_type
        if speak_permission is not None:
            payload["speak_permission"] = speak_permission
        data = await http.patch(f"/channels/{channel_id}", json=payload)
        return Model.Channel.from_dict(data)

    async def delete_channel(self, channel_id: str) -> bool:
        """
        删除子频道

        Args:
            channel_id: 子频道 ID

        Returns:
            bool: 是否删除成功
        """
        http = await self._get_http()
        await http.delete(f"/channels/{channel_id}")
        return True

    async def _send_message(
        self,
        endpoint: str,
        content: MessageContent | None = None,
        image: str | None = None,
        file_image: bytes | str | None = None,
        msg_id: str | None = None,
        event_id: str | None = None,
        msg_type: str | None = None,
        msg_seq: int | None = None,
        response_model: type = Model.GuildMessage,
        require_content: bool = False,
        **kwargs,
    ) -> Any:
        """
        通用消息发送方法

        Args:
            endpoint: API 端点
            content: 消息内容，可以是文本或消息对象
            image: 图片 URL（当 content 为文本时使用）
            file_image: 图片数据，支持 bytes 或文件路径（当 content 为文本时使用）
            msg_id: 要回复的消息 ID（被动消息）
            event_id: 要回复的事件 ID（被动消息）
            msg_type: 消息类型（群聊/单聊需要）
            msg_seq: 回复消息的序号（群聊/单聊需要）
            response_model: 响应模型类
            require_content: 是否要求必须有文本内容（群聊需要）
            **kwargs: 其他参数

        Returns:
            响应模型实例
        """
        http = await self._get_http()

        if isinstance(content, str) or content is None:
            if content is None and image is None and file_image is None:
                raise ValueError("content、image 和 file_image 至少需要提供一个")
            if content is not None:
                content = MessagesModel.Message(
                    content=content, image=image, file_image=file_image
                )
            else:
                content = MessagesModel.Message(image=image, file_image=file_image)

        payload = content.build()

        if require_content and not payload.get("content"):
            raise ValueError(
                "群聊消息必须有文本内容(content)，纯图片/富媒体请配合文本使用"
            )

        # 添加通用参数
        if msg_id:
            payload["msg_id"] = msg_id
        if event_id:
            payload["event_id"] = event_id
        if msg_type:
            payload["msg_type"] = msg_type
        if msg_seq is not None:
            payload["msg_seq"] = msg_seq

        # 添加额外参数
        payload.update(kwargs)

        self._logger.debug(
            f"发送消息: endpoint={endpoint}, type={type(content).__name__}"
        )

        if "file_image" in payload:
            file_data = payload.pop("file_image")
            data = aiohttp.FormData()
            for key, value in payload.items():
                if value is not None:
                    if isinstance(value, dict):
                        data.add_field(key, json.dumps(value))
                    else:
                        data.add_field(key, str(value))
            data.add_field("file_image", file_data, filename="image.png")
            result = await http.post(endpoint, data=data)
        else:
            result = await http.post(endpoint, json=payload)

        response = response_model.from_dict(result)
        self._logger.debug(
            f"消息已发送: endpoint={endpoint}, msg_id={getattr(response, 'id', 'unknown')}"
        )
        return response

    async def send_guild_message(
        self,
        channel_id: str,
        content: MessageContent | None = None,
        image: str | None = None,
        file_image: bytes | str | None = None,
        msg_id: str | None = None,
        event_id: str | None = None,
    ) -> Model.GuildMessage:
        """
        发送频道消息

        支持两种方式：
        1. 传入消息对象：content=MessagesModel.MessageEmbed(title="标题", content=["行1"])
        2. 传入文本和参数：content="文本", image="https://..."

        Args:
            channel_id: 子频道 ID
            content: 消息内容，可以是文本或消息对象
                      - str: 文本消息
                      - MessagesModel.Message: 普通消息
                      - MessagesModel.MessageEmbed: Embed 消息
                      - MessagesModel.MessageArk23/24/37: Ark 模板消息
                      - MessagesModel.MessageMarkdown: Markdown 消息
            image: 图片 URL（当 content 为文本时使用）
            file_image: 图片数据，支持 bytes 或文件路径（当 content 为文本时使用）
            msg_id: 要回复的消息 ID（被动消息）
            event_id: 要回复的事件 ID（被动消息）

        Returns:
            Model.GuildMessage: 发送的消息对象

        使用示例：
            # 方式一：消息对象
            await api.send_guild_message(channel_id, MessagesModel.Message(content="Hello"))
            await api.send_guild_message(channel_id, MessagesModel.MessageEmbed(title="标题"))
            await api.send_guild_message(channel_id, MessagesModel.MessageMarkdown(content="# 标题"))

            # 方式二：文本+参数
            await api.send_guild_message(channel_id, "Hello")
            await api.send_guild_message(channel_id, "图片", image="https://...")
            await api.send_guild_message(channel_id, "图片", file_image="./image.png")
        """
        endpoint = f"/channels/{channel_id}/messages"
        return await self._send_message(
            endpoint,
            content=content,
            image=image,
            file_image=file_image,
            msg_id=msg_id,
            event_id=event_id,
            response_model=Model.GuildMessage,
        )

    async def get_guild_message(
        self,
        channel_id: str,
        message_id: str,
    ) -> Model.GuildMessage:
        """
        获取指定消息

        Args:
            channel_id: 子频道 ID
            message_id: 消息 ID

        Returns:
            Model.GuildMessage: 消息对象
        """
        http = await self._get_http()
        data = await http.get(f"/channels/{channel_id}/messages/{message_id}")
        return Model.GuildMessage.from_dict(data)

    async def recall_guild_message(
        self,
        channel_id: str,
        message_id: str,
        hidetip: bool = False,
    ) -> bool:
        """
        撤回频道消息

        Args:
            channel_id: 子频道 ID
            message_id: 消息 ID
            hidetip: 是否隐藏提示小灰条

        Returns:
            bool: 是否撤回成功
        """
        http = await self._get_http()
        endpoint = f"/channels/{channel_id}/messages/{message_id}"
        params = {"hidetip": str(hidetip).lower()}
        await http.delete(endpoint, params=params)
        return True

    async def patch_guild_message(
        self,
        channel_id: str,
        patch_msg_id: str,
        content: MessageContent | None = None,
        msg_id: str | None = None,
        event_id: str | None = None,
    ) -> Model.GuildMessage:
        """
        修改频道 markdown 消息

        需要先申请权限才能使用此接口。
        仅支持修改 Markdown 和 Keyboard 内容（与 MessageMarkdown 对象天然匹配）。

        Args:
            channel_id: 子频道 ID
            patch_msg_id: 需要修改的消息 ID
            content: 消息内容，推荐使用 MessagesModel.MessageMarkdown
                      - MessagesModel.MessageMarkdown: Markdown + Keyboard（推荐）
                      - 其他类型会提取其中支持的 markdown/keyboard 字段
            msg_id: 要回复的消息的 ID（被动消息）
            event_id: 要回复的事件 ID（被动消息）

        Returns:
            Model.GuildMessage: 修改后的消息对象

        使用示例：
            # 使用 Markdown 消息对象修改
            md = MessagesModel.MessageMarkdown(content="# 更新后的标题")
            await api.patch_guild_message(channel_id, msg_id, content=md)

            # 使用带 Keyboard 的 Markdown 修改
            md = MessagesModel.MessageMarkdown(
                content="# 标题",
                keyboard_content={"rows": [{"buttons": [...]}]}
            )
            await api.patch_guild_message(channel_id, msg_id, content=md)
        """
        http = await self._get_http()
        endpoint = f"/channels/{channel_id}/messages/{patch_msg_id}"

        payload = {}
        if msg_id:
            payload["msg_id"] = msg_id
        if event_id:
            payload["event_id"] = event_id

        if content is not None:
            if isinstance(content, str):
                content = MessagesModel.Message(content=content)
            built = content.build()
            for key in ("markdown", "keyboard"):
                if key in built and built[key]:
                    payload[key] = built[key]

        data = await http.patch(endpoint, json=payload)
        return Model.GuildMessage.from_dict(data)

    async def send_group_message(
        self,
        group_openid: str,
        content: MessageContent | None = None,
        event_id: str | None = None,
        msg_id: str | None = None,
        msg_seq: int | None = None,
    ) -> Model.GroupSendMessageResponse:
        """
        发送群聊消息

        支持两种方式：
        1. 传入消息对象：content=MessagesModel.MessageMarkdown(content="# 标题")
        2. 传入文本：content="Hello"

        Args:
            group_openid: 群 openid
            content: 消息内容，可以是文本或消息对象
                      - str: 文本消息
                      - MessagesModel.Message: 普通消息
                      - MessagesModel.MessageEmbed: Embed 消息
                      - MessagesModel.MessageArk23/24/37: Ark 模板消息
                      - MessagesModel.MessageMarkdown: Markdown 消息
            event_id: 前置收到的事件 ID（被动消息）
            msg_id: 要回复的消息 ID（被动消息）
            msg_seq: 回复消息的序号

        Returns:
            Model.GroupSendMessageResponse: 发送的消息响应

        使用示例：
            # 文本消息
            await api.send_group_message(group_openid, "Hello")

            # Markdown 消息
            await api.send_group_message(group_openid, MessagesModel.MessageMarkdown(content="# 标题"))

            # Embed 消息
            await api.send_group_message(group_openid, MessagesModel.MessageEmbed(title="标题"))
        """
        endpoint = f"/v2/groups/{group_openid}/messages"
        return await self._send_message(
            endpoint,
            content=content,
            msg_id=msg_id,
            event_id=event_id,
            msg_seq=msg_seq,
            msg_type=(
                getattr(content, "msg_type", None)
                if content and not isinstance(content, str)
                else None
            ),
            response_model=Model.GroupSendMessageResponse,
            require_content=True,
        )

    async def recall_group_message(
        self,
        group_openid: str,
        message_id: str,
    ) -> bool:
        """
        撤回群聊消息

        Args:
            group_openid: 群 openid
            message_id: 消息 ID

        Returns:
            bool: 是否撤回成功
        """
        http = await self._get_http()
        endpoint = f"/v2/groups/{group_openid}/messages/{message_id}"
        await http.delete(endpoint)
        return True

    async def send_c2c_message(
        self,
        openid: str,
        content: MessageContent | None = None,
        event_id: str | None = None,
        msg_id: str | None = None,
        msg_seq: int | None = None,
    ) -> Model.C2CSendMessageResponse:
        """
        发送单聊消息

        支持两种方式：
        1. 传入消息对象：content=MessagesModel.MessageMarkdown(content="# 标题")
        2. 传入文本：content="Hello"

        Args:
            openid: 用户 openid
            content: 消息内容，可以是文本或消息对象
                      - str: 文本消息
                      - MessagesModel.Message: 普通消息
                      - MessagesModel.MessageEmbed: Embed 消息
                      - MessagesModel.MessageArk23/24/37: Ark 模板消息
                      - MessagesModel.MessageMarkdown: Markdown 消息
            event_id: 前置收到的事件 ID（被动消息）
            msg_id: 要回复的消息 ID（被动消息）
            msg_seq: 回复消息的序号

        Returns:
            Model.C2CSendMessageResponse: 发送的消息响应

        使用示例：
            # 文本消息
            await api.send_c2c_message(openid, "Hello")

            # Markdown 消息
            await api.send_c2c_message(openid, MessagesModel.MessageMarkdown(content="# 标题"))

            # Embed 消息
            await api.send_c2c_message(openid, MessagesModel.MessageEmbed(title="标题"))
        """
        endpoint = f"/v2/users/{openid}/messages"
        return await self._send_message(
            endpoint,
            content=content,
            msg_id=msg_id,
            event_id=event_id,
            msg_seq=msg_seq,
            msg_type=(
                getattr(content, "msg_type", None)
                if content and not isinstance(content, str)
                else None
            ),
            response_model=Model.C2CSendMessageResponse,
        )

    async def recall_c2c_message(
        self,
        openid: str,
        message_id: str,
    ) -> bool:
        """
        撤回单聊消息

        Args:
            openid: 用户 openid
            message_id: 消息 ID

        Returns:
            bool: 是否撤回成功
        """
        http = await self._get_http()
        endpoint = f"/v2/users/{openid}/messages/{message_id}"
        await http.delete(endpoint)
        return True

    async def create_dms(
        self,
        recipient_id: str,
        source_guild_id: str,
    ) -> Model.DMS:
        """
        创建私信会话

        Args:
            recipient_id: 接收者 ID
            source_guild_id: 源频道 ID

        Returns:
            Model.DMS: 私信会话对象
        """
        http = await self._get_http()
        payload = {"recipient_id": recipient_id, "source_guild_id": source_guild_id}
        data = await http.post("/users/@me/dms", json=payload)
        return Model.DMS.from_dict(data)

    async def send_direct_message(
        self,
        guild_id: str,
        content: MessageContent | None = None,
        image: str | None = None,
        file_image: bytes | str | None = None,
        msg_id: str | None = None,
        event_id: str | None = None,
    ) -> Model.GuildMessage:
        """
        发送频道私信消息

        支持两种方式：
        1. 传入消息对象：content=MessagesModel.MessageEmbed(title="标题")
        2. 传入文本和参数：content="文本", image="https://..."

        Args:
            guild_id: 私信频道 ID
            content: 消息内容，可以是文本或消息对象
                      - str: 文本消息
                      - MessagesModel.Message: 普通消息
                      - MessagesModel.MessageEmbed: Embed 消息
                      - MessagesModel.MessageArk23/24/37: Ark 模板消息
                      - MessagesModel.MessageMarkdown: Markdown 消息
            image: 图片 URL（当 content 为文本时使用）
            file_image: 图片数据，支持 bytes 或文件路径（当 content 为文本时使用）
            msg_id: 要回复的消息 ID（被动消息）
            event_id: 要回复的事件 ID（被动消息）

        Returns:
            Model.GuildMessage: 发送的消息对象

        使用示例：
            # 方式一：消息对象
            await api.send_direct_message(guild_id, MessagesModel.Message(content="Hello"))
            await api.send_direct_message(guild_id, MessagesModel.MessageEmbed(title="标题"))

            # 方式二：文本+参数
            await api.send_direct_message(guild_id, "Hello")
            await api.send_direct_message(guild_id, "图片", image="https://...")
        """
        endpoint = f"/dms/{guild_id}/messages"
        return await self._send_message(
            endpoint,
            content=content,
            image=image,
            file_image=file_image,
            msg_id=msg_id,
            event_id=event_id,
            response_model=Model.GuildMessage,
        )

    async def recall_direct_message(
        self,
        guild_id: str,
        message_id: str,
        hidetip: bool = False,
    ) -> bool:
        """
        撤回频道私信消息

        Args:
            guild_id: 私信频道 ID
            message_id: 消息 ID
            hidetip: 是否隐藏提示小灰条

        Returns:
            bool: 是否撤回成功
        """
        http = await self._get_http()
        endpoint = f"/dms/{guild_id}/messages/{message_id}"
        params = {"hidetip": str(hidetip).lower()}
        await http.delete(endpoint, params=params)
        return True

    async def get_guild_members(
        self,
        guild_id: str,
        after: str = "0",
        limit: int = 100,
    ) -> list[Model.Member]:
        """
        获取频道成员列表

        Args:
            guild_id: 频道 ID
            after: 上一次回包中最后一个 member 的 user id
            limit: 分页大小，默认 100，最大 1000

        Returns:
            list[Model.Member]: 成员对象列表
        """
        http = await self._get_http()
        params = {"after": after, "limit": limit}
        data = await http.get(f"/guilds/{guild_id}/members", params=params)
        return [Model.Member.from_dict(m) for m in data]

    async def get_guild_member(
        self,
        guild_id: str,
        user_id: str,
    ) -> Model.Member:
        """
        获取频道成员详情

        Args:
            guild_id: 频道 ID
            user_id: 用户 ID

        Returns:
            Model.Member: 成员对象
        """
        http = await self._get_http()
        data = await http.get(f"/guilds/{guild_id}/members/{user_id}")
        return Model.Member.from_dict(data)

    async def delete_guild_member(
        self,
        guild_id: str,
        user_id: str,
        add_blacklist: bool = False,
        delete_history_msg_days: int = 0,
    ) -> bool:
        """
        删除频道成员

        Args:
            guild_id: 频道 ID
            user_id: 用户 ID
            add_blacklist: 是否同时添加到黑名单
            delete_history_msg_days: 撤回消息天数（3, 7, 15, 30, -1 全部）

        Returns:
            bool: 是否删除成功
        """
        http = await self._get_http()
        payload = {
            "add_blacklist": add_blacklist,
            "delete_history_msg_days": delete_history_msg_days,
        }
        await http.delete(f"/guilds/{guild_id}/members/{user_id}", json=payload)
        return True

    async def get_channel_online_nums(
        self, channel_id: str
    ) -> Model.OnlineNumsResponse:
        """
        获取子频道在线成员数

        Args:
            channel_id: 子频道 ID

        Returns:
            Model.OnlineNumsResponse: 在线成员数响应
        """
        http = await self._get_http()
        data = await http.get(f"/channels/{channel_id}/online_nums")
        return Model.OnlineNumsResponse.from_dict(data)

    async def get_guild_roles(self, guild_id: str) -> Model.GuildRolesResponse:
        """
        获取频道身份组列表

        Args:
            guild_id: 频道 ID

        Returns:
            Model.GuildRolesResponse: 包含 roles 列表和 role_num_limit 的响应
        """
        http = await self._get_http()
        data = await http.get(f"/guilds/{guild_id}/roles")
        return Model.GuildRolesResponse.from_dict(data)

    async def create_guild_role(
        self,
        guild_id: str,
        name: str = "新的身份组",
        color: int = 0,
        hoist: int = 0,
    ) -> Model.CreateRoleResponse:
        """
        创建频道身份组

        Args:
            guild_id: 频道 ID
            name: 身份组名称
            color: 颜色值
            hoist: 是否在成员列表中单独展示

        Returns:
            Model.CreateRoleResponse: 包含 role_id 和 role 的响应
        """
        http = await self._get_http()
        payload = {"name": name, "color": color, "hoist": hoist}
        data = await http.post(f"/guilds/{guild_id}/roles", json=payload)
        return Model.CreateRoleResponse.from_dict(data)

    async def update_guild_role(
        self,
        guild_id: str,
        role_id: str,
        name: str | None = None,
        color: int | None = None,
        hoist: int | None = None,
    ) -> Model.CreateRoleResponse:
        """
        修改频道身份组

        Args:
            guild_id: 频道 ID
            role_id: 身份组 ID
            name: 身份组名称
            color: 颜色值
            hoist: 是否在成员列表中单独展示

        Returns:
            Model.CreateRoleResponse: 包含 role_id 和 role 的响应
        """
        http = await self._get_http()
        payload = {}
        if name is not None:
            payload["name"] = name
        if color is not None:
            payload["color"] = color
        if hoist is not None:
            payload["hoist"] = hoist
        data = await http.patch(f"/guilds/{guild_id}/roles/{role_id}", json=payload)
        return Model.CreateRoleResponse.from_dict(data)

    async def delete_guild_role(
        self,
        guild_id: str,
        role_id: str,
    ) -> bool:
        """
        删除频道身份组

        Args:
            guild_id: 频道 ID
            role_id: 身份组 ID

        Returns:
            bool: 是否删除成功
        """
        http = await self._get_http()
        await http.delete(f"/guilds/{guild_id}/roles/{role_id}")
        return True

    async def add_guild_member_role(
        self,
        guild_id: str,
        user_id: str,
        role_id: str,
        channel_id: str | None = None,
    ) -> bool:
        """
        添加成员到身份组

        Args:
            guild_id: 频道 ID
            user_id: 用户 ID
            role_id: 身份组 ID
            channel_id: 子频道 ID（当身份组为子频道管理员时需要）

        Returns:
            bool: 是否添加成功
        """
        http = await self._get_http()
        endpoint = f"/guilds/{guild_id}/members/{user_id}/roles/{role_id}"
        payload = {}
        if channel_id:
            payload["channel"] = {"id": channel_id}
        await http.put(endpoint, json=payload)
        return True

    async def remove_guild_member_role(
        self,
        guild_id: str,
        user_id: str,
        role_id: str,
        channel_id: str | None = None,
    ) -> bool:
        """
        从身份组移除成员

        Args:
            guild_id: 频道 ID
            user_id: 用户 ID
            role_id: 身份组 ID
            channel_id: 子频道 ID（当身份组为子频道管理员时需要）

        Returns:
            bool: 是否移除成功
        """
        http = await self._get_http()
        endpoint = f"/guilds/{guild_id}/members/{user_id}/roles/{role_id}"
        payload = {}
        if channel_id:
            payload["channel"] = {"id": channel_id}
        await http.delete(endpoint, json=payload)
        return True

    async def get_guild_role_members(
        self,
        guild_id: str,
        role_id: str,
        start_index: str = "0",
        limit: int = 20,
    ) -> Model.RoleMembersResponse:
        """
        获取频道身份组成员列表

        Args:
            guild_id: 频道 ID
            role_id: 身份组 ID
            start_index: 分页起始位置
            limit: 分页大小

        Returns:
            Model.RoleMembersResponse: 包含 data 和 next 的响应
        """
        http = await self._get_http()
        params = {"start_index": start_index, "limit": limit}
        data = await http.get(
            f"/guilds/{guild_id}/roles/{role_id}/members", params=params
        )
        return Model.RoleMembersResponse.from_dict(data)

    async def mute_guild(
        self,
        guild_id: str,
        mute_seconds: int | None = None,
        mute_end_timestamp: int | None = None,
    ) -> bool:
        """
        频道全员禁言

        Args:
            guild_id: 频道 ID
            mute_seconds: 禁言秒数
            mute_end_timestamp: 禁言结束时间戳

        Returns:
            bool: 是否禁言成功
        """
        http = await self._get_http()
        payload = {}
        if mute_seconds is not None:
            payload["mute_seconds"] = str(mute_seconds)
        if mute_end_timestamp is not None:
            payload["mute_end_timestamp"] = str(mute_end_timestamp)
        await http.patch(f"/guilds/{guild_id}/mute", json=payload)
        return True

    async def mute_guild_member(
        self,
        guild_id: str,
        user_id: str,
        mute_seconds: int | None = None,
        mute_end_timestamp: int | None = None,
    ) -> bool:
        """
        频道指定成员禁言

        Args:
            guild_id: 频道 ID
            user_id: 用户 ID
            mute_seconds: 禁言秒数
            mute_end_timestamp: 禁言结束时间戳

        Returns:
            bool: 是否禁言成功
        """
        http = await self._get_http()
        payload = {}
        if mute_seconds is not None:
            payload["mute_seconds"] = str(mute_seconds)
        if mute_end_timestamp is not None:
            payload["mute_end_timestamp"] = str(mute_end_timestamp)
        await http.patch(f"/guilds/{guild_id}/members/{user_id}/mute", json=payload)
        return True

    async def mute_guild_members(
        self,
        guild_id: str,
        user_ids: list[str],
        mute_seconds: int | None = None,
        mute_end_timestamp: int | None = None,
    ) -> Model.MuteBatchResponse:
        """
        频道批量成员禁言

        Args:
            guild_id: 频道 ID
            user_ids: 用户 ID 列表
            mute_seconds: 禁言秒数
            mute_end_timestamp: 禁言结束时间戳

        Returns:
            Model.MuteBatchResponse: 设置成功的用户 ID 列表响应
        """
        http = await self._get_http()
        payload = {"user_ids": user_ids}
        if mute_seconds is not None:
            payload["mute_seconds"] = str(mute_seconds)
        if mute_end_timestamp is not None:
            payload["mute_end_timestamp"] = str(mute_end_timestamp)
        data = await http.patch(f"/guilds/{guild_id}/mute", json=payload)
        return Model.MuteBatchResponse.from_dict(data)

    async def cancel_mute_all(self, guild_id: str) -> bool:
        """
        取消频道全员禁言

        Args:
            guild_id: 频道 ID

        Returns:
            bool: 是否操作成功
        """
        http = await self._get_http()
        payload = {"mute_end_timestamp": "0", "mute_seconds": "0"}
        await http.patch(f"/guilds/{guild_id}/mute", json=payload)
        return True

    async def cancel_mute_multi_member(
        self, guild_id: str, user_ids: list[str]
    ) -> Model.MuteBatchResponse:
        """
        取消频道批量成员禁言

        Args:
            guild_id: 频道 ID
            user_ids: 用户 ID 列表

        Returns:
            Model.MuteBatchResponse: 设置成功的用户 ID 列表响应
        """
        http = await self._get_http()
        payload = {"mute_end_timestamp": "0", "mute_seconds": "0", "user_ids": user_ids}
        data = await http.patch(f"/guilds/{guild_id}/mute", json=payload)
        return Model.MuteBatchResponse.from_dict(data)

    async def get_channel_user_permissions(
        self,
        channel_id: str,
        user_id: str,
    ) -> Model.ChannelPermissions:
        """
        获取子频道用户权限

        Args:
            channel_id: 子频道 ID
            user_id: 用户 ID

        Returns:
            Model.ChannelPermissions: 子频道权限对象
        """
        http = await self._get_http()
        data = await http.get(f"/channels/{channel_id}/members/{user_id}/permissions")
        return Model.ChannelPermissions.from_dict(data)

    async def get_channel_role_permissions(
        self,
        channel_id: str,
        role_id: str,
    ) -> Model.ChannelPermissions:
        """
        获取子频道身份组权限

        Args:
            channel_id: 子频道 ID
            role_id: 身份组 ID

        Returns:
            Model.ChannelPermissions: 子频道权限对象
        """
        http = await self._get_http()
        data = await http.get(f"/channels/{channel_id}/roles/{role_id}/permissions")
        return Model.ChannelPermissions.from_dict(data)

    async def update_channel_user_permissions(
        self,
        channel_id: str,
        user_id: str,
        add: str | None = None,
        remove: str | None = None,
    ) -> bool:
        """
        修改子频道用户权限

        Args:
            channel_id: 子频道 ID
            user_id: 用户 ID
            add: 赋予的权限
            remove: 删除的权限

        Returns:
            bool: 是否修改成功
        """
        http = await self._get_http()
        payload = {}
        if add is not None:
            payload["add"] = add
        if remove is not None:
            payload["remove"] = remove
        await http.put(
            f"/channels/{channel_id}/members/{user_id}/permissions", json=payload
        )
        return True

    async def update_channel_role_permissions(
        self,
        channel_id: str,
        role_id: str,
        add: str | None = None,
        remove: str | None = None,
    ) -> bool:
        """
        修改子频道身份组权限

        Args:
            channel_id: 子频道 ID
            role_id: 身份组 ID
            add: 赋予的权限
            remove: 删除的权限

        Returns:
            bool: 是否修改成功
        """
        http = await self._get_http()
        payload = {}
        if add is not None:
            payload["add"] = add
        if remove is not None:
            payload["remove"] = remove
        await http.put(
            f"/channels/{channel_id}/roles/{role_id}/permissions", json=payload
        )
        return True

    async def get_guild_api_permissions(
        self, guild_id: str
    ) -> Model.APIPermissionListResponse:
        """
        获取机器人在频道可用权限列表

        Args:
            guild_id: 频道 ID

        Returns:
            Model.APIPermissionListResponse: 包含 apis 列表的响应
        """
        http = await self._get_http()
        data = await http.get(f"/guilds/{guild_id}/api_permission")
        return Model.APIPermissionListResponse.from_dict(data)

    async def demand_guild_api_permission(
        self,
        guild_id: str,
        channel_id: str,
        api_path: str,
        api_method: str,
        desc: str,
    ) -> Model.APIPermissionDemand:
        """
        发送机器人在频道接口权限的授权链接

        Args:
            guild_id: 频道 ID
            channel_id: 授权链接发送的子频道 ID
            api_path: API 接口名
            api_method: 请求方法
            desc: 机器人申请权限后可使用功能的描述

        Returns:
            Model.APIPermissionDemand: API权限需求对象
        """
        http = await self._get_http()
        payload = {
            "channel_id": channel_id,
            "api_identify": {"path": api_path, "method": api_method},
            "desc": desc,
        }
        data = await http.post(
            f"/guilds/{guild_id}/api_permission/demand", json=payload
        )
        return Model.APIPermissionDemand.from_dict(data)

    async def create_announces(
        self,
        guild_id: str,
        message_id: str | None = None,
        channel_id: str | None = None,
        announces_type: int = 0,
        recommend_channels: list[dict] | None = None,
    ) -> Model.Announces:
        """
        创建频道公告

        Args:
            guild_id: 频道 ID
            message_id: 消息 ID
            channel_id: 子频道 ID
            announces_type: 公告类别（0 成员公告，1 欢迎公告）
            recommend_channels: 推荐子频道列表

        Returns:
            Model.Announces: 公告对象
        """
        http = await self._get_http()
        payload = {"announces_type": announces_type}
        if message_id:
            payload["message_id"] = message_id
        if channel_id:
            payload["channel_id"] = channel_id
        if recommend_channels:
            payload["recommend_channels"] = recommend_channels
        data = await http.post(f"/guilds/{guild_id}/announces", json=payload)
        return Model.Announces.from_dict(data)

    async def delete_announces(
        self,
        guild_id: str,
        message_id: str = "all",
    ) -> bool:
        """
        删除频道公告

        Args:
            guild_id: 频道 ID
            message_id: 消息 ID，传 "all" 删除全部

        Returns:
            bool: 是否删除成功
        """
        http = await self._get_http()
        await http.delete(f"/guilds/{guild_id}/announces/{message_id}")
        return True

    async def get_schedules(
        self,
        channel_id: str,
        since: str | None = None,
    ) -> list[Model.Schedule]:
        """
        获取频道日程列表

        Args:
            channel_id: 子频道 ID
            since: 起始时间戳（ms）

        Returns:
            list[Model.Schedule]: 日程对象列表
        """
        http = await self._get_http()
        params = {}
        if since:
            params["since"] = since
        data = await http.get(f"/channels/{channel_id}/schedules", params=params)
        return [Model.Schedule.from_dict(s) for s in data]

    async def get_schedule(
        self,
        channel_id: str,
        schedule_id: str,
    ) -> Model.Schedule:
        """
        获取日程详情

        Args:
            channel_id: 子频道 ID
            schedule_id: 日程 ID

        Returns:
            Model.Schedule: 日程对象
        """
        http = await self._get_http()
        data = await http.get(f"/channels/{channel_id}/schedules/{schedule_id}")
        return Model.Schedule.from_dict(data)

    async def create_schedule(
        self,
        channel_id: str,
        name: str,
        start_timestamp: str,
        end_timestamp: str,
        jump_channel_id: str | None = None,
        remind_type: str = "0",
        description: str | None = None,
    ) -> Model.Schedule:
        """
        创建日程

        Args:
            channel_id: 子频道 ID
            name: 日程名称
            start_timestamp: 开始时间戳（ms）
            end_timestamp: 结束时间戳（ms）
            jump_channel_id: 开始时跳转到的子频道 ID
            remind_type: 提醒类型（0 无提醒，1 开始时提醒，2 5分钟前，3 15分钟前，4 30分钟前，5 60分钟前）
            description: 日程描述

        Returns:
            Model.Schedule: 日程对象
        """
        http = await self._get_http()
        payload = {
            "name": name,
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
            "remind_type": remind_type,
        }
        if jump_channel_id:
            payload["jump_channel_id"] = jump_channel_id
        if description:
            payload["description"] = description
        data = await http.post(f"/channels/{channel_id}/schedules", json=payload)
        return Model.Schedule.from_dict(data)

    async def update_schedule(
        self,
        channel_id: str,
        schedule_id: str,
        name: str | None = None,
        start_timestamp: str | None = None,
        end_timestamp: str | None = None,
        jump_channel_id: str | None = None,
        remind_type: str | None = None,
        description: str | None = None,
    ) -> Model.Schedule:
        """
        修改日程

        Args:
            channel_id: 子频道 ID
            schedule_id: 日程 ID
            name: 日程名称
            start_timestamp: 开始时间戳（ms）
            end_timestamp: 结束时间戳（ms）
            jump_channel_id: 开始时跳转到的子频道 ID
            remind_type: 提醒类型（0 无提醒，1 开始时提醒，2 5分钟前，3 15分钟前，4 30分钟前，5 60分钟前）
            description: 日程描述

        Returns:
            Model.Schedule: 日程对象
        """
        http = await self._get_http()
        payload = {}
        if name is not None:
            payload["name"] = name
        if start_timestamp is not None:
            payload["start_timestamp"] = start_timestamp
        if end_timestamp is not None:
            payload["end_timestamp"] = end_timestamp
        if jump_channel_id is not None:
            payload["jump_channel_id"] = jump_channel_id
        if remind_type is not None:
            payload["remind_type"] = remind_type
        if description is not None:
            payload["description"] = description
        data = await http.patch(
            f"/channels/{channel_id}/schedules/{schedule_id}", json=payload
        )
        return Model.Schedule.from_dict(data)

    async def delete_schedule(
        self,
        channel_id: str,
        schedule_id: str,
    ) -> bool:
        """
        删除日程

        Args:
            channel_id: 子频道 ID
            schedule_id: 日程 ID

        Returns:
            bool: 是否删除成功
        """
        http = await self._get_http()
        await http.delete(f"/channels/{channel_id}/schedules/{schedule_id}")
        return True

    async def get_pins(self, channel_id: str) -> Model.PinsMessage:
        """
        获取精华消息

        Args:
            channel_id: 子频道 ID

        Returns:
            Model.PinsMessage: 精华消息对象
        """
        http = await self._get_http()
        data = await http.get(f"/channels/{channel_id}/pins")
        return Model.PinsMessage.from_dict(data)

    async def add_pin(
        self,
        channel_id: str,
        message_id: str,
    ) -> Model.PinsMessage:
        """
        添加精华消息

        Args:
            channel_id: 子频道 ID
            message_id: 消息 ID

        Returns:
            Model.PinsMessage: 精华消息对象
        """
        http = await self._get_http()
        data = await http.put(f"/channels/{channel_id}/pins/{message_id}")
        return Model.PinsMessage.from_dict(data)

    async def delete_pin(
        self,
        channel_id: str,
        message_id: str,
    ) -> bool:
        """
        删除精华消息

        Args:
            channel_id: 子频道 ID
            message_id: 消息 ID

        Returns:
            bool: 是否删除成功
        """
        http = await self._get_http()
        await http.delete(f"/channels/{channel_id}/pins/{message_id}")
        return True

    async def get_reaction_users(
        self,
        channel_id: str,
        message_id: str,
        emoji_type: int,
        emoji_id: str,
        cookie: str | None = None,
        limit: int = 20,
    ) -> Model.ReactionUsers:
        """
        获取表情表态用户列表

        Args:
            channel_id: 子频道 ID
            message_id: 消息 ID
            emoji_type: 表情类型
            emoji_id: 表情 ID
            cookie: 分页 cookie
            limit: 每页数量

        Returns:
            Model.ReactionUsers: 表情表态用户列表
        """
        http = await self._get_http()
        params = {"type": emoji_type, "id": emoji_id, "limit": limit}
        if cookie:
            params["cookie"] = cookie
        data = await http.get(
            f"/channels/{channel_id}/messages/{message_id}/reactions", params=params
        )
        return Model.ReactionUsers.from_dict(data)

    async def create_reaction(
        self,
        channel_id: str,
        message_id: str,
        emoji_type: int,
        emoji_id: str,
    ) -> bool:
        """
        机器人发表表情表态

        Args:
            channel_id: 子频道 ID
            message_id: 消息 ID
            emoji_type: 表情类型（1 系统表情，2 emoji表情）
            emoji_id: 表情 ID

        Returns:
            bool: 是否操作成功
        """
        http = await self._get_http()
        await http.put(
            f"/channels/{channel_id}/messages/{message_id}/reactions/{emoji_type}/{emoji_id}"
        )
        return True

    async def delete_reaction(
        self,
        channel_id: str,
        message_id: str,
        emoji_type: int,
        emoji_id: str,
    ) -> bool:
        """
        删除机器人发表的表情表态

        Args:
            channel_id: 子频道 ID
            message_id: 消息 ID
            emoji_type: 表情类型（1 系统表情，2 emoji表情）
            emoji_id: 表情 ID

        Returns:
            bool: 是否操作成功
        """
        http = await self._get_http()
        await http.delete(
            f"/channels/{channel_id}/messages/{message_id}/reactions/{emoji_type}/{emoji_id}"
        )
        return True

    async def audio_control(
        self,
        channel_id: str,
        audio_url: str | None = None,
        text: str | None = None,
        status: int = 0,
    ) -> bool:
        """
        音频控制

        Args:
            channel_id: 子频道 ID
            audio_url: 音频 URL
            text: 状态文本
            status: 播放状态（0 开始、1 暂停、2 继续、3 停止）

        Returns:
            bool: 是否操作成功
        """
        http = await self._get_http()
        payload = {"status": status}
        if audio_url:
            payload["audio_url"] = audio_url
        if text:
            payload["text"] = text
        await http.post(f"/channels/{channel_id}/audio", json=payload)
        return True

    async def mic_up(self, channel_id: str) -> bool:
        """
        机器人上麦

        Args:
            channel_id: 子频道 ID

        Returns:
            bool: 是否上麦成功
        """
        http = await self._get_http()
        await http.put(f"/channels/{channel_id}/mic")
        return True

    async def mic_down(self, channel_id: str) -> bool:
        """
        机器人下麦

        Args:
            channel_id: 子频道 ID

        Returns:
            bool: 是否下麦成功
        """
        http = await self._get_http()
        await http.delete(f"/channels/{channel_id}/mic")
        return True

    async def get_thread(
        self,
        channel_id: str,
        thread_id: str,
    ) -> Model.ThreadDetail:
        """
        获取帖子详情

        Args:
            channel_id: 子频道 ID
            thread_id: 帖子 ID

        Returns:
            Model.ThreadDetail: 帖子详情对象
        """
        http = await self._get_http()
        data = await http.get(f"/channels/{channel_id}/threads/{thread_id}")
        return Model.ThreadDetail.from_dict(data)

    async def get_threads(
        self,
        channel_id: str,
    ) -> Model.ThreadListResult:
        """
        获取帖子列表

        Args:
            channel_id: 子频道 ID（须为论坛子频道 type=10007）

        Returns:
            Model.ThreadListResult: 帖子列表结果，包含 threads 和 is_finish
        """
        http = await self._get_http()
        data = await http.get(f"/channels/{channel_id}/threads")
        return Model.ThreadListResult.from_dict(data)

    async def create_thread(
        self,
        channel_id: str,
        title: str,
        content: str,
        format: int = 3,
    ) -> Model.CreateThreadResponse:
        """
        发表帖子

        Args:
            channel_id: 子频道 ID（须为论坛子频道 type=10007）
            title: 帖子标题
            content: 帖子内容
            format: 帖子格式（1=纯文本, 2=HTML, 3=Markdown, 4=JSON），默认 3

        Returns:
            Model.CreateThreadResponse: 创建帖子响应，包含 task_id 和 create_time
        """
        http = await self._get_http()
        payload = {"title": title, "content": content, "format": format}
        data = await http.put(f"/channels/{channel_id}/threads", json=payload)
        return Model.CreateThreadResponse.from_dict(data)

    async def delete_thread(
        self,
        channel_id: str,
        thread_id: str,
    ) -> bool:
        """
        删除帖子

        Args:
            channel_id: 子频道 ID
            thread_id: 帖子 ID

        Returns:
            bool: 是否删除成功
        """
        http = await self._get_http()
        await http.delete(f"/channels/{channel_id}/threads/{thread_id}")
        return True

    async def create_thread_comment(
        self,
        channel_id: str,
        thread_id: str,
        thread_author: str,
        content: str,
        thread_create_time: str | None = None,
        image: str | None = None,
    ) -> Model.CreateCommentResponse:
        """
        发表评论

        Args:
            channel_id: 子频道 ID
            thread_id: 帖子 ID
            thread_author: 帖子作者 ID
            content: 评论内容
            thread_create_time: 帖子创建时间
            image: 图片链接

        Returns:
            Model.CreateCommentResponse: 创建评论响应，包含 task_id 和 create_time
        """
        http = await self._get_http()
        payload = {
            "thread_author": thread_author,
            "content": content,
        }
        if thread_create_time:
            payload["thread_create_time"] = thread_create_time
        if image:
            payload["image"] = image
        data = await http.post(
            f"/channels/{channel_id}/threads/{thread_id}/comment", json=payload
        )
        return Model.CreateCommentResponse.from_dict(data)

    async def get_gateway(self) -> Model.GatewayResponse:
        """
        获取通用 WSS 接入点

        Returns:
            Model.GatewayResponse: 包含 url 的响应
        """
        http = await self._get_http()
        data = await http.get("/gateway")
        return Model.GatewayResponse.from_dict(data)

    async def get_gateway_bot(self) -> Model.GatewayBotResponse:
        """
        获取带分片 WSS 接入点

        Returns:
            Model.GatewayBotResponse: 包含 url、shards 和 session_start_limit 的响应
        """
        http = await self._get_http()
        data = await http.get("/gateway/bot")
        return Model.GatewayBotResponse.from_dict(data)

    async def get_guild_message_setting(self, guild_id: str) -> Model.MessageSetting:
        """
        获取频道消息频率设置

        Args:
            guild_id: 频道 ID

        Returns:
            Model.MessageSetting: 消息频率设置对象
        """
        http = await self._get_http()
        data = await http.get(f"/guilds/{guild_id}/message/setting")
        return Model.MessageSetting.from_dict(data)

    async def respond_interaction(
        self,
        interaction_id: str,
        code: int = 0,
    ) -> bool:
        """
        回应互动按钮点击事件

        由于 websocket 推送事件是单向的，开发者收到事件之后，
        需要进行一次"回应"，告知QQ后台事件已经收到。

        Args:
            interaction_id: 互动事件 ID
            code: 回应码
                - 0: 成功
                - 1: 操作失败
                - 2: 操作频繁
                - 3: 重复操作
                - 4: 没有权限
                - 5: 仅管理员操作

        Returns:
            bool: 是否回应成功
        """
        http = await self._get_http()
        payload = {"code": code}
        await http.put(f"/interactions/{interaction_id}", json=payload)
        return True

    async def generate_url_link(
        self,
        callback_data: str | None = None,
    ) -> Model.UrlLinkResponse:
        """
        获取机器人资料页分享链接

        开发者可传入参数，用作追踪该链接后续被用户添加使用机器人的来源归因。

        Args:
            callback_data: 添加好友时会回传该参数给到开发者（最长32字符）

        Returns:
            Model.UrlLinkResponse: 包含 url 字段的响应
        """
        http = await self._get_http()
        payload = {}
        if callback_data:
            payload["callback_data"] = callback_data
        data = await http.post("/v2/generate_url_link", json=payload)
        return Model.UrlLinkResponse.from_dict(data)

    async def upload_media(
        self,
        file_type: int,
        url: str | None = None,
        file_data: bytes | str | None = None,
        srv_send_msg: bool = False,
        user_openid: str | None = None,
        group_openid: str | None = None,
    ) -> Model.FileInfo:
        """
        上传富媒体文件（QQ单聊和QQ群聊通用）

        Args:
            file_type: 媒体类型（1 图片、2 视频、3 语音、4 文件）
            url: 媒体资源 URL
            file_data: 文件数据，支持三种方式：
                       - bytes: 二进制数据
                       - str: 本地文件路径
            srv_send_msg: 是否直接发送消息到目标端，设置为 True 会直接发送消息且占用主动消息频次
            user_openid: 用户 openid（单聊时使用，与 group_openid 二选一）
            group_openid: 群 openid（群聊时使用，与 user_openid 二选一）

        Returns:
            Model.FileInfo: 包含 file_uuid、file_info、ttl 字段的响应

        使用示例：
            # 方式一：文件路径
            result = await api.upload_media(
                file_type=1,
                file_data="./image.png",
                user_openid="xxx"
            )

            # 方式二：二进制数据
            with open("image.png", "rb") as f:
                result = await api.upload_media(
                    file_type=1,
                    file_data=f.read(),
                    user_openid="xxx"
                )

            # 方式三：URL
            result = await api.upload_media(
                file_type=1,
                url="https://example.com/image.png",
                user_openid="xxx"
            )

        注意:
            url 和 file_data 必须提供其中之一
            user_openid 和 group_openid 必须提供其中之一，不能同时提供
        """
        if not url and not file_data:
            raise ValueError("url 和 file_data 必须提供其中之一")

        if user_openid and group_openid:
            raise ValueError("user_openid 和 group_openid 不能同时提供")

        if not user_openid and not group_openid:
            raise ValueError("user_openid 和 group_openid 必须提供其中之一")

        http = await self._get_http()
        payload = {"file_type": file_type, "srv_send_msg": srv_send_msg}

        payload["url"] = url if url else ""
        if file_data:
            if isinstance(file_data, str):
                path = Path(file_data)
                if not path.exists():
                    raise FileNotFoundError(f"文件不存在: {file_data}")
                file_data = path.read_bytes()
            payload["file_data"] = base64.b64encode(file_data).decode("utf-8")

        if user_openid:
            data = await http.post(f"/v2/users/{user_openid}/files", json=payload)
        else:
            data = await http.post(f"/v2/groups/{group_openid}/files", json=payload)
        return Model.FileInfo.from_dict(data)

    async def send_c2c_stream_message(
        self,
        openid: str,
        content_raw: str,
        event_id: str,
        msg_id: str,
        msg_seq: int,
        index: int,
        input_mode: str = "replace",
        input_state: int = 1,
        content_type: str = "markdown",
        stream_msg_id: str | None = None,
    ) -> Model.StreamMessageResponse:
        """
        发送流式消息（C2C 私聊）

        流式协议：
        - 首次调用时不传 stream_msg_id，由平台返回
        - 后续分片携带 stream_msg_id 和递增 msg_seq
        - input_state=1 表示生成中，10 表示生成结束（终结状态）

        Args:
            openid: 用户 openid
            content_raw: markdown 内容
            event_id: 事件 ID
            msg_id: 原始消息 ID
            msg_seq: 递增序号
            index: 同一条流式会话内的发送索引，从 0 开始，每次发送前递增
            input_mode: 输入模式，默认 "replace"（每次发送的 content_raw 替换整条消息内容）
            input_state: 输入状态，1=正文生成中，10=正文生成结束（终结状态）
            content_type: 内容类型，默认 "markdown"
            stream_msg_id: 流式消息 ID，首次发送后返回，后续分片需携带

        Returns:
            Model.StreamMessageResponse: 流式消息响应

        使用示例：
            # 首次发送（开始流式消息）
            resp = await api.send_c2c_stream_message(
                openid="xxx",
                content_raw="正在生成...",
                event_id="event_xxx",
                msg_id="msg_xxx",
                msg_seq=0,
                index=0,
                input_state=Model.StreamInputState.GENERATING,
            )
            stream_msg_id = resp.id  # 保存后续使用

            # 后续分片
            await api.send_c2c_stream_message(
                openid="xxx",
                content_raw="内容更新...",
                event_id="event_xxx",
                msg_id="msg_xxx",
                msg_seq=1,
                index=1,
                stream_msg_id=stream_msg_id,
                input_state=Model.StreamInputState.GENERATING,
            )

            # 结束流式消息
            await api.send_c2c_stream_message(
                openid="xxx",
                content_raw="最终内容",
                event_id="event_xxx",
                msg_id="msg_xxx",
                msg_seq=2,
                index=2,
                stream_msg_id=stream_msg_id,
                input_state=Model.StreamInputState.DONE,
            )
        """
        http = await self._get_http()
        endpoint = f"/v2/users/{openid}/stream_messages"

        payload = {
            "input_mode": input_mode,
            "input_state": input_state,
            "content_type": content_type,
            "content_raw": content_raw,
            "event_id": event_id,
            "msg_id": msg_id,
            "msg_seq": msg_seq,
            "index": index,
        }

        if stream_msg_id:
            payload["stream_msg_id"] = stream_msg_id

        self._logger.debug(
            f"发送流式消息: openid={openid}, msg_seq={msg_seq}, index={index}, "
            f"input_state={input_state}"
        )

        data = await http.post(endpoint, json=payload)
        response = Model.StreamMessageResponse.from_dict(data)

        self._logger.debug(
            f"流式消息已发送: msg_seq={msg_seq}, "
            f"stream_msg_id={getattr(response, 'id', 'unknown')}"
        )

        return response
