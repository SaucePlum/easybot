"""
EasyBot 插件开发模板（方式一：Plugins 装饰器）
===========================================
这是一个插件开发模板，展示：
- 使用 Plugins 装饰器注册命令
- 使用 Plugins 装饰器注册预处理器
- 权限控制
"""

from easybot import CommandValidScenes, Model, Plugins


@Plugins.before_command(valid_scenes=CommandValidScenes.ALL)
async def preprocessor(
    msg: (
        Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage
    ),
):
    return True


@Plugins.on_command(
    command=["plugin_cmd", "插件命令"],
    valid_scenes=CommandValidScenes.ALL,
    is_short_circuit=True,
)
async def plugin_command(
    msg: (
        Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage
    ),
):
    await msg.reply("插件命令执行成功！")


@Plugins.on_command(
    command="admin_cmd",
    valid_scenes=CommandValidScenes.GUILD,
    is_require_admin=True,
    admin_error_msg="此命令需要频道管理员权限",
)
async def admin_command(msg: Model.GuildMessage):
    await msg.reply("管理员命令执行成功！")
