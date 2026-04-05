"""
EasyBot 会话交互模板
===================
这是一个会话交互模板，展示：
- 会话绑定
- wait_for 多轮对话
- 状态管理
- 超时处理
"""

import os
from easybot import Bot, Model, Scope, WaitTimeoutError, CommandValidScenes

bot = Bot(
    app_id=os.getenv("EASYBOT_APP_ID", "your_app_id"),
    app_secret=os.getenv("EASYBOT_APP_SECRET", "your_app_secret"),
)

@bot.on_command(command="表单", valid_scenes=CommandValidScenes.ALL)
async def form_demo(msg: Model.MessageBase):
    with bot.session.bind(msg) as s:
        answers = {}
        
        questions = [
            ("name", "请输入您的姓名："),
            ("age", "请输入您的年龄："),
            ("email", "请输入您的邮箱："),
        ]
        
        for key, question in questions:
            await msg.reply(question)
            
            try:
                result = await s.wait_for(
                    scopes=Scope.USER,
                    timeout=60
                )
                answers[key] = result.content.strip()
            except WaitTimeoutError:
                await msg.reply("⏰ 等待超时，表单已取消")
                return
        
        await msg.reply(
            f"✅ 表单提交成功！\n"
            f"━━━━━━━━━━━━━\n"
            f"姓名: {answers['name']}\n"
            f"年龄: {answers['age']}\n"
            f"邮箱: {answers['email']}"
        )

@bot.on_command(command="确认", valid_scenes=CommandValidScenes.ALL)
async def confirm_demo(msg: Model.MessageBase):
    with bot.session.bind(msg) as s:
        await msg.reply("确定要执行此操作吗？回复「是」或「否」")
        
        try:
            result = await s.wait_for(
                scopes=Scope.USER,
                command=["是", "否"],
                timeout=30
            )
            
            if "是" in result.content:
                await msg.reply("✅ 操作已执行")
            else:
                await msg.reply("❌ 操作已取消")
        
        except WaitTimeoutError:
            await msg.reply("⏰ 等待超时，操作已取消")

if __name__ == "__main__":
    bot.start()
