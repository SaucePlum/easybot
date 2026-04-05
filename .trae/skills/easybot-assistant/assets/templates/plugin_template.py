"""
EasyBot 插件开发模板
===================
这是一个插件开发模板，展示：
- 命令注册
- 预处理器
- 权限控制
- 插件注册函数
"""

from easybot import Bot, Plugins, CommandValidScenes, Model

@Plugins.before_command(valid_scenes=CommandValidScenes.ALL)
def preprocessor(msg: Model.MessageBase):
    print(f"[插件预处理] {msg.treated_msg}")

@Plugins.on_command(
    command=["plugin_cmd", "插件命令"],
    valid_scenes=CommandValidScenes.ALL,
    is_short_circuit=True
)
async def plugin_command(msg: Model.MessageBase):
    await msg.reply("插件命令执行成功！")

@Plugins.on_command(
    command="admin_cmd",
    valid_scenes=CommandValidScenes.GUILD,
    is_require_admin=True,
    admin_error_msg="此命令需要频道管理员权限"
)
async def admin_command(msg: Model.GuildMessage):
    await msg.reply("管理员命令执行成功！")

def register(bot: Bot):
    bot.logger.info("示例插件已加载")
    bot.bot_admin_manager.add_admin("default_admin_id")
