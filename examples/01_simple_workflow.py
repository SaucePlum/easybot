#!/usr/bin/env python3
"""
EasyBot SDK 示例 01：简单工作流

最简单的机器人示例，展示如何：
1. 创建 Bot 实例
2. 注册事件处理器
3. 启动机器人

运行前请将 app_id 和 app_secret 替换为你的机器人凭证
"""

from easybot import Bot, Model


def main():
    # 创建机器人实例（WebSocket 模式，最常用）
    bot = Bot(
        app_id="your_app_id",
        app_secret="your_app_secret",
        is_debug=True,  # 开启调试模式，输出详细日志
    )

    # 处理频道@机器人的消息
    @bot.on_guild_message
    async def handle_guild_message(msg: Model.GuildMessage):
        """当有人在频道@机器人时触发"""
        await msg.reply(f"收到频道消息：{msg.treated_msg}")

    # 处理群聊@机器人的消息
    @bot.on_group_message
    async def handle_group_message(msg: Model.GroupMessage):
        """当有人在群聊@机器人时触发"""
        await msg.reply(f"收到群聊消息：{msg.treated_msg}")

    # 处理单聊消息
    @bot.on_c2c_message
    async def handle_c2c_message(msg: Model.C2CMessage):
        """当有人给机器人发私信时触发"""
        await msg.reply(f"收到私信：{msg.treated_msg}")

    # 启动机器人
    bot.start()


if __name__ == "__main__":
    main()
