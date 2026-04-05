"""
猜数字游戏机器人
===============
一个展示会话管理和多轮对话的完整示例。

运行方式：
1. 设置环境变量 EASYBOT_APP_ID 和 EASYBOT_APP_SECRET
2. python guess_number_game.py
"""

import os
import random
from easybot import Bot, Model, Scope, WaitTimeoutError, CommandValidScenes

bot = Bot(
    app_id=os.getenv("EASYBOT_APP_ID", "your_app_id"),
    app_secret=os.getenv("EASYBOT_APP_SECRET", "your_app_secret"),
    is_debug=True,
)

@bot.on_startup
async def on_startup(event: Model.StartupEvent):
    bot.logger.info("🎮 猜数字游戏机器人已启动")

@bot.on_command(command="猜数字", valid_scenes=CommandValidScenes.ALL)
async def guess_number_game(msg: Model.MessageBase):
    target = random.randint(1, 100)
    attempts = 0
    max_attempts = 10
    
    with bot.session.bind(msg) as s:
        s.new(
            scope=Scope.USER,
            key="guess_game",
            data={
                "target": target,
                "attempts": 0,
                "max_attempts": max_attempts,
                "is_active": True
            },
            timeout=300,
            timeout_reply="⏰ 游戏超时，已自动结束"
        )
        
        await msg.reply(
            f"🎮 猜数字游戏开始！\n"
            f"━━━━━━━━━━━━━\n"
            f"我想了一个 1-100 的数字\n"
            f"你有 {max_attempts} 次机会\n"
            f"输入「退出」可以结束游戏"
        )
        
        while True:
            try:
                result = await s.wait_for(scopes=Scope.USER, timeout=60)
                user_input = result.content.strip()
                
                if user_input == "退出":
                    await msg.reply(f"游戏结束！答案是 {target}")
                    s.remove(scope=Scope.USER, key="guess_game")
                    break
                
                try:
                    guess = int(user_input)
                    if not 1 <= guess <= 100:
                        await msg.reply("请输入 1-100 之间的数字！")
                        continue
                except ValueError:
                    await msg.reply("请输入有效的数字！")
                    continue
                
                session = s.get(Scope.USER, "guess_game")
                attempts = session.data["attempts"] + 1
                s.update(Scope.USER, "guess_game", {"attempts": attempts})
                
                if guess == target:
                    await msg.reply(
                        f"🎉 恭喜你猜对了！\n"
                        f"答案就是 {target}\n"
                        f"你用了 {attempts} 次猜中"
                    )
                    s.remove(scope=Scope.USER, key="guess_game")
                    break
                elif attempts >= max_attempts:
                    await msg.reply(
                        f"😢 游戏结束！\n"
                        f"你已经用完了 {max_attempts} 次机会\n"
                        f"正确答案是 {target}"
                    )
                    s.remove(scope=Scope.USER, key="guess_game")
                    break
                elif guess < target:
                    remaining = max_attempts - attempts
                    await msg.reply(f"📈 太小了！还有 {remaining} 次机会")
                else:
                    remaining = max_attempts - attempts
                    await msg.reply(f"📉 太大了！还有 {remaining} 次机会")
            
            except WaitTimeoutError:
                await msg.reply(f"⏰ 等待超时！答案是 {target}")
                s.remove(scope=Scope.USER, key="guess_game")
                break

@bot.on_command(command="继续", valid_scenes=CommandValidScenes.ALL)
async def continue_game(msg: Model.MessageBase):
    with bot.session.bind(msg) as s:
        session = s.get(Scope.USER, "guess_game")
        
        if not session or not session.data.get("is_active"):
            await msg.reply("没有进行中的游戏，发送「猜数字」开始新游戏")
            return
        
        data = session.data
        remaining = data["max_attempts"] - data["attempts"]
        
        await msg.reply(
            f"🎮 游戏继续！\n"
            f"已猜 {data['attempts']} 次\n"
            f"还剩 {remaining} 次机会\n"
            f"请继续猜 1-100 的数字"
        )

@bot.on_command(command="help", valid_scenes=CommandValidScenes.ALL)
async def help_cmd(msg: Model.MessageBase):
    await msg.reply(
        "🎮 猜数字游戏\n"
        "━━━━━━━━━━━━━\n"
        "猜数字 - 开始新游戏\n"
        "继续 - 继续未完成的游戏\n"
        "help - 显示帮助"
    )

if __name__ == "__main__":
    bot.start()
