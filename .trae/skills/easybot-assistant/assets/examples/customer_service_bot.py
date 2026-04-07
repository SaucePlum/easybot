"""
客服问答机器人
=============
一个展示富媒体消息和交互设计的完整示例。

运行方式：
1. 设置环境变量 EASYBOT_APP_ID 和 EASYBOT_APP_SECRET
2. python customer_service_bot.py
"""

import os

from easybot import (
    Bot,
    CommandValidScenes,
    MessagesModel,
    Model,
    Scope,
    WaitTimeoutError,
)

bot = Bot(
    app_id=os.getenv("EASYBOT_APP_ID", "your_app_id"),
    app_secret=os.getenv("EASYBOT_APP_SECRET", "your_app_secret"),
    is_debug=True,
)

FAQ_DATA = {
    "账号": {
        "q": "账号相关问题",
        "a": "账号问题包括：注册、登录、密码找回、账号安全等。",
        "items": [
            "如何注册账号？",
            "忘记密码怎么办？",
            "如何修改绑定手机？",
            "账号被盗怎么办？",
        ],
    },
    "支付": {
        "q": "支付相关问题",
        "a": "支付问题包括：充值、提现、退款、支付失败等。",
        "items": [
            "支持哪些支付方式？",
            "充值多久到账？",
            "如何申请退款？",
            "支付失败怎么办？",
        ],
    },
    "功能": {
        "q": "功能使用问题",
        "a": "功能问题包括：功能介绍、使用教程、常见操作等。",
        "items": ["如何使用XX功能？", "功能限制说明", "如何开通会员？", "功能更新日志"],
    },
}

ANSWERS = {
    "如何注册账号？": "📱 注册步骤：\n1. 点击「注册」按钮\n2. 输入手机号\n3. 获取验证码\n4. 设置密码\n5. 完成注册",
    "忘记密码怎么办？": "🔑 找回密码：\n1. 点击「忘记密码」\n2. 输入注册手机号\n3. 验证身份\n4. 设置新密码",
    "如何修改绑定手机？": "📱 修改绑定：\n设置 → 账号安全 → 修改手机号 → 验证新手机",
    "账号被盗怎么办？": "🚨 账号被盗：\n1. 立即修改密码\n2. 联系客服冻结账号\n3. 提供身份证明申诉",
    "支持哪些支付方式？": "💳 支持的支付方式：\n• 微信支付\n• 支付宝\n• QQ钱包\n• 银行卡",
    "充值多久到账？": "⏰ 到账时间：\n• 微信/支付宝：即时到账\n• 银行卡：1-3个工作日",
    "如何申请退款？": "💰 退款流程：\n1. 进入「我的订单」\n2. 选择需要退款的订单\n3. 点击「申请退款」\n4. 填写退款原因\n5. 等待审核（1-3天）",
    "支付失败怎么办？": "❌ 支付失败排查：\n1. 检查网络连接\n2. 确认余额充足\n3. 更换支付方式\n4. 联系银行客服",
}


def build_faq_keyboard():
    rows = []
    for cat in FAQ_DATA:
        rows.append(
            {
                "buttons": [
                    {
                        "render_data": {
                            "label": f"📋 {FAQ_DATA[cat]['q']}",
                            "style": 1,
                        },
                        "action": {"type": 1, "data": f"faq:{cat}"},
                    }
                ]
            }
        )
    rows.append(
        {
            "buttons": [
                {
                    "render_data": {"label": "👤 转人工客服", "style": 2},
                    "action": {"type": 1, "data": "human_service"},
                }
            ]
        }
    )
    return rows


def build_question_keyboard(category: str):
    items = FAQ_DATA[category]["items"]
    rows = []
    for item in items:
        rows.append(
            {
                "buttons": [
                    {
                        "render_data": {"label": item[:20], "style": 1},
                        "action": {"type": 1, "data": f"answer:{item}"},
                    }
                ]
            }
        )
    rows.append(
        {
            "buttons": [
                {
                    "render_data": {"label": "🔙 返回分类", "style": 2},
                    "action": {"type": 1, "data": "back_to_menu"},
                }
            ]
        }
    )
    return rows


