#!/usr/bin/env python3
"""
EasyBot SDK 示例 03：reply() 快速回复消息

展示如何使用 reply() 方法快速回复各种类型的消息：
- 纯文本消息
- 带图片的消息（网络图片、本地图片）- 仅频道支持
- Embed 消息 - 仅频道支持
- Ark 模板消息 - 仅频道支持
- Markdown 消息

注意：
- 频道消息支持 image/file_image 参数直接发送图片
- 群聊/单聊需要使用 upload_media API 上传后发送

运行前请将 app_id 和 app_secret 替换为你的机器人凭证
"""

from easybot import Bot, MessagesModel, Model


def main():
    bot = Bot(
        app_id="your_app_id",
        app_secret="your_app_secret",
    )

    # ==================== 群聊消息回复示例 ====================
    @bot.on_group_message
    async def handle_group(msg: Model.GroupMessage):
        """
        群聊消息处理示例

        群聊使用 v2 API，reply() 方法只支持：
        - 纯文本
        - Markdown 消息
        - Embed 消息
        - Ark 消息
        - 富媒体（需要先调用 upload_media）

        不支持直接使用 image/file_image 参数
        """

        # ----- 3.1 回复纯文本 -----
        if msg.treated_msg == "文本":
            await msg.reply("这是一条纯文本消息")

        # ----- 3.2 回复 Markdown -----
        elif msg.treated_msg == "markdown":
            await msg.reply(
                MessagesModel.MessageMarkdown(content="# 群聊标题\n群聊内容")
            )

        # ----- 3.3 回复 Embed -----
        elif msg.treated_msg == "embed":
            await msg.reply(
                MessagesModel.MessageEmbed(
                    title="群公告", content=["公告内容1", "公告内容2"]
                )
            )

    # ==================== 频道消息回复示例 ====================
    @bot.on_guild_message
    async def handle_guild(msg: Model.GuildMessage):
        """
        频道消息处理示例

        频道消息支持更多类型，包括：
        - 纯文本
        - 网络图片（image 参数）
        - 本地图片（file_image 参数）
        - Embed 消息
        - Ark 模板消息
        - Markdown 消息
        """

        # ----- 3.4 回复纯文本 -----
        if msg.treated_msg == "文本":
            await msg.reply("这是一条纯文本消息")

        # ----- 3.5 回复带网络图片的消息（仅频道） -----
        elif msg.treated_msg == "网络图片":
            await msg.reply(
                MessagesModel.Message(
                    content="看这张图",
                    image="https://example.com/image.png",  # 仅频道支持
                )
            )

        # ----- 3.6 回复带本地图片的消息（仅频道） -----
        elif msg.treated_msg == "本地图片":
            await msg.reply(
                MessagesModel.Message(
                    content="本地图片", file_image="./images/photo.jpg"  # 仅频道支持
                )
            )

        # ----- 3.7 回复 Embed 消息 -----
        elif msg.treated_msg == "embed":
            await msg.reply(
                MessagesModel.MessageEmbed(
                    title="这是标题",
                    content=["第一行内容", "第二行内容", "第三行内容"],
                    image="https://example.com/thumb.png",
                    prompt="通知提示文本",
                )
            )

        # ----- 3.8 回复 Markdown 消息 -----
        elif msg.treated_msg == "markdown":
            await msg.reply(
                MessagesModel.MessageMarkdown(
                    content="# 标题\n## 副标题\n正文内容\n- 列表项1\n- 列表项2"
                )
            )

        # ----- 3.9 回复 Ark 23 模板消息（链接列表） -----
        elif msg.treated_msg == "ark23":
            await msg.reply(
                MessagesModel.MessageArk23(
                    content=["链接1", "链接2"],
                    link=["https://link1.com", "https://link2.com"],
                    desc="描述",
                    prompt="通知",
                )
            )

        # ----- 3.10 回复 Ark 24 模板消息（图文） -----
        elif msg.treated_msg == "ark24":
            await msg.reply(
                MessagesModel.MessageArk24(
                    title="主标题",
                    subtitle="副标题",
                    content="详细描述",
                    link="https://example.com",
                    image="https://example.com/cover.png",
                )
            )

        # ----- 3.11 回复 Ark 37 模板消息（大图） -----
        elif msg.treated_msg == "ark37":
            await msg.reply(
                MessagesModel.MessageArk37(
                    title="标题",
                    content="内容描述",
                    link="https://example.com",
                    image="https://example.com/big_image.png",
                )
            )

        # ----- 3.12 引用回复原消息 -----
        elif msg.treated_msg == "引用":
            await msg.reply(
                MessagesModel.Message(
                    content="这是引用回复", message_reference_id=msg.id  # 引用原消息
                )
            )

    # ==================== 单聊消息回复示例 ====================
    @bot.on_c2c_message
    async def handle_c2c(msg: Model.C2CMessage):
        """
        单聊消息处理示例

        单聊使用 v2 API，与群聊类似：
        - 支持纯文本、Markdown、Embed、Ark
        - 不支持直接使用 image/file_image 参数
        - 发送图片需要先调用 upload_media
        """
        # 单聊中回复简单文本
        if msg.treated_msg == "hello":
            await msg.reply("Hello! 有什么可以帮助你的吗？")

        # 单聊中发送 Markdown
        elif msg.treated_msg == "帮助":
            help_msg = MessagesModel.MessageMarkdown(content="""# 帮助文档

可用指令：
- `hello` - 打招呼
- `帮助` - 显示帮助
- `信息` - 显示信息
""")
            await msg.reply(help_msg)

    bot.start()


if __name__ == "__main__":
    main()
