#!/usr/bin/env python3
"""
EasyBot SDK 示例 10：API 使用方法

展示 EasyBot 提供的完整 QQ 官方 API 封装：
- 发送消息（频道、群聊、单聊、私信）
- 频道管理（获取信息、子频道、成员）
- 消息管理（获取、撤回）
- 身份组管理
- 禁言管理
- 互动事件处理
- 富媒体上传

注意：
- 频道消息支持 image/file_image 参数直接发送图片
- 群聊/单聊需要使用 upload_media API 上传后发送

运行前请将 app_id 和 app_secret 替换为你的机器人凭证
"""

from easybot import Bot, MessagesModel, Model


def main() -> None:
    bot: Bot = Bot(
        app_id="your_app_id",
        app_secret="your_app_secret",
    )

    # ==================== 10.1 频道消息 API ====================
    @bot.on_guild_message
    async def handle_guild(msg: Model.GuildMessage) -> None:
        """频道消息处理及 API 调用示例"""

        if msg.treated_msg == "发送消息":
            # 发送频道消息
            result = await bot.api.send_guild_message(
                channel_id=msg.channel_id,
                content="Hello from API!",
                msg_id=msg.id,  # 被动消息，回复原消息
            )
            bot.logger.info(f"消息发送成功，ID: {result.id}")

        # ----- 发送带图片的消息（仅频道支持 image/file_image） -----
        elif msg.treated_msg == "发送图片":
            result = await bot.api.send_guild_message(
                channel_id=msg.channel_id,
                content="看这张图",
                file_image="./images/photo.png",  # 仅频道支持
                msg_id=msg.id,
            )
            bot.logger.info(f"图片消息发送成功，ID: {result.id}")

        elif msg.treated_msg == "发送markdown":
            # 发送 Markdown 消息
            await bot.api.send_guild_message(
                channel_id=msg.channel_id,
                content=MessagesModel.MessageMarkdown(content="# API 发送的 Markdown"),
                msg_id=msg.id,
            )

        elif msg.treated_msg == "获取消息":
            # 获取指定消息
            try:
                message = await bot.api.get_guild_message(
                    channel_id=msg.channel_id, message_id=msg.id
                )
                await msg.reply(f"消息内容：{message.content}")
            except Exception as e:
                bot.logger.error(f"获取消息失败: {e}")

        elif msg.treated_msg == "撤回消息":
            # 撤回消息
            try:
                await bot.api.recall_guild_message(
                    channel_id=msg.channel_id,
                    message_id=msg.id,
                    hidetip=False,  # 是否隐藏提示小灰条
                )
                bot.logger.info("消息已撤回")
            except Exception as e:
                bot.logger.error(f"撤回消息失败: {e}")

    # ==================== 10.2 群聊相关 API ====================
    @bot.on_group_message
    async def handle_group(msg: Model.GroupMessage) -> None:
        """群聊 API 调用示例"""

        if msg.treated_msg == "发送群消息":
            # 发送群聊消息
            await bot.api.send_group_message(
                group_openid=msg.group_openid, content="Hello Group!", msg_id=msg.id
            )

        # ----- 群聊发送图片（必须使用 upload_media） -----
        elif msg.treated_msg == "发送图片":
            try:
                # 步骤1：上传图片
                upload_result = await bot.api.upload_media(
                    file_type=1,  # 1=图片
                    file_data="./images/group_image.png",
                    group_openid=msg.group_openid,
                )

                # 步骤2：发送引用图片的消息
                await bot.api.send_group_message(
                    group_openid=msg.group_openid,
                    content=MessagesModel.Message(
                        content="群聊图片", media_file_info=upload_result.file_info
                    ),
                    msg_id=msg.id,
                )
            except Exception as e:
                bot.logger.error(f"发送图片失败: {e}")
                await msg.reply("❌ 图片发送失败")

        elif msg.treated_msg == "发送embed":
            # 发送 Embed 消息
            await bot.api.send_group_message(
                group_openid=msg.group_openid,
                content=MessagesModel.MessageEmbed(
                    title="群公告", content=["公告内容1", "公告内容2"]
                ),
                msg_id=msg.id,
            )

    # ==================== 10.3 单聊相关 API ====================
    @bot.on_c2c_message
    async def handle_c2c(msg: Model.C2CMessage) -> None:
        """单聊 API 调用示例"""

        if msg.treated_msg == "发送私信":
            # 发送单聊消息
            await bot.api.send_c2c_message(
                openid=msg.author.user_openid, content="Hello!", msg_id=msg.id
            )

        # ----- 单聊发送图片（必须使用 upload_media） -----
        elif msg.treated_msg == "发送图片":
            try:
                # 步骤1：上传图片
                upload_result = await bot.api.upload_media(
                    file_type=1,  # 1=图片
                    file_data="./images/c2c_image.png",
                    user_openid=msg.author.user_openid,
                )

                # 步骤2：发送引用图片的消息
                await bot.api.send_c2c_message(
                    openid=msg.author.user_openid,
                    content=MessagesModel.Message(
                        content="私信图片", media_file_info=upload_result.file_info
                    ),
                    msg_id=msg.id,
                )
            except Exception as e:
                bot.logger.error(f"发送图片失败: {e}")
                await msg.reply("❌ 图片发送失败")

    # ==================== 10.4 频道管理 API ====================
    @bot.on_guild_message
    async def handle_guild_management(msg: Model.GuildMessage) -> None:
        """频道管理 API 示例"""

        if msg.treated_msg == "频道信息":
            # 获取频道信息
            try:
                guild = await bot.api.get_guild(msg.guild_id)
                await msg.reply(
                    f"📋 频道信息：\n"
                    f"- 名称：{guild.name}\n"
                    f"- 拥有者：{guild.owner_id}\n"
                    f"- 成员数：{guild.member_count}"
                )
            except Exception as e:
                bot.logger.error(f"获取频道信息失败: {e}")

        elif msg.treated_msg == "子频道列表":
            # 获取子频道列表
            try:
                channels = await bot.api.get_guild_channels(msg.guild_id)
                channel_list = "\n".join(
                    [
                        f"- {ch.name} (ID: {ch.id}, 类型: {ch.type})"
                        for ch in channels[:10]  # 只显示前10个
                    ]
                )
                await msg.reply(f"📋 子频道列表：\n{channel_list}")
            except Exception as e:
                bot.logger.error(f"获取子频道列表失败: {e}")

        elif msg.treated_msg == "成员列表":
            # 获取成员列表
            try:
                members = await bot.api.get_guild_members(msg.guild_id, limit=20)
                member_list = "\n".join([f"- {m.user.username}" for m in members])
                await msg.reply(f"📋 成员列表（前20）：\n{member_list}")
            except Exception as e:
                bot.logger.error(f"获取成员列表失败: {e}")

    # ==================== 10.5 身份组管理 API ====================
    @bot.on_guild_message
    async def handle_role_management(msg: Model.GuildMessage) -> None:
        """身份组管理 API 示例"""

        if msg.treated_msg == "身份组列表":
            # 获取身份组列表
            try:
                roles_response = await bot.api.get_guild_roles(msg.guild_id)
                roles = roles_response.roles
                role_list = "\n".join(
                    [
                        f"- {role.name} (ID: {role.id}, 颜色: {role.color})"
                        for role in roles
                    ]
                )
                await msg.reply(f"📋 身份组列表：\n{role_list}")
            except Exception as e:
                bot.logger.error(f"获取身份组列表失败: {e}")

    # ==================== 10.6 禁言管理 API ====================
    @bot.on_guild_message
    async def handle_moderation(msg: Model.GuildMessage) -> None:
        """禁言管理 API 示例"""

        if msg.treated_msg == "全员禁言":
            # 全员禁言
            try:
                await bot.api.mute_guild(
                    guild_id=msg.guild_id, mute_seconds=3600  # 禁言1小时
                )
                await msg.reply("✅ 已开启全员禁言（1小时）")
            except Exception as e:
                bot.logger.error(f"全员禁言失败: {e}")

        elif msg.treated_msg == "解除禁言":
            # 取消全员禁言
            try:
                await bot.api.cancel_mute_all(msg.guild_id)
                await msg.reply("✅ 已解除全员禁言")
            except Exception as e:
                bot.logger.error(f"解除禁言失败: {e}")

    # ==================== 10.7 互动事件处理 ====================
    @bot.on_interaction
    async def handle_interaction(msg) -> None:
        """互动按钮点击事件处理"""
        bot.logger.info(f"收到互动事件: {msg.data}")

        try:
            # 回应互动事件（必须回应，否则QQ会提示操作失败）
            await bot.api.respond_interaction(
                interaction_id=msg.id,
                code=0,  # 0=成功, 1=失败, 2=频繁, 3=重复, 4=无权限, 5=仅管理员
            )
            bot.logger.info("互动事件已回应")
        except Exception as e:
            bot.logger.error(f"回应互动事件失败: {e}")

    # ==================== 10.8 其他 API ====================
    @bot.on_guild_message
    async def handle_other_apis(msg: Model.GuildMessage) -> None:
        """其他 API 示例"""

        if msg.treated_msg == "机器人信息":
            # 获取机器人信息
            try:
                me = await bot.api.get_me()
                await msg.reply(
                    f"🤖 机器人信息：\n"
                    f"- ID：{me.id}\n"
                    f"- 名称：{me.username}\n"
                    f"- 头像：{me.avatar}"
                )
            except Exception as e:
                bot.logger.error(f"获取机器人信息失败: {e}")

        elif msg.treated_msg == "在线人数":
            # 获取子频道在线人数
            try:
                online = await bot.api.get_channel_online_nums(msg.channel_id)
                await msg.reply(f"👥 当前在线人数：{online.online_nums}")
            except Exception as e:
                bot.logger.error(f"获取在线人数失败: {e}")

    bot.start()


if __name__ == "__main__":
    main()