@bot.on_startup
async def on_startup(event: Model.StartupEvent):
    bot.logger.info("🤖 客服问答机器人已启动")


@bot.on_command(command=["客服", "帮助", "help"], valid_scenes=CommandValidScenes.ALL)
async def customer_service(
    msg: (
        Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage
    ),
):
    embed = MessagesModel.MessageEmbed(
        title="🤖 智能客服",
        prompt="欢迎使用智能客服",
        content=[
            "请选择问题分类",
            "或直接输入您的问题",
        ],
    )
    await msg.reply(embed)

    md = MessagesModel.MessageMarkdown(
        content="请选择：", keyboard_content={"rows": build_faq_keyboard()}
    )
    await msg.reply(md)


@bot.on_interaction
async def handle_interaction(msg: Model.Interaction) -> None:
    resolved = msg.data.resolved if msg.data and msg.data.resolved else None
    if not resolved:
        return
    button_data = resolved.button_data
    await bot.api.respond_interaction(interaction_id=msg.id, code=0)

    if button_data == "back_to_menu":
        embed = MessagesModel.MessageEmbed(
            title="🤖 智能客服", prompt="请选择问题分类", content=["请选择问题分类"]
        )
        await msg.reply(embed)

        md = MessagesModel.MessageMarkdown(
            content="请选择：", keyboard_content={"rows": build_faq_keyboard()}
        )
        await msg.reply(md)

    elif button_data == "human_service":
        embed = MessagesModel.MessageEmbed(
            title="👤 人工客服",
            prompt="正在为您转接人工客服",
            content=[
                "排队中，请稍候...",
                "预计等待时间：2分钟",
            ],
        )
        await msg.reply(embed)

    elif button_data.startswith("faq:"):
        category = button_data.split(":")[1]
        info = FAQ_DATA[category]

        embed = MessagesModel.MessageEmbed(
            title=f"📋 {info['q']}",
            prompt=info["q"],
            content=[
                info["a"],
                "请选择具体问题：",
            ],
        )
        await msg.reply(embed)

        md = MessagesModel.MessageMarkdown(
            content="请选择：",
            keyboard_content={"rows": build_question_keyboard(category)},
        )
        await msg.reply(md)

    elif button_data.startswith("answer:"):
        question = button_data.split(":", 1)[1]
        answer = ANSWERS.get(question, "抱歉，暂无此问题的答案，请联系人工客服。")

        embed = MessagesModel.MessageEmbed(
            title=f"❓ {question}", prompt=question[:20], content=[answer]
        )
        await msg.reply(embed)

        md = MessagesModel.MessageMarkdown(
            content="问题是否解决？",
            keyboard_content={
                "rows": [
                    {
                        "buttons": [
                            {
                                "render_data": {"label": "✅ 问题已解决", "style": 1},
                                "action": {"type": 1, "data": "resolved"},
                            },
                            {
                                "render_data": {"label": "❌ 未解决", "style": 2},
                                "action": {"type": 1, "data": "unresolved"},
                            },
                        ]
                    }
                ]
            },
        )
        await msg.reply(md)

    elif button_data == "resolved":
        embed = MessagesModel.MessageEmbed(
            title="✅ 感谢您的反馈",
            prompt="问题已解决",
            content=[
                "很高兴能帮到您！",
                "如有其他问题，随时联系客服",
            ],
        )
        await msg.reply(embed)

    elif button_data == "unresolved":
        embed = MessagesModel.MessageEmbed(
            title="😔 很抱歉", prompt="问题未解决", content=["建议您转接人工客服"]
        )
        await msg.reply(embed)

        md = MessagesModel.MessageMarkdown(
            content="请选择：", keyboard_content={"rows": build_faq_keyboard()}
        )
        await msg.reply(md)


if __name__ == "__main__":
    bot.start()
