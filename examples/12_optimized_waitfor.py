#!/usr/bin/env python3
"""
EasyBot SDK 示例 12：优化后的 wait_for 使用方法

展示 Session 会话管理器和 wait_for 的优化功能：
- 简洁的 wait_for 接口（直接传 command/regex）
- 高级用法：直接传入 BotCommandObject 使用完整参数
- 自定义谓词函数匹配
- 超时回调函数
- 插件命令的动态管理
"""

from re import compile as re_compile

from easybot import (
    Bot,
    BotCommandObject,
    CommandValidScenes,
    Model,
    Plugins,
    Scope,
    WaitTimeoutError,
)
from easybot.models import C2CMessage, DirectMessage, GroupMessage, GuildMessage


def main() -> None:
    bot: Bot = Bot(
        app_id="your_app_id",
        app_secret="your_app_secret",
    )

    # ==================== 12.1 简洁的 wait_for 使用 ====================
    @bot.on_command(command="简单确认")
    async def cmd_simple_confirm(
        msg: (
            Model.GuildMessage
            | Model.GroupMessage
            | Model.C2CMessage
            | Model.DirectMessage
        ),
    ) -> None:
        """演示简洁的 wait_for 接口使用"""
        with bot.session.bind(msg) as s:
            await msg.reply("请回复「确认」或「取消」：")

            try:
                # 直接使用字符串列表作为命令
                result = await s.wait_for(
                    scopes=Scope.USER,
                    command=["确认", "取消"],  # 简化，无需 BotCommandObject
                    timeout=30,
                )

                if "确认" in result.content:
                    await msg.reply("✅ 已确认！操作执行成功")
                else:
                    await msg.reply("❌ 已取消")

            except WaitTimeoutError:
                await msg.reply("⏰ 等待超时，操作自动取消")

    # ==================== 12.2 使用正则表达式 ====================
    @bot.on_command(command="数字输入")
    async def cmd_number_input(
        msg: (
            Model.GuildMessage
            | Model.GroupMessage
            | Model.C2CMessage
            | Model.DirectMessage
        ),
    ) -> None:
        """演示使用正则表达式作为 wait_for 条件"""
        with bot.session.bind(msg) as s:
            await msg.reply("请输入一个 1-100 之间的数字：")

            try:
                # 使用正则表达式
                result = await s.wait_for(
                    scopes=Scope.USER,
                    command=re_compile(r"^(\d{1,3})$"),  # 直接传正则
                    timeout=30,
                )

                # 获取正则捕获组
                num = int(result.treated_msg[0])
                if 1 <= num <= 100:
                    await msg.reply(f"✅ 你输入了：{num}")
                else:
                    await msg.reply(f"❌ 数字 {num} 不在 1-100 范围内")

            except WaitTimeoutError:
                await msg.reply("⏰ 等待超时")

    # ==================== 12.3 使用谓词函数 ====================
    @bot.on_command(command="自定义匹配")
    async def cmd_predicate_match(
        msg: (
            Model.GuildMessage
            | Model.GroupMessage
            | Model.C2CMessage
            | Model.DirectMessage
        ),
    ) -> None:
        """演示使用自定义谓词函数进行匹配"""
        with bot.session.bind(msg) as s:
            await msg.reply("请发送一条包含至少 3 个表情符号的消息：")

            try:
                # 使用自定义谓词函数
                def has_multiple_emojis(
                    message: (
                        Model.GuildMessage
                        | Model.GroupMessage
                        | Model.C2CMessage
                        | Model.DirectMessage
                    ),
                ) -> bool:
                    """检查消息中是否包含至少3个表情符号"""
                    content = message.content
                    # 简单的表情检测（实际项目应使用更完善的方法）
                    emoji_chars = [c for c in content if ord(c) > 0x1F000]
                    return len(emoji_chars) >= 3

                result = await s.wait_for(
                    scopes=Scope.USER,
                    command=None,  # 不使用 command/regex 匹配
                    predicate=has_multiple_emojis,  # 使用谓词函数
                    timeout=60,
                )

                await msg.reply(f"✅ 检测到足够的表情！消息内容：{result.content}")

            except WaitTimeoutError:
                await msg.reply("⏰ 等待超时，请发送包含3个以上表情的消息")

    # ==================== 12.4 使用超时回调 ====================
    @bot.on_command(command="超时回调")
    async def cmd_timeout_callback(
        msg: (
            Model.GuildMessage
            | Model.GroupMessage
            | Model.C2CMessage
            | Model.DirectMessage
        ),
    ) -> None:
        """演示使用超时回调函数"""
        with bot.session.bind(msg) as s:
            await msg.reply("请在 10 秒内回复「收到」：")

            # 记录超时的次数
            timeout_count = 0

            def on_timeout():
                """超时回调函数"""
                nonlocal timeout_count
                timeout_count += 1

            try:
                result = await s.wait_for(
                    scopes=Scope.USER, command="收到", timeout=10, on_timeout=on_timeout
                )

                await msg.reply(f"✅ 收到！超时次数：{timeout_count}")

            except WaitTimeoutError:
                await msg.reply(f"⏰ 等待超时！超时次数：{timeout_count}")

    # ==================== 12.5 不指定命令（接受任意输入） ====================
    @bot.on_command(command="任意输入")
    async def cmd_any_input(
        msg: (
            Model.GuildMessage
            | Model.GroupMessage
            | Model.C2CMessage
            | Model.DirectMessage
        ),
    ) -> None:
        """演示不指定 command，接受任何输入"""
        with bot.session.bind(msg) as s:
            await msg.reply("请随意说点什么：")

            try:
                # 不指定 command，接受任意输入
                result = await s.wait_for(
                    scopes=Scope.USER, command=None, timeout=30  # 不指定命令
                )

                await msg.reply(f"👂 听到了：{result.content}")

            except WaitTimeoutError:
                await msg.reply("⏰ 等待超时")

    # ==================== 12.6 插件命令动态管理 ====================
    @bot.on_command(command="管理命令")
    async def cmd_manage_commands(
        msg: (
            Model.GuildMessage
            | Model.GroupMessage
            | Model.C2CMessage
            | Model.DirectMessage
        ),
    ) -> None:
        """演示插件命令的动态管理"""

        with bot.session.bind(msg) as s:
            await msg.reply(
                "📋 命令管理菜单：\n1. 查看所有命令\n2. 禁用/启用「简单确认」命令\n请选择："
            )

            try:
                result = await s.wait_for(
                    scopes=Scope.USER, command=["1", "2"], timeout=30
                )

                choice = result.content

                if choice == "1":
                    # 获取所有命令
                    all_commands = Plugins.get_all_commands()
                    cmd_list = []
                    for cmd in all_commands:
                        status = "✅" if cmd.enabled else "❌"
                        names = ", ".join(cmd.command) if cmd.command else "正则"
                        cmd_list.append(f"{status} {cmd.func.__name__}: {names}")

                    await msg.reply("📋 所有命令：\n" + "\n".join(cmd_list))

                elif choice == "2":
                    # 切换「简单确认」命令的启用状态
                    current = Plugins.is_command_enabled("cmd_simple_confirm")
                    if current:
                        Plugins.disable_command("cmd_simple_confirm")
                        await msg.reply("❌ 已禁用「简单确认」命令")
                    else:
                        Plugins.enable_command("cmd_simple_confirm")
                        await msg.reply("✅ 已启用「简单确认」命令")

            except WaitTimeoutError:
                await msg.reply("⏰ 选择超时")

    # ==================== 12.7 高级用法：直接传入 BotCommandObject ====================

    @bot.on_command(command="管理员确认")
    async def cmd_admin_confirm(
        msg: (
            Model.GuildMessage
            | Model.GroupMessage
            | Model.C2CMessage
            | Model.DirectMessage
        ),
    ) -> None:
        """演示通过 BotCommandObject 使用 admin 权限校验"""
        with bot.session.bind(msg) as s:
            await msg.reply(
                "🔒 此操作需要管理员权限\n" "请回复「确认执行」或「取消」："
            )

            try:
                # 直接传入 BotCommandObject，使用 admin 参数进行权限校验
                admin_cmd = BotCommandObject(
                    command=["确认执行", "取消"],
                    admin=True,  # 要求频道/群管理员权限
                    admin_error_msg="⚠️ 你没有管理员权限，操作已取消",
                )
                result = await s.wait_for(
                    scopes=Scope.USER,
                    command=admin_cmd,
                    timeout=30,
                )

                if "确认" in result.content:
                    await msg.reply("✅ 管理员已确认！敏感操作执行成功")
                else:
                    await msg.reply("❌ 已取消")

            except WaitTimeoutError:
                await msg.reply("⏰ 等待超时")

    @bot.on_command(command="机器人管理")
    async def cmd_bot_admin(
        msg: (
            Model.GuildMessage
            | Model.GroupMessage
            | Model.C2CMessage
            | Model.DirectMessage
        ),
    ) -> None:
        """演示通过 BotCommandObject 使用 is_require_bot_admin 校验"""
        with bot.session.bind(msg) as s:
            await msg.reply("🤖 仅机器人管理员可操作\n请回复「shutdown」或「cancel」：")

            try:
                # 使用 is_require_bot_admin 限制仅机器人管理员可触发
                bot_admin_cmd = BotCommandObject(
                    command=["shutdown", "cancel"],
                    is_require_bot_admin=True,  # 要求机器人管理员权限
                    bot_admin_error_msg="⚠️ 你不是机器人管理员",
                )
                result = await s.wait_for(
                    scopes=Scope.USER,
                    command=bot_admin_cmd,
                    timeout=20,
                )

                if result.content == "shutdown":
                    await msg.reply("🔴 机器人管理员已确认关闭指令")
                else:
                    await msg.reply("已取消")

            except WaitTimeoutError:
                await msg.reply("⏰ 等待超时")

    @bot.on_command(command="正则+艾特")
    async def cmd_regex_at(
        msg: (
            Model.GuildMessage
            | Model.GroupMessage
            | Model.C2CMessage
            | Model.DirectMessage
        ),
    ) -> None:
        """演示通过 BotCommandObject 同时使用 regex 和 at 参数"""
        with bot.session.bind(msg) as s:
            await msg.reply(
                "@我 并发送一个 4 位数字验证码：\n"
                "（需要同时满足 @机器人 和 数字格式要求）"
            )

            try:
                # 组合使用正则匹配 + @机器人要求
                regex_at_cmd = BotCommandObject(
                    regex=re_compile(r"^\d{4}$"),
                    at=True,  # 必须在消息中 @机器人
                )
                result: GuildMessage | GroupMessage | C2CMessage | DirectMessage = (
                    await s.wait_for(
                        scopes=Scope.USER,
                        command=regex_at_cmd,
                        timeout=60,
                    )
                )
                await msg.reply(f"✅ 验证码 {result.content} 验证成功（已 @我）")

            except WaitTimeoutError:
                await msg.reply("⏰ 验证超时")

    @bot.on_command(command="场景限制等待")
    async def cmd_scene_limited(
        msg: (
            Model.GuildMessage
            | Model.GroupMessage
            | Model.C2CMessage
            | Model.DirectMessage
        ),
    ) -> None:
        """演示通过 BotCommandObject 的 valid_scenes 限制有效场景"""
        with bot.session.bind(msg) as s:
            await msg.reply(
                "📍 请在 **频道** 或 **群聊** 中回复「ok」：\n"
                "（单聊中不会响应此等待）"
            )

            try:
                # 限制仅在频道和群聊场景生效，单聊不响应
                scene_cmd = BotCommandObject(
                    command="ok",
                    valid_scenes=CommandValidScenes.GUILD | CommandValidScenes.GROUP,
                )
                result = await s.wait_for(
                    scopes=Scope.USER,
                    command=scene_cmd,
                    timeout=30,
                )
                await msg.reply("✅ 收到！当前为频道或群聊场景")

            except WaitTimeoutError:
                await msg.reply("⏰ 等待超时")

    bot.start()


if __name__ == "__main__":
    main()
