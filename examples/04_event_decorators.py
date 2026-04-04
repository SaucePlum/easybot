#!/usr/bin/env python3
"""
EasyBot SDK 示例 04：事件装饰器的使用方法

展示 EasyBot 提供的各种事件装饰器，用于订阅不同类型的事件：
- 消息事件（频道、群聊、单聊、私信）
- 成员事件（加入、退出、更新）
- 频道/群聊生命周期事件
- 互动事件（按钮点击、表情表态）
- 批量订阅事件

运行前请将 app_id 和 app_secret 替换为你的机器人凭证
"""

from easybot import Bot, Model


def main() -> None:
    bot: Bot = Bot(
        app_id="your_app_id",
        app_secret="your_app_secret",
        is_private=False,  # 公域机器人（默认）
    )

    # ==================== 4.1 消息事件 ====================

    @bot.on_guild_message
    async def on_guild_message(msg: Model.GuildMessage) -> None:
        """频道@机器人消息（公域机器人）"""
        bot.logger.info(f"[频道消息] {msg.author.username}: {msg.treated_msg}")
        await msg.reply(f"收到频道消息：{msg.treated_msg}")

    @bot.on_guild_full_message
    async def on_full_message(msg: Model.GuildMessage) -> None:
        """频道全量消息（仅私域机器人可用）"""
        bot.logger.info(f"[全量消息] {msg.author.username}: {msg.treated_msg}")

    @bot.on_group_message
    async def on_group_message(msg: Model.GroupMessage) -> None:
        """群聊@机器人消息"""
        bot.logger.info(f"[群聊消息] {msg.group_openid}: {msg.treated_msg}")
        await msg.reply(f"收到群聊消息：{msg.treated_msg}")

    @bot.on_c2c_message
    async def on_c2c_message(msg: Model.C2CMessage) -> None:
        """单聊消息"""
        bot.logger.info(f"[单聊消息] {msg.author.user_openid}: {msg.treated_msg}")
        await msg.reply(f"收到私信：{msg.treated_msg}")

    @bot.on_direct_message
    async def on_direct_message(msg: Model.DirectMessage) -> None:
        """频道私信消息"""
        bot.logger.info(f"[私信] {msg.author.username}: {msg.treated_msg}")
        await msg.reply(f"收到私信：{msg.treated_msg}")

    # ==================== 4.2 成员事件 ====================

    @bot.on_guild_member_add
    async def on_member_add(msg) -> None:
        """成员加入频道"""
        bot.logger.info(f"[成员加入] {msg.user.username} 加入了频道")

    @bot.on_guild_member_remove
    async def on_member_remove(msg) -> None:
        """成员退出频道"""
        bot.logger.info(f"[成员退出] {msg.user.username} 退出了频道")

    @bot.on_guild_member_update
    async def on_member_update(msg) -> None:
        """成员信息更新"""
        bot.logger.info(f"[成员更新] {msg.user.username} 信息已更新")

    # ==================== 4.3 频道生命周期事件 ====================

    @bot.on_guild_create
    async def on_guild_create(msg) -> None:
        """机器人加入频道"""
        bot.logger.info(f"[加入频道] 机器人加入了频道：{msg.name}")

    @bot.on_guild_delete
    async def on_guild_delete(msg) -> None:
        """机器人退出频道"""
        bot.logger.info(f"[退出频道] 机器人退出了频道：{msg.id}")

    @bot.on_channel_create
    async def on_channel_create(msg) -> None:
        """子频道创建"""
        bot.logger.info(f"[子频道创建] {msg.name}")

    @bot.on_channel_delete
    async def on_channel_delete(msg) -> None:
        """子频道删除"""
        bot.logger.info(f"[子频道删除] {msg.id}")

    # ==================== 4.4 群聊生命周期事件 ====================

    @bot.on_group_add
    async def on_group_add(msg) -> None:
        """机器人被加入群聊"""
        bot.logger.info(f"[加入群聊] 机器人被加入群聊：{msg.group_openid}")
        # 可以发送欢迎消息
        # await bot.api.send_group_message(
        #     group_openid=msg.group_openid,
        #     content="大家好！我是机器人，请多关照！"
        # )

    @bot.on_group_delete
    async def on_group_delete(msg) -> None:
        """机器人被移出群聊"""
        bot.logger.info(f"[移出群聊] 机器人被移出群聊：{msg.group_openid}")

    @bot.on_friend_add
    async def on_friend_add(msg) -> None:
        """添加好友"""
        bot.logger.info(f"[添加好友] {msg.user_openid}")

    @bot.on_friend_delete
    async def on_friend_delete(msg) -> None:
        """删除好友"""
        bot.logger.info(f"[删除好友] {msg.user_openid}")

    # ==================== 4.5 互动事件 ====================

    @bot.on_interaction
    async def on_interaction(msg) -> None:
        """互动按钮点击事件"""
        bot.logger.info(f"[按钮点击] {msg.data}")
        # 回应互动事件
        await bot.api.respond_interaction(interaction_id=msg.id, code=0)

    @bot.on_reaction_add
    async def on_reaction_add(msg) -> None:
        """表情表态添加"""
        bot.logger.info(f"[表情添加] {msg.emoji.name}")

    @bot.on_reaction_remove
    async def on_reaction_remove(msg) -> None:
        """表情表态移除"""
        bot.logger.info(f"[表情移除] {msg.emoji.name}")

    # ==================== 4.6 消息删除事件 ====================

    @bot.on_public_message_delete
    async def on_public_message_delete(msg) -> None:
        """公域消息删除"""
        bot.logger.info(f"[消息删除] 消息ID：{msg.message.id}")

    @bot.on_direct_message_delete
    async def on_direct_message_delete(msg) -> None:
        """私信消息删除"""
        bot.logger.info(f"[私信删除] 消息ID：{msg.message.id}")

    # ==================== 4.7 批量订阅事件 ====================

    @bot.on_default_public_events
    async def on_default_public(event) -> None:
        """
        订阅公域机器人默认事件集合
        包含：GUILDS、PUBLIC_GUILD_MESSAGES、GROUP_AND_C2C_EVENT、OPEN_FORUM_EVENT
        """
        bot.logger.info(f"[默认公域事件] {event.event_type}")

    @bot.on_all_intent_events
    async def on_all_events(event) -> None:
        """
        订阅所有事件
        注意：部分事件需要私域权限才能接收
        """
        bot.logger.debug(f"[所有事件] {event.event_type}")

    bot.start()


if __name__ == "__main__":
    main()
