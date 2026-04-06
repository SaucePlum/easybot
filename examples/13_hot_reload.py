#!/usr/bin/env python3
"""
EasyBot SDK 示例 13：插件热重载功能

展示 EasyBot 的插件热重载功能：
- 通过 Bot 实例热重载插件
- 通过 Plugins 类热重载插件
- 动态启用/禁用命令
- 查看插件和命令信息

运行前请将 app_id 和 app_secret 替换为你的机器人凭证
"""

from pathlib import Path

from easybot import Bot, BotAdminManager, Model


def main():
    bot = Bot(
        app_id="your_app_id",
        app_secret="your_app_secret",
        auto_load_plugins=True,
        plugins_dir="plugins",
        plugins_recursive=True,
    )

    admin_mgr = BotAdminManager()
    admin_mgr.bot_admins = ["your_admin_id"]

    @bot.on_startup
    async def on_startup(event):
        bot.logger.info("机器人启动成功！")
        plugins = bot.get_loaded_plugins()
        bot.logger.info(f"已加载 {len(plugins)} 个插件: {plugins}")

    @bot.on_command(
        command="/热重载",
        is_require_bot_admin=True,
        bot_admin_error_msg="此命令仅机器人管理员可用",
    )
    async def reload_cmd(msg: Model.GroupMessage | Model.C2CMessage):
        """热重载指定插件（自动识别插件名或命令名）"""
        arg = msg.treated_msg.strip() if msg.treated_msg else ""

        if not arg:
            loaded = bot.get_loaded_plugins()
            await msg.reply(
                f"用法: /热重载 <插件名或命令名>\n"
                f"示例: /热重载 hot_reload (插件名)\n"
                f"示例: /热重载 ping (命令名)\n"
                f"已加载的插件: {', '.join(loaded) if loaded else '无'}"
            )
            return

        result = bot.reload_plugin(arg)

        if result["success"]:
            await msg.reply(
                f"✅ 插件 {result['module']} 热重载成功\n"
                f"卸载: {result['unloaded']['commands']} 命令\n"
                f"加载: {result['loaded']['commands']} 命令"
            )
        else:
            await msg.reply(f"❌ 热重载失败: {result['error']}")

    @bot.on_command(
        command="/插件列表",
        is_require_bot_admin=True,
        bot_admin_error_msg="此命令仅机器人管理员可用",
    )
    async def list_plugins_cmd(msg: Model.GroupMessage | Model.C2CMessage):
        """列出所有已加载的插件"""
        plugins = bot.get_loaded_plugins()

        if not plugins:
            await msg.reply("当前没有已加载的插件")
            return

        lines = ["📦 已加载插件列表:\n"]
        for plugin_name in plugins:
            cmds = bot.get_plugin_commands(plugin_name)
            preprocessors = bot.get_plugin_preprocessors(plugin_name)
            lines.append(f"• {plugin_name}")
            lines.append(f"  命令: {len(cmds)} 个")
            lines.append(f"  预处理器: {len(preprocessors)} 个")

        await msg.reply("\n".join(lines))

    @bot.on_command(
        command="/命令列表",
        is_require_bot_admin=True,
        bot_admin_error_msg="此命令仅机器人管理员可用",
    )
    async def list_commands_cmd(msg: Model.GroupMessage | Model.C2CMessage):
        """列出所有命令"""
        commands = bot.get_all_commands()

        if not commands:
            await msg.reply("当前没有注册的命令")
            return

        lines = ["📋 已注册命令列表:\n"]
        for cmd in commands:
            status = "✅" if cmd.enabled else "❌"
            if cmd.command:
                cmd_names = ", ".join(cmd.command)
                lines.append(f"{status} {cmd.func.__name__}: {cmd_names}")

        await msg.reply("\n".join(lines))

    @bot.on_command(
        command="/启用",
        is_require_bot_admin=True,
        bot_admin_error_msg="此命令仅机器人管理员可用",
    )
    async def enable_cmd(msg: Model.GroupMessage | Model.C2CMessage):
        """启用指定命令"""
        func_name = msg.treated_msg.strip() if msg.treated_msg else ""

        if not func_name:
            await msg.reply("用法: /启用 <命令函数名>")
            return

        if bot.enable_command(func_name):
            await msg.reply(f"✅ 命令 {func_name} 已启用")
        else:
            await msg.reply(f"❌ 命令不存在: {func_name}")

    @bot.on_command(
        command="/禁用",
        is_require_bot_admin=True,
        bot_admin_error_msg="此命令仅机器人管理员可用",
    )
    async def disable_cmd(msg: Model.GroupMessage | Model.C2CMessage):
        """禁用指定命令"""
        func_name = msg.treated_msg.strip() if msg.treated_msg else ""

        if not func_name:
            await msg.reply("用法: /禁用 <命令函数名>")
            return

        if bot.disable_command(func_name):
            await msg.reply(f"✅ 命令 {func_name} 已禁用")
        else:
            await msg.reply(f"❌ 命令不存在: {func_name}")

    @bot.on_command(
        command="/卸载插件",
        is_require_bot_admin=True,
        bot_admin_error_msg="此命令仅机器人管理员可用",
    )
    async def unload_cmd(msg: Model.GroupMessage | Model.C2CMessage):
        """卸载指定插件"""
        plugin_name = msg.treated_msg.strip() if msg.treated_msg else ""

        if not plugin_name:
            await msg.reply("用法: /卸载插件 <插件名>")
            return

        result = bot.unload_plugin(plugin_name)
        await msg.reply(
            f"✅ 插件 {plugin_name} 已卸载\n"
            f"移除: {result['commands']} 命令, {result['preprocessors']} 预处理器"
        )

    @bot.on_command(
        command="/重载全部",
        is_require_bot_admin=True,
        bot_admin_error_msg="此命令仅机器人管理员可用",
    )
    async def reload_all_cmd(msg: Model.GroupMessage | Model.C2CMessage):
        """热重载所有插件"""
        results = bot.reload_all_plugins()
        success = sum(1 for r in results if r["success"])
        fail = len(results) - success
        await msg.reply(f"🔄 热重载完成: 成功 {success} 个, 失败 {fail} 个")

    @bot.on_command(
        command="/查找命令",
        is_require_bot_admin=True,
        bot_admin_error_msg="此命令仅机器人管理员可用",
    )
    async def find_cmd(msg: Model.GroupMessage | Model.C2CMessage):
        """查找指定命令"""
        func_name = msg.treated_msg.strip() if msg.treated_msg else ""

        if not func_name:
            await msg.reply("用法: /查找命令 <命令函数名>")
            return

        cmd = bot.find_command(func_name)
        if cmd:
            status = "启用" if cmd.enabled else "禁用"
            cmd_names = ", ".join(cmd.command) if cmd.command else "无"
            await msg.reply(
                f"✅ 找到命令: {func_name}\n" f"状态: {status}\n" f"触发词: {cmd_names}"
            )
        else:
            await msg.reply(f"❌ 命令不存在: {func_name}")

    @bot.on_command(
        command="/命令状态",
        is_require_bot_admin=True,
        bot_admin_error_msg="此命令仅机器人管理员可用",
    )
    async def status_cmd(msg: Model.GroupMessage | Model.C2CMessage):
        """检查命令是否启用"""
        func_name = msg.treated_msg.strip() if msg.treated_msg else ""

        if not func_name:
            await msg.reply("用法: /命令状态 <命令函数名>")
            return

        status = bot.is_command_enabled(func_name)
        if status is None:
            await msg.reply(f"❌ 命令不存在: {func_name}")
        elif status:
            await msg.reply(f"✅ 命令 {func_name} 已启用")
        else:
            await msg.reply(f"❌ 命令 {func_name} 已禁用")

    @bot.on_command(
        command="/移除命令",
        is_require_bot_admin=True,
        bot_admin_error_msg="此命令仅机器人管理员可用",
    )
    async def remove_cmd(msg: Model.GroupMessage | Model.C2CMessage):
        """移除指定命令"""
        func_name = msg.treated_msg.strip() if msg.treated_msg else ""

        if not func_name:
            await msg.reply("用法: /移除命令 <命令函数名>")
            return

        if bot.remove_command(func_name):
            await msg.reply(f"✅ 命令 {func_name} 已移除")
        else:
            await msg.reply(f"❌ 命令不存在: {func_name}")

    @bot.on_command(
        command="/清空插件",
        is_require_bot_admin=True,
        bot_admin_error_msg="此命令仅机器人管理员可用",
    )
    async def clear_cmd(msg: Model.GroupMessage | Model.C2CMessage):
        """清空所有插件"""
        result = bot.clear_all_plugins()
        await msg.reply(
            f"✅ 已清空所有插件\n"
            f"移除: {result['commands']} 命令, {result['preprocessors']} 预处理器"
        )

    bot.start()


if __name__ == "__main__":
    main()
