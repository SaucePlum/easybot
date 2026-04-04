#!/usr/bin/env python3
"""
EasyBot SDK 示例 08：插件 & 权限系统使用方法

展示 EasyBot 的插件系统和权限管理功能：
- 基础指令注册
- 多指令别名
- 正则指令
- 限制有效场景
- 权限控制（频道管理员、机器人管理员）
- 运行时管理管理员
- 预处理器

运行前请将 app_id 和 app_secret 替换为你的机器人凭证
"""

from re import compile as re_compile

from easybot import Bot, BotAdminManager, BotCommandObject, CommandValidScenes, Model


def main():
    # 初始化机器人（管理员通过 BotAdminManager 独立管理，支持持久化）
    bot = Bot(
        app_id="your_app_id",
        app_secret="your_app_secret",
    )

    # 推荐方式：直接实例化 BotAdminManager，与 Bot 解耦
    # 数据自动持久化到 sdk_data/bot_admins.yaml，重启不丢失
    admin_mgr = BotAdminManager()

    # 设置默认管理员（合并式，立即持久化）
    admin_mgr.bot_admins = ["admin_user_id_1", "admin_user_id_2"]

    # ==================== 8.1 基础指令注册 ====================
    @bot.on_command(command="帮助")
    async def cmd_help(msg: Model.GroupMessage | Model.C2CMessage | Model.GuildMessage):
        """注册 "帮助" 指令"""
        help_text = """可用指令：
- 帮助 - 显示帮助信息
- hello - 打招呼
- 查询 <数字> - 查询信息
- 群聊专用 - 仅群聊可用
- 私信专用 - 仅单聊可用
- 管理员指令 - 仅管理员可用
- 超管指令 - 仅机器人管理员可用"""
        await msg.reply(help_text)

    # ==================== 8.2 多指令别名 ====================
    @bot.on_command(command=["hello", "你好", "hi", "嗨"])
    async def cmd_hello(
        msg: Model.GroupMessage | Model.C2CMessage | Model.GuildMessage,
    ):
        """多个指令触发同一个功能"""
        await msg.reply("你好！很高兴见到你 😊")

    # ==================== 8.3 正则指令 ====================
    @bot.on_command(regex=re_compile(r"查询 (\d+)"))
    async def cmd_query(
        msg: Model.GroupMessage | Model.C2CMessage | Model.GuildMessage,
    ):
        """使用正则匹配指令

        msg.treated_msg 包含正则匹配的分组结果（元组）
        """
        number = msg.treated_msg[0]  # 获取第一个分组
        await msg.reply(f"查询的号码是：{number}\n正在查询...")

    @bot.on_command(regex=re_compile(r"计算 (\d+) \+ (\d+)"))
    async def cmd_calc(msg: Model.GroupMessage | Model.C2CMessage | Model.GuildMessage):
        """正则匹配多个分组"""
        a, b = int(msg.treated_msg[0]), int(msg.treated_msg[1])
        result = a + b
        await msg.reply(f"{a} + {b} = {result}")

    # ==================== 8.4 限制有效场景 ====================
    @bot.on_command(
        command="群聊专用", valid_scenes=CommandValidScenes.GROUP  # 仅在群聊有效
    )
    async def cmd_group_only(msg: Model.GroupMessage):
        """仅在群聊中可用的指令"""
        await msg.reply("✅ 这条指令只能在群聊中使用")

    @bot.on_command(
        command="私信专用", valid_scenes=CommandValidScenes.C2C  # 仅在单聊有效
    )
    async def cmd_c2c_only(msg: Model.C2CMessage):
        """仅在单聊中可用的指令"""
        await msg.reply("✅ 这条指令只能在单聊中使用")

    @bot.on_command(
        command="全场景",
        valid_scenes=CommandValidScenes.GROUP | CommandValidScenes.C2C,  # 多场景
    )
    async def cmd_multi_scene(msg: Model.GroupMessage | Model.C2CMessage):
        """在多个场景中可用的指令"""
        await msg.reply("✅ 这条指令可以在群聊和单聊中使用")

    @bot.on_command(
        command="频道专用", valid_scenes=CommandValidScenes.GUILD  # 仅在频道有效
    )
    async def cmd_guild_only(msg: Model.GuildMessage):
        """仅在频道中可用的指令"""
        await msg.reply("✅ 这条指令只能在频道中使用")

    # ==================== 8.5 权限控制 ====================
    @bot.on_command(
        command="管理员指令",
        is_require_admin=True,  # 要求频道主或管理员
        admin_error_msg="❌ 只有频道管理员才能使用此指令",
    )
    async def cmd_admin(msg: Model.GuildMessage):
        """仅频道管理员可用的指令"""
        await msg.reply("✅ 管理员你好！这条指令只有频道管理员可以使用")

    @bot.on_command(
        command="超管指令",
        is_require_bot_admin=True,  # 要求机器人管理员
        bot_admin_error_msg="❌ 只有机器人管理员才能使用此指令",
    )
    async def cmd_bot_admin(
        msg: Model.GroupMessage | Model.C2CMessage | Model.GuildMessage,
    ):
        """仅机器人管理员可用的指令"""
        await msg.reply("✅ 机器人管理员你好！这条指令只有机器人管理员可以使用")

    # ==================== 8.6 运行时管理管理员 ====================
    @bot.on_command(command="添加管理员")
    async def cmd_add_admin(
        msg: Model.GroupMessage | Model.C2CMessage | Model.GuildMessage,
    ):
        """动态添加机器人管理员（仅现有管理员可执行）"""
        user_id = (
            msg.author.user_openid
            if hasattr(msg.author, "user_openid")
            else msg.author.id
        )

        # 检查执行者是否为机器人管理员
        if not admin_mgr.is_admin(user_id):
            await msg.reply("❌ 你没有权限执行此操作")
            return

        # 添加新管理员（示例，实际应从消息中解析用户ID）
        new_admin_id = "new_admin_user_id"
        admin_mgr.add_admin(new_admin_id)
        await msg.reply(f"✅ 已添加管理员：{new_admin_id}")

    @bot.on_command(command="移除管理员")
    async def cmd_remove_admin(
        msg: Model.GroupMessage | Model.C2CMessage | Model.GuildMessage,
    ):
        """动态移除机器人管理员"""
        user_id = (
            msg.author.user_openid
            if hasattr(msg.author, "user_openid")
            else msg.author.id
        )

        if not admin_mgr.is_admin(user_id):
            await msg.reply("❌ 你没有权限执行此操作")
            return

        admin_to_remove = "admin_to_remove_id"
        admin_mgr.remove_admin(admin_to_remove)
        await msg.reply(f"✅ 已移除管理员：{admin_to_remove}")

    @bot.on_command(command="检查管理员")
    async def cmd_check_admin(
        msg: Model.GroupMessage | Model.C2CMessage | Model.GuildMessage,
    ):
        """检查当前用户是否为机器人管理员"""
        user_id = (
            msg.author.user_openid
            if hasattr(msg.author, "user_openid")
            else msg.author.id
        )

        if admin_mgr.is_admin(user_id):
            await msg.reply("✅ 你是机器人管理员")
        else:
            await msg.reply("❌ 你不是机器人管理员")

    @bot.on_command(command="管理员列表")
    async def cmd_admin_list(
        msg: Model.GroupMessage | Model.C2CMessage | Model.GuildMessage,
    ):
        """查看所有机器人管理员"""
        user_id = (
            msg.author.user_openid
            if hasattr(msg.author, "user_openid")
            else msg.author.id
        )

        if not admin_mgr.is_admin(user_id):
            await msg.reply("❌ 你没有权限查看管理员列表")
            return

        admins = admin_mgr.get_all_admins()
        admin_list = "\n".join([f"- {admin_id}" for admin_id in admins])
        await msg.reply(f"机器人管理员列表：\n{admin_list}")

    # ==================== 8.7 预处理器 ====================
    @bot.before_command(valid_scenes=CommandValidScenes.ALL)
    async def before_all(
        msg: Model.GroupMessage | Model.C2CMessage | Model.GuildMessage,
    ):
        """
        在所有指令执行前运行

        可用于：
        - 权限检查
        - 日志记录
        - 消息预处理
        - 频率限制
        """
        bot.logger.info(f"[预处理器] 收到指令：{msg.treated_msg}")

        # 示例：记录用户指令使用
        # user_id = msg.author.id if hasattr(msg.author, 'id') else msg.author.user_openid
        # log_command_usage(user_id, msg.treated_msg)

    @bot.before_command(valid_scenes=CommandValidScenes.GROUP)
    async def before_group(msg: Model.GroupMessage):
        """仅在群聊中执行的预处理器"""
        bot.logger.debug(f"[群聊预处理器] 群ID: {msg.group_openid}")

    bot.start()


if __name__ == "__main__":
    main()
