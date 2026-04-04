#!/usr/bin/env python3
"""
EasyBot SDK 示例 07：发送图片方法

展示多种发送图片的方式：

【频道】
1. 通过文件路径发送（file_image 参数）
2. 通过 bytes 发送（file_image 参数）
3. 通过文件对象发送（file_image 参数）
4. 通过网络图片 URL 发送（image 参数）

【群聊/单聊】
1. 通过文件路径发送（upload_media + file_data）
2. 通过 bytes 发送（upload_media + file_data）
3. 通过网络图片 URL 发送（upload_media + url）

注意：
- 频道消息：支持 image/file_image 参数直接发送图片，不支持 upload_media
- 群聊/单聊：不支持 image/file_image 参数，必须使用 upload_media API 上传后发送

运行前请将 app_id 和 app_secret 替换为你的机器人凭证
"""

from easybot import Bot, MessagesModel, Model


def main():
    bot = Bot(
        app_id="your_app_id",
        app_secret="your_app_secret",
    )

    # ==================== 7.1 频道发送图片（支持 file_image/image 参数） ====================
    @bot.on_guild_message
    async def handle_guild_path(msg: Model.GuildMessage):
        """
        频道使用 file_image/image 参数发送图片

        频道支持直接使用 file_image/image 参数发送图片
        不支持 upload_media API（upload_media 仅用于群聊/单聊）
        """

        # ----- 通过文件路径发送（仅频道） -----
        if msg.treated_msg == "图片路径":
            await msg.reply(
                MessagesModel.Message(
                    content="这是通过文件路径发送的本地图片",
                    file_image="./images/cat.png",  # 仅频道支持
                )
            )

        # ----- 通过 bytes 发送（仅频道） -----
        elif msg.treated_msg == "图片bytes":
            with open("./images/dog.png", "rb") as f:
                image_bytes = f.read()

            await msg.reply(
                MessagesModel.Message(
                    content="这是通过 bytes 发送的本地图片",
                    file_image=image_bytes,  # 仅频道支持
                )
            )

        # ----- 通过文件对象发送（仅频道） -----
        elif msg.treated_msg == "图片文件对象":
            with open("./images/bird.png", "rb") as f:
                await msg.reply(
                    MessagesModel.Message(
                        content="这是通过文件对象发送的本地图片",
                        file_image=f,  # 仅频道支持
                    )
                )

        # ----- 通过网络 URL 发送（仅频道） -----
        elif msg.treated_msg == "网络图片":
            await msg.reply(
                MessagesModel.Message(
                    content="这是网络图片",
                    image="https://example.com/image.png",  # 仅频道支持
                )
            )

        # ----- 仅发送图片，无文本（仅频道） -----
        elif msg.treated_msg == "仅图片":
            await msg.reply(
                MessagesModel.Message(
                    file_image="./images/only_image.png"  # 仅频道支持
                )
            )

    # ==================== 7.2 群聊发送图片（必须使用 upload_media） ====================
    @bot.on_group_message
    async def handle_group_image(msg: Model.GroupMessage):
        """
        群聊发送图片

        群聊必须使用 upload_media API 上传后发送
        不支持直接使用 file_image/image 参数
        """

        # ----- 通过文件路径发送 -----
        if msg.treated_msg == "图片":
            try:
                # 步骤1：上传媒体文件
                result = await bot.api.upload_media(
                    file_type=1,  # 1=图片, 2=视频, 3=语音, 4=文件
                    file_data="./images/group_photo.png",  # 本地文件路径
                    group_openid=msg.group_openid,
                    # srv_send_msg=False  # 设为 True 会直接发送，不需要步骤2
                )

                bot.logger.info(f"上传成功，file_info: {result.file_info}")

                # 步骤2：发送消息引用媒体
                await bot.api.send_group_message(
                    group_openid=msg.group_openid,
                    content=MessagesModel.Message(
                        content="群聊图片（本地文件）",
                        media_file_info=result.file_info,  # 使用上传返回的 file_info
                    ),
                    msg_id=msg.id,
                )

            except FileNotFoundError:
                await msg.reply("❌ 图片文件不存在，请检查路径")
            except Exception as e:
                bot.logger.error(f"发送图片失败: {e}")
                await msg.reply("❌ 图片发送失败，请稍后重试")

        # ----- 通过网络 URL 发送 -----
        elif msg.treated_msg == "网络图片":
            try:
                # 步骤1：上传网络图片（通过 URL）
                result = await bot.api.upload_media(
                    file_type=1,  # 1=图片
                    url="https://example.com/image.png",  # 网络图片 URL
                    group_openid=msg.group_openid,
                )

                bot.logger.info(f"上传成功，file_info: {result.file_info}")

                # 步骤2：发送消息引用媒体
                await bot.api.send_group_message(
                    group_openid=msg.group_openid,
                    content=MessagesModel.Message(
                        content="群聊图片（网络URL）", media_file_info=result.file_info
                    ),
                    msg_id=msg.id,
                )

            except Exception as e:
                bot.logger.error(f"发送网络图片失败: {e}")
                await msg.reply("❌ 网络图片发送失败")

        # ----- 通过 bytes 发送 -----
        elif msg.treated_msg == "图片bytes":
            try:
                # 读取图片为 bytes
                with open("./images/group_image.png", "rb") as f:
                    image_bytes = f.read()

                # 步骤1：上传 bytes
                result = await bot.api.upload_media(
                    file_type=1,
                    file_data=image_bytes,  # 直接传入 bytes
                    group_openid=msg.group_openid,
                )

                bot.logger.info(f"上传成功，file_info: {result.file_info}")

                # 步骤2：发送消息
                await bot.api.send_group_message(
                    group_openid=msg.group_openid,
                    content=MessagesModel.Message(
                        content="群聊图片（bytes）", media_file_info=result.file_info
                    ),
                    msg_id=msg.id,
                )

            except Exception as e:
                bot.logger.error(f"发送失败: {e}")
                await msg.reply("❌ 发送失败")

    # ==================== 7.3 单聊发送图片（必须使用 upload_media） ====================
    @bot.on_c2c_message
    async def handle_c2c_image(msg: Model.C2CMessage):
        """
        单聊发送图片

        单聊必须使用 upload_media API 上传后发送
        不支持直接使用 file_image/image 参数
        """

        # ----- 通过文件路径发送 -----
        if msg.treated_msg == "图片":
            try:
                # 步骤1：上传媒体文件
                result = await bot.api.upload_media(
                    file_type=1,  # 1=图片
                    file_data="./images/photo.jpg",  # 本地文件路径
                    user_openid=msg.author.user_openid,
                )

                bot.logger.info(f"上传成功，file_info: {result.file_info}")

                # 步骤2：发送消息引用媒体
                await bot.api.send_c2c_message(
                    openid=msg.author.user_openid,
                    content=MessagesModel.Message(
                        content="私信图片（本地文件）", media_file_info=result.file_info
                    ),
                    msg_id=msg.id,
                )

            except FileNotFoundError:
                await msg.reply("❌ 图片文件不存在，请检查路径")
            except Exception as e:
                bot.logger.error(f"发送图片失败: {e}")
                await msg.reply("❌ 图片发送失败，请稍后重试")

        # ----- 通过网络 URL 发送 -----
        elif msg.treated_msg == "网络图片":
            try:
                # 步骤1：上传网络图片（通过 URL）
                result = await bot.api.upload_media(
                    file_type=1,  # 1=图片
                    url="https://example.com/image.png",  # 网络图片 URL
                    user_openid=msg.author.user_openid,
                )

                bot.logger.info(f"上传成功，file_info: {result.file_info}")

                # 步骤2：发送消息引用媒体
                await bot.api.send_c2c_message(
                    openid=msg.author.user_openid,
                    content=MessagesModel.Message(
                        content="私信图片（网络URL）", media_file_info=result.file_info
                    ),
                    msg_id=msg.id,
                )

            except Exception as e:
                bot.logger.error(f"发送网络图片失败: {e}")
                await msg.reply("❌ 网络图片发送失败")

        # ----- 通过 bytes 发送 -----
        elif msg.treated_msg == "图片bytes":
            try:
                # 读取图片为 bytes
                with open("./images/photo.png", "rb") as f:
                    image_bytes = f.read()

                # 步骤1：上传 bytes
                result = await bot.api.upload_media(
                    file_type=1,
                    file_data=image_bytes,  # 直接传入 bytes
                    user_openid=msg.author.user_openid,
                )

                # 步骤2：发送
                await bot.api.send_c2c_message(
                    openid=msg.author.user_openid,
                    content=MessagesModel.Message(
                        content="私信图片（bytes）", media_file_info=result.file_info
                    ),
                    msg_id=msg.id,
                )

            except Exception as e:
                bot.logger.error(f"发送失败: {e}")
                await msg.reply("❌ 发送失败")

    bot.start()


if __name__ == "__main__":
    main()
