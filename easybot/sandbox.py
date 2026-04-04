#!/usr/bin/env python3
"""
EasyBot SDK 沙箱配置模块

提供沙箱环境配置，用于限制或过滤消息接收范围。
"""

from dataclasses import dataclass, field


@dataclass
class SandBox:
    """
    沙箱环境配置

    当 Bot(..., is_sandbox=True) 时，只有此实例指定的频道、私信用户、群、用户可以接收到消息。
    当 Bot(..., is_sandbox=False) 时，过滤掉此实例指定的频道、私信用户、群、用户的消息。

    示例:
        # 沙箱模式：只接收指定频道的消息
        sandbox = SandBox(guilds=["123456789"])
        bot = Bot(app_id="xxx", app_secret="xxx", is_sandbox=True, sandbox=sandbox)

        # 过滤模式：过滤掉指定频道的消息
        bot = Bot(app_id="xxx", app_secret="xxx", is_sandbox=False, sandbox=sandbox)
    """

    guilds: list[str] | None = field(default=None)
    guild_users: list[str] | None = field(default=None)
    groups: list[str] | None = field(default=None)
    q_users: list[str] | None = field(default=None)
    sandbox_fail_action: bool = field(default=True)

    def check_guild(self, guild_id: str, is_sandbox: bool) -> bool:
        """
        检查频道是否在沙箱范围内

        Args:
            guild_id: 频道 ID
            is_sandbox: 是否为沙箱模式

        Returns:
            是否通过沙箱检查
        """
        if not self.guilds:
            return self.sandbox_fail_action

        in_list = guild_id in self.guilds

        if is_sandbox:
            return in_list
        else:
            return not in_list

    def check_group(self, group_openid: str, is_sandbox: bool) -> bool:
        """
        检查群是否在沙箱范围内

        Args:
            group_openid: 群 openid
            is_sandbox: 是否为沙箱模式

        Returns:
            是否通过沙箱检查
        """
        if not self.groups:
            return self.sandbox_fail_action

        in_list = group_openid in self.groups

        if is_sandbox:
            return in_list
        else:
            return not in_list

    def check_user(self, user_id: str, is_sandbox: bool, is_qq: bool = False) -> bool:
        """
        检查用户是否在沙箱范围内

        Args:
            user_id: 用户 ID
            is_sandbox: 是否为沙箱模式
            is_qq: 是否为 QQ 用户（True 为 QQ 私信，False 为频道私信）

        Returns:
            是否通过沙箱检查
        """
        user_list = self.q_users if is_qq else self.guild_users

        if not user_list:
            return self.sandbox_fail_action

        in_list = user_id in user_list

        if is_sandbox:
            return in_list
        else:
            return not in_list
