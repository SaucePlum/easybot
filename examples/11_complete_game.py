#!/usr/bin/env python3
"""
EasyBot SDK 示例 11：完整示例 - 猜数字游戏

综合运用以下功能的完整游戏示例：
- session 会话管理
- wait_for 等待用户输入
- 指令系统
- 正则匹配
- 多步骤流程

游戏规则：
1. 用户发送 "猜数字" 开始游戏
2. 机器人生成 1-100 的随机数
3. 用户输入数字进行猜测
4. 机器人提示大了还是小了
5. 猜对后显示猜测次数

运行前请将 app_id 和 app_secret 替换为你的机器人凭证
"""

from random import randint
from re import compile as re_compile
from time import time

from easybot import Bot, BoundSession, CommandValidScenes, Model, Scope, with_session


def main() -> None:
    bot: Bot = Bot(
        app_id="your_app_id",
        app_secret="your_app_secret",
        is_debug=True,
    )

    # ==================== 开始游戏 ====================
    @bot.on_command(command="猜数字", valid_scenes=CommandValidScenes.C2C)
    @with_session
    async def start_game(msg: Model.C2CMessage, session: BoundSession) -> None:
        """开始猜数字游戏"""
        number = randint(1, 100)

        await session.new(
            scope=Scope.USER,
            key="number_game",
            data={
                "number": number,
                "attempts": 0,
                "min": 1,
                "max": 100,
                "active": True,
                "start_time": time(),
            },
            timeout=300,
            timeout_reply=f"⏰ 游戏超时！答案是 {number}",
        )

        await msg.reply(
            "🎮 猜数字游戏开始！\n"
            "我想了一个 1-100 之间的数字，你来猜！\n"
            "请输入你的猜测（输入 0 结束游戏）："
        )

    @bot.on_command(regex=re_compile(r"^(\d+)$"), valid_scenes=CommandValidScenes.C2C)
    @with_session
    async def guess_number(msg: Model.C2CMessage, session: BoundSession) -> None:
        """处理用户的猜测"""
        game = await session.get(Scope.USER, "number_game")
        if not game or not game.data.get("active"):
            return

        guess = int(msg.treated_msg[0])
        data = game.data
        target = data["number"]

        if guess == 0:
            await session.remove(Scope.USER, key="number_game")
            await msg.reply(f"🛑 游戏已结束，答案是 {target}")
            return

        if guess < 1 or guess > 100:
            await msg.reply("❌ 请输入 1-100 之间的数字")
            return

        data["attempts"] += 1

        if guess == target:
            attempts = data["attempts"]

            if attempts <= 5:
                rating = "🏆 太厉害了！"
            elif attempts <= 10:
                rating = "⭐ 表现不错！"
            else:
                rating = "👍 终于猜对了！"

            await msg.reply(
                f"🎉 {rating}\n"
                f"答案就是 {target}\n"
                f"你一共猜了 {attempts} 次\n\n"
                f"发送「猜数字」开始新游戏"
            )

            await session.remove(Scope.USER, key="number_game")

        elif guess < target:
            data["min"] = max(data["min"], guess + 1)
            await session.update(Scope.USER, "number_game", data)

            await msg.reply(
                f"📈 猜小了！\n"
                f"💡 提示：{data['min']} - {data['max']}\n"
                f"📝 已猜 {data['attempts']} 次"
            )

        else:
            data["max"] = min(data["max"], guess - 1)
            await session.update(Scope.USER, "number_game", data)

            await msg.reply(
                f"📉 猜大了！\n"
                f"💡 提示：{data['min']} - {data['max']}\n"
                f"📝 已猜 {data['attempts']} 次"
            )

    @bot.on_command(command="结束游戏", valid_scenes=CommandValidScenes.C2C)
    @with_session
    async def end_game(msg: Model.C2CMessage, session: BoundSession) -> None:
        """主动结束游戏"""
        game = await session.get(Scope.USER, "number_game")
        if game:
            answer = game.data["number"]
            attempts = game.data["attempts"]
            await session.remove(Scope.USER, key="number_game")

            if attempts > 0:
                await msg.reply(
                    f"🛑 游戏已结束\n" f"答案是 {answer}\n" f"你猜了 {attempts} 次"
                )
            else:
                await msg.reply(f"🛑 游戏已结束，答案是 {answer}")
        else:
            await msg.reply("❌ 没有进行中的游戏")

    @bot.on_command(command="游戏状态", valid_scenes=CommandValidScenes.C2C)
    @with_session
    async def game_status(msg: Model.C2CMessage, session: BoundSession) -> None:
        """查看当前游戏状态"""
        game = await session.get(Scope.USER, "number_game")
        if game and game.data.get("active"):
            data = game.data
            elapsed = int(time() - data.get("start_time", time()))
            remaining = max(0, 300 - elapsed)
            await msg.reply(
                f"🎮 游戏状态：\n"
                f"- 猜测范围：{data['min']} - {data['max']}\n"
                f"- 已猜次数：{data['attempts']}\n"
                f"- 游戏剩余时间：约 {remaining} 秒"
            )
        else:
            await msg.reply("❌ 没有进行中的游戏\n发送「猜数字」开始新游戏")

    # ==================== 游戏帮助 ====================
    @bot.on_command(command="游戏帮助", valid_scenes=CommandValidScenes.C2C)
    async def game_help(msg: Model.C2CMessage):
        """显示游戏帮助"""
        await msg.reply(
            "🎮 猜数字游戏帮助\n"
            "==================\n"
            "「猜数字」- 开始新游戏\n"
            "「0」- 结束当前游戏\n"
            "「结束游戏」- 结束当前游戏\n"
            "「游戏状态」- 查看当前游戏状态\n"
            "「游戏帮助」- 显示此帮助\n"
            "==================\n"
            "规则：\n"
            "1. 机器人会想一个 1-100 的数字\n"
            "2. 你输入数字进行猜测\n"
            "3. 机器人会提示大了还是小了\n"
            "4. 猜对后显示猜测次数\n"
            "5. 游戏限时 5 分钟"
        )

    bot.start()


if __name__ == "__main__":
    main()
