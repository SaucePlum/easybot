#!/usr/bin/env python3
"""
EasyBot SDK 示例 09：session, wait_for 使用方法

展示 Session 会话管理和 wait_for 等待用户输入功能：
- 基础 session 使用（bind 上下文管理器）
- 使用 with_session 装饰器简化
- wait_for 等待用户输入
- 复杂的多步骤流程
- 不同作用域的 session

运行前请将 app_id 和 app_secret 替换为你的机器人凭证
"""

from re import compile as re_compile

from easybot import (
    Bot,
    CommandValidScenes,
    Model,
    Scope,
    WaitError,
    WaitTimeoutError,
    with_session,
)


def main() -> None:
    bot: Bot = Bot(
        app_id="your_app_id",
        app_secret="your_app_secret",
    )

    # ==================== 9.1 基础 session 使用 ====================
    @bot.on_command(command="注册")
    async def cmd_register(
        msg: Model.GroupMessage | Model.C2CMessage | Model.GuildMessage,
    ) -> None:
        """简单的注册流程示例"""
        with bot.session.bind(msg) as s:
            # 创建会话，设置60秒超时
            s.new(
                scope=Scope.USER,  # 用户级别
                key="register_flow",
                data={"step": 1, "name": None, "age": None},
                timeout=60,
                timeout_reply="⏰ 注册超时，请重新开始",
            )
            await msg.reply("📝 注册流程开始\n请输入你的名字：")

    @bot.on_command(command="查看注册")
    async def cmd_check_register(
        msg: Model.GroupMessage | Model.C2CMessage | Model.GuildMessage,
    ) -> None:
        """查看当前注册状态"""
        with bot.session.bind(msg) as s:
            session = s.get(Scope.USER, "register_flow")
            if session:
                await msg.reply(
                    f"📋 注册进度：\n"
                    f"- 当前步骤：{session.data['step']}\n"
                    f"- 姓名：{session.data.get('name', '未填写')}\n"
                    f"- 年龄：{session.data.get('age', '未填写')}"
                )
            else:
                await msg.reply("❌ 你没有进行中的注册流程")

    # ==================== 9.2 使用 with_session 装饰器简化 ====================
    @bot.on_command(command="游戏")
    @with_session
    async def cmd_game(
        msg: Model.GroupMessage | Model.C2CMessage | Model.GuildMessage, session=None
    ) -> None:
        """使用装饰器自动注入 session"""
        # 创建游戏会话
        session.new(
            scope=Scope.USER,
            key="game_session",
            data={"score": 0, "level": 1, "lives": 3},
            timeout=300,  # 5分钟超时
            timeout_reply="⏰ 游戏已超时结束",
        )
        await msg.reply("🎮 游戏开始！\n当前等级：1\n生命值：3")

    @bot.on_command(command="查看游戏")
    @with_session
    async def cmd_check_game(
        msg: Model.GroupMessage | Model.C2CMessage | Model.GuildMessage, session=None
    ) -> None:
        """查看游戏状态"""
        game = session.get(Scope.USER, "game_session")
        if game:
            data = game.data
            await msg.reply(
                f"🎮 游戏状态：\n"
                f"- 等级：{data['level']}\n"
                f"- 分数：{data['score']}\n"
                f"- 生命值：{data['lives']}"
            )
        else:
            await msg.reply("❌ 没有进行中的游戏")

    # ==================== 9.3 wait_for 等待用户输入 ====================
    @bot.on_command(command="确认")
    async def cmd_confirm(
        msg: Model.GroupMessage | Model.C2CMessage | Model.GuildMessage,
    ) -> None:
        """等待用户确认"""
        with bot.session.bind(msg) as s:
            await msg.reply("请回复「确认」或「取消」：")

            try:
                # 等待用户回复特定指令，30秒超时
                result = await s.wait_for(
                    scopes=Scope.USER,
                    command=["确认", "取消"],
                    timeout=30,
                )

                if "确认" in result.content:
                    await msg.reply("✅ 已确认！操作执行成功")
                else:
                    await msg.reply("❌ 已取消")

            except WaitTimeoutError:
                await msg.reply("⏰ 等待超时，操作自动取消")
            except WaitError as e:
                await msg.reply(f"❌ 发生错误：{e}")

    @bot.on_command(command="选择")
    async def cmd_choose(
        msg: Model.GroupMessage | Model.C2CMessage | Model.GuildMessage,
    ) -> None:
        """等待用户选择"""
        with bot.session.bind(msg) as s:
            await msg.reply("请选择一项：\n1. 选项一\n2. 选项二\n3. 选项三")

            try:
                result = await s.wait_for(
                    scopes=Scope.USER,
                    command=["1", "2", "3"],
                    timeout=60,
                )

                choice = result.content
                options = {"1": "选项一", "2": "选项二", "3": "选项三"}
                await msg.reply(f"✅ 你选择了：{options.get(choice)}")

            except WaitTimeoutError:
                await msg.reply("⏰ 选择超时")

    # ==================== 9.4 复杂的多步骤流程 ====================
    @bot.on_command(command="问卷调查")
    async def cmd_survey(
        msg: Model.GroupMessage | Model.C2CMessage | Model.GuildMessage,
    ) -> None:
        """多步骤问卷调查示例"""
        with bot.session.bind(msg) as s:
            await msg.reply("📋 欢迎使用问卷调查！\n请输入你的年龄：")

            try:
                # 步骤1：等待年龄输入（正则匹配数字）
                age_msg = await s.wait_for(
                    scopes=Scope.USER,
                    command=re_compile(r"^(\d+)$"),
                    timeout=60,
                )
                age = int(age_msg.treated_msg[0])

                if age < 1 or age > 150:
                    await msg.reply("❌ 年龄输入不合法，请重新开始")
                    return

                await msg.reply(f"你的年龄是 {age} 岁。\n请输入你的性别（男/女）：")

                # 步骤2：等待性别输入
                gender_msg = await s.wait_for(
                    scopes=Scope.USER,
                    command=["男", "女"],
                    timeout=60,
                )
                gender = gender_msg.content

                await msg.reply("请输入你的兴趣爱好（用逗号分隔）：")

                # 步骤3：等待兴趣爱好
                hobby_msg = await s.wait_for(
                    scopes=Scope.USER,
                    timeout=60,
                    # 不指定 command，接受任何输入
                )
                hobbies = hobby_msg.content

                # 保存调查数据到 session
                s.new(
                    scope=Scope.USER,
                    key="survey_data",
                    data={
                        "age": age,
                        "gender": gender,
                        "hobbies": hobbies,
                        "completed": True,
                    },
                    timeout=3600,  # 1小时过期
                )

                await msg.reply(
                    f"✅ 调查完成！\n"
                    f"- 年龄：{age}\n"
                    f"- 性别：{gender}\n"
                    f"- 兴趣爱好：{hobbies}\n\n"
                    f"感谢你的参与！"
                )

            except WaitTimeoutError:
                await msg.reply("⏰ 调查超时，请重新开始")

    @bot.on_command(command="查看调查")
    async def cmd_check_survey(
        msg: Model.GroupMessage | Model.C2CMessage | Model.GuildMessage,
    ) -> None:
        """查看调查结果"""
        with bot.session.bind(msg) as s:
            survey = s.get(Scope.USER, "survey_data")
            if survey and survey.data.get("completed"):
                data = survey.data
                await msg.reply(
                    f"📋 你的调查信息：\n"
                    f"- 年龄：{data['age']}\n"
                    f"- 性别：{data['gender']}\n"
                    f"- 兴趣爱好：{data['hobbies']}"
                )
            else:
                await msg.reply("❌ 你还没有完成调查")

    # ==================== 9.5 不同作用域的 session ====================
    @bot.on_command(command="群设置")
    async def cmd_group_settings(msg: Model.GroupMessage) -> None:
        """群聊级别的设置"""
        with bot.session.bind(msg) as s:
            # Scope.GROUP 表示这个设置是整个群聊共享的
            s.new(
                scope=Scope.GROUP,
                key="group_config",
                data={
                    "welcome_msg": "欢迎新人！请遵守群规~",
                    "auto_kick": False,
                    "slow_mode": 0,
                },
            )
            await msg.reply("✅ 群设置已保存（群聊级别）")

    @bot.on_command(command="查看群设置")
    async def cmd_check_group_settings(msg: Model.GroupMessage) -> None:
        """查看群聊设置"""
        with bot.session.bind(msg) as s:
            config = s.get(Scope.GROUP, "group_config")
            if config:
                data = config.data
                await msg.reply(
                    f"📋 群设置：\n"
                    f"- 欢迎消息：{data.get('welcome_msg')}\n"
                    f"- 自动踢人：{'开启' if data.get('auto_kick') else '关闭'}\n"
                    f"- 慢速模式：{data.get('slow_mode', 0)}秒"
                )
            else:
                await msg.reply("❌ 没有群设置")

    @bot.on_command(command="频道设置", valid_scenes=CommandValidScenes.GUILD)
    async def cmd_channel_settings(msg: Model.GuildMessage) -> None:
        """频道级别的设置"""
        with bot.session.bind(msg) as s:
            # Scope.CHANNEL 表示这个设置是当前子频道共享的
            s.new(
                scope=Scope.CHANNEL,
                key="channel_config",
                data={"slow_mode": 30, "announcement": "频道公告"},
            )
            await msg.reply("✅ 频道设置已保存（子频道级别）")

    @bot.on_command(command="全局设置")
    @with_session
    async def cmd_global_settings(
        msg: Model.GroupMessage | Model.C2CMessage | Model.GuildMessage, session=None
    ) -> None:
        """全局级别的设置"""
        # Scope.GLOBAL 表示这个设置是全局共享的
        session.new(
            scope=Scope.GLOBAL,
            key="global_config",
            data={"maintenance_mode": False, "version": "1.0.0"},
        )
        await msg.reply("✅ 全局设置已保存（全局级别）")

    bot.start()


if __name__ == "__main__":
    main()
