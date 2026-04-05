"""
EasyBot 基础机器人模板
=====================
这是一个最基础的机器人模板，包含：
- 基本配置
- 事件处理器
- 简单命令
- 生命周期事件
"""

import os
from easybot import Bot, Model, CommandValidScenes

bot = Bot(
    app_id=os.getenv("EASYBOT_APP_ID", "your_app_id"),
    app_secret=os.getenv("EASYBOT_APP_SECRET", "your_app_secret"),
    is_debug=True,
)

@bot.on_startup
async def on_startup(event: Model.StartupEvent):
    bot.logger.info("🚀 机器人启动成功")

@bot.on_shutdown
async def on_shutdown(event: Model.ShutdownEvent):
    bot.logger.info("👋 机器人正在关闭")

@bot.before_command(valid_scenes=CommandValidScenes.ALL)
async def log_message(msg: Model.MessageBase):
    if hasattr(msg, 'author'):
        bot.logger.info(f"收到消息: {msg.treated_msg}")

@bot.on_guild_message
async def on_guild(msg: Model.GuildMessage):
    await msg.reply(f"收到频道消息: {msg.treated_msg}")

@bot.on_group_message
async def on_group(msg: Model.GroupMessage):
    await msg.reply(f"收到群聊消息: {msg.treated_msg}")

@bot.on_c2c_message
async def on_c2c(msg: Model.C2CMessage):
    await msg.reply(f"收到私聊消息: {msg.treated_msg}")

@bot.on_command(command="ping", valid_scenes=CommandValidScenes.ALL)
async def ping(msg: Model.MessageBase):
    await msg.reply("pong! 🏓")

@bot.on_command(command="help", valid_scenes=CommandValidScenes.ALL)
async def help_cmd(msg: Model.MessageBase):
    await msg.reply(
        "📖 帮助信息\n"
        "━━━━━━━━━━━━━\n"
        "ping - 测试连接\n"
        "help - 显示帮助"
    )

if __name__ == "__main__":
    bot.start()
