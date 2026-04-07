#!/usr/bin/env python3
"""
EasyBot SDK 示例 06：消息构建器使用方法

展示 MessagesModel 提供的各种消息类型构建方法：
- Message: 普通消息（文本、图片、引用）
- MessageEmbed: Embed 消息
- MessageArk23: Ark 23 模板（链接列表）
- MessageArk24: Ark 24 模板（图文）
- MessageArk37: Ark 37 模板（大图）
- MessageMarkdown: Markdown 消息

注意：
- image/file_image 参数仅频道消息支持
- 群聊/单聊需要使用 upload_media API 上传后发送

运行前请将 app_id 和 app_secret 替换为你的机器人凭证
"""

from easybot import Bot, MessagesModel, Model


def main():
    bot = Bot(
        app_id="your_app_id",
        app_secret="your_app_secret",
    )

    @bot.on_group_message
    async def handle_group(msg: Model.GroupMessage):
        """群聊消息处理示例"""

        # ==================== 6.1 普通消息（群聊） ====================

        if msg.treated_msg == "纯文本":
            # 纯文本消息
            text_msg = MessagesModel.Message(content="Hello World")
            await msg.reply(text_msg)

        # 注意：群聊不支持直接使用 image/file_image 参数
        # 需要使用 upload_media API 上传后发送

    @bot.on_guild_message
    async def handle_guild(msg: Model.GuildMessage):
        """频道消息处理示例"""

        # ==================== 6.1 普通消息（频道） ====================

        if msg.treated_msg == "纯文本":
            # 纯文本
            text_msg = MessagesModel.Message(content="Hello World")
            await msg.reply(text_msg)

        # ----- 带网络图片（仅频道支持） -----
        elif msg.treated_msg == "网络图片":
            image_msg = MessagesModel.Message(
                content="看这张图", image="https://example.com/image.png"  # 仅频道支持
            )
            await msg.reply(image_msg)

        # ----- 带本地图片（仅频道支持） -----
        elif msg.treated_msg == "本地图片":
            local_image_msg = MessagesModel.Message(
                content="本地图片", file_image="./images/photo.jpg"  # 仅频道支持
            )
            await msg.reply(local_image_msg)

        # ----- 仅图片（仅频道支持） -----
        elif msg.treated_msg == "仅图片":
            image_only = MessagesModel.Message(
                file_image="./images/only_image.png"  # 仅频道支持
            )
            await msg.reply(image_only)

        # ----- 引用回复 -----
        elif msg.treated_msg == "引用":
            reply_msg = MessagesModel.Message(
                content="这是回复", message_reference_id=msg.id  # 引用原消息
            )
            await msg.reply(reply_msg)

        # ==================== 6.2 Embed 消息 ====================

        elif msg.treated_msg == "embed":
            # Embed 消息 - 适合展示结构化信息
            embed = MessagesModel.MessageEmbed(
                title="📋 信息卡片",
                content=["第一行信息", "第二行信息", "第三行信息"],
                image="https://example.com/thumb.png",  # 缩略图
                prompt="弹窗通知文本",
            )
            await msg.reply(embed)

        # ==================== 6.3 Ark 23 模板（链接列表） ====================

        elif msg.treated_msg == "ark23":
            # Ark 23 - 适合展示链接列表
            ark23 = MessagesModel.MessageArk23(
                content=["官网", "文档", "GitHub"],
                link=[
                    "https://example.com",
                    "https://docs.example.com",
                    "https://github.com/example",
                ],
                desc="相关链接",
                prompt="点击查看链接",
            )
            await msg.reply(ark23)

        # ==================== 6.4 Ark 24 模板（图文） ====================

        elif msg.treated_msg == "ark24":
            # Ark 24 - 适合展示图文信息
            ark24 = MessagesModel.MessageArk24(
                title="文章标题",
                subtitle="副标题",
                content="这是一段详细描述内容...",
                link="https://example.com/article",
                image="https://example.com/cover.png",
            )
            await msg.reply(ark24)

        # ==================== 6.5 Ark 37 模板（大图） ====================

        elif msg.treated_msg == "ark37":
            # Ark 37 - 适合展示大图
            ark37 = MessagesModel.MessageArk37(
                title="大图标题",
                content="图片描述文字",
                link="https://example.com",
                image="https://example.com/big_image.png",
            )
            await msg.reply(ark37)

        # ==================== 6.6 Markdown 消息 ====================

        elif msg.treated_msg == "markdown":
            md_native = MessagesModel.MessageMarkdown(content="""# Markdown 消息示例

支持 **粗体**、*斜体*、`代码块` 和引用回复。

## 引用回复

使用 `reference=True` 参数可以引用原消息：
""")
            await msg.reply(md_native)

        elif msg.treated_msg == "md模板":
            # 模板 Markdown
            md_template = MessagesModel.MessageMarkdown(
                template_id="template_123",
                key_values={
                    "title": "标题内容",
                    "content": "正文内容",
                    "footer": "底部信息",
                },
            )
            await msg.reply(md_template)

    @bot.on_c2c_message
    async def handle_c2c(msg: Model.C2CMessage):
        """单聊消息处理示例"""

        # 单聊中发送简单文本
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

        # 注意：单聊不支持直接使用 image/file_image 参数
        # 需要使用 upload_media API 上传后发送

    bot.start()


if __name__ == "__main__":
    main()
