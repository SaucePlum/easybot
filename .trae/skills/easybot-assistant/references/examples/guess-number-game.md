# 猜数字游戏机器人

一个展示会话管理和多轮对话的完整示例。

## 功能概述

- 随机生成 1-100 的目标数字
- 玩家猜测，机器人给出提示（太大/太小）
- 记录猜测次数
- 支持中途退出

## 核心代码

```python
import random
from easybot import Bot, Model, Scope, WaitTimeoutError, CommandValidScenes

bot = Bot(
    app_id="your_app_id",
    app_secret="your_app_secret",
)

@bot.on_command(command="猜数字", valid_scenes=CommandValidScenes.ALL)
async def guess_number_game(msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage):
    """启动猜数字游戏"""
    target = random.randint(1, 100)
    attempts = 0
    max_attempts = 10
    
    with bot.session.bind(msg) as s:
        # 保存游戏状态
        await s.new(
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
            f"我想了一个 1-100 的数字\n"
            f"你有 {max_attempts} 次机会\n"
            f"输入「退出」可以结束游戏"
        )
        
        while True:
            try:
                result = await s.wait_for(
                    scopes=Scope.USER,
                    timeout=60
                )
                
                user_input = result.content.strip()
                
                # 检查退出命令
                if user_input == "退出":
                    await msg.reply(f"游戏结束！答案是 {target}")
                    await s.remove(scope=Scope.USER, key="guess_game")
                    break
                
                # 验证输入
                try:
                    guess = int(user_input)
                    if not 1 <= guess <= 100:
                        await msg.reply("请输入 1-100 之间的数字！")
                        continue
                except ValueError:
                    await msg.reply("请输入有效的数字！")
                    continue
                
                # 更新尝试次数
                session = await s.get(Scope.USER, "guess_game")
                attempts = session.data["attempts"] + 1
                await s.update(Scope.USER, "guess_game", {"attempts": attempts})
                
                # 判断结果
                if guess == target:
                    await msg.reply(
                        f"🎉 恭喜你猜对了！\n"
                        f"答案就是 {target}\n"
                        f"你用了 {attempts} 次猜中"
                    )
                    await s.remove(scope=Scope.USER, key="guess_game")
                    break
                elif attempts >= max_attempts:
                    await msg.reply(
                        f"😢 游戏结束！\n"
                        f"你已经用完了 {max_attempts} 次机会\n"
                        f"正确答案是 {target}"
                    )
                    await s.remove(scope=Scope.USER, key="guess_game")
                    break
                elif guess < target:
                    remaining = max_attempts - attempts
                    await msg.reply(f"📈 太小了！还有 {remaining} 次机会")
                else:
                    remaining = max_attempts - attempts
                    await msg.reply(f"📉 太大了！还有 {remaining} 次机会")
            
            except WaitTimeoutError:
                await msg.reply(f"⏰ 等待超时！答案是 {target}")
                await s.remove(scope=Scope.USER, key="guess_game")
                break

@bot.on_command(command="继续", valid_scenes=CommandValidScenes.ALL)
async def continue_game(msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage):
    """继续未完成的游戏"""
    with bot.session.bind(msg) as s:
        session = await s.get(Scope.USER, "guess_game")
        
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

bot.start()
```

## 关键知识点

1. **会话绑定**：使用 `session.bind(msg)` 自动提取用户标识
2. **状态保存**：使用 `s.new()` 保存游戏状态
3. **多轮对话**：使用 `wait_for()` 等待用户输入
4. **超时处理**：设置 `timeout` 和 `timeout_reply`
5. **状态更新**：使用 `s.update()` 更新游戏进度

## 扩展建议

- 添加难度选择（简单/中等/困难）
- 添加排行榜功能
- 支持多人游戏模式
- 添加提示功能（消耗额外机会）
