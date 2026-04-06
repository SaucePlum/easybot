"""
EasyBot 富媒体消息模板
=====================
这是一个富媒体消息模板，展示：
- Embed 消息
- Markdown 消息
- 按钮键盘
- 交互处理
"""

import os

from easybot import Bot, CommandValidScenes, MessagesModel, Model

bot = Bot(
    app_id=os.getenv("EASYBOT_APP_ID", "your_app_id"),
    app_secret=os.getenv("EASYBOT_APP_SECRET", "your_app_secret"),
)


@bot.on_command(command="embed", valid_scenes=CommandValidScenes.ALL)
async def send_embed(
    msg: (
        Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage
    ),
):
    embed = MessagesModel.MessageEmbed(
        title="📋 信息卡片",
        prompt="这是一个 Embed 消息",
        content=[
            "字段1: 这是第一个字段",
            "字段2: 这是第二个字段",
            "字段3: 这是第三个字段",
        ],
        image="https://example.com/icon.png",
    )
    await msg.reply(embed)


@bot.on_command(command="markdown", valid_scenes=CommandValidScenes.ALL)
async def send_markdown(
    msg: (
        Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage
    ),
):
    md = MessagesModel.MessageMarkdown(content="""# 📖 Markdown 消息

## 功能列表

1. **粗体文本**
2. *斜体文本*
3. `代码块`

---

> 这是一段引用
""")
    await msg.reply(md)


@bot.on_command(command="keyboard", valid_scenes=CommandValidScenes.ALL)
async def send_keyboard(
    msg: (
        Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage
    ),
):
    md = MessagesModel.MessageMarkdown(
        content="请选择操作：",
        keyboard_content={
            "rows": [
                {
                    "buttons": [
                        {
                            "render_data": {"label": "✅ 确认", "style": 1},
                            "action": {"type": 1, "data": "action:confirm"},
                        },
                        {
                            "render_data": {"label": "❌ 取消", "style": 2},
                            "action": {"type": 1, "data": "action:cancel"},
                        },
                    ]
                },
                {
                    "buttons": [
                        {
                            "render_data": {"label": "🔗 访问官网", "style": 2},
                            "action": {"type": 2, "data": "https://example.com"},
                        }
                    ]
                },
            ]
        },
    )
    await msg.reply(md)


@bot.on_interaction
async def handle_interaction(msg: Model.Interaction):
    button_data = msg.data.resolved.button_data

    await bot.api.respond_interaction(interaction_id=msg.id, code=0)

    if button_data == "action:confirm":
        await bot.api.send_c2c_message(
            openid=msg.user_openid, content="✅ 您点击了确认按钮", event_id=msg.id
        )
    elif button_data == "action:cancel":
        await bot.api.send_c2c_message(
            openid=msg.user_openid, content="❌ 您点击了取消按钮", event_id=msg.id
        )


if __name__ == "__main__":
    bot.start()
