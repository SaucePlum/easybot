#!/usr/bin/env python3
"""
EasyBot SDK 示例 12：优化后的 wait_for 使用方法

展示 Session 会话管理器和 wait_for 的优化功能：
- 简洁的 wait_for 接口（直接传 command/regex）
- 自定义谓词函数匹配
- 超时回调函数
- 插件命令的动态管理
"""

from re import compile as re_compile

from easybot import Bot, Model, Plugins, Scope, WaitTimeoutError


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

    bot.start()


if __name__ == "__main__":
    main()
