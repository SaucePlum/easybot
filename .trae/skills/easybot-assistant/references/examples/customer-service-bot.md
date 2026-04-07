# 客服问答机器人

一个展示富媒体消息和交互设计的完整示例。

## 功能概述

- 自动回复常见问题
- 富媒体消息展示
- 按钮交互导航
- 人工客服转接

## 核心代码

```python
import os
from easybot import (
    Bot, Model, MessagesModel, CommandValidScenes,
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
        "items": ["如何注册账号？", "忘记密码怎么办？", "如何修改绑定手机？", "账号被盗怎么办？"]
    },
    "支付": {
        "q": "支付相关问题",
        "a": "支付问题包括：充值、提现、退款、支付失败等。",
        "items": ["支持哪些支付方式？", "充值多久到账？", "如何申请退款？", "支付失败怎么办？"]
    },
    "功能": {
        "q": "功能使用问题",
        "a": "功能问题包括：功能介绍、使用教程、常见操作等。",
        "items": ["如何使用XX功能？", "功能限制说明", "如何开通会员？", "功能更新日志"]
    }
}

ANSWERS = {
    "如何注册账号？": "📱 注册步骤：\n1. 点击「注册」按钮\n2. 输入手机号\n3. 获取验证码\n4. 设置密码\n5. 完成注册",
    "忘记密码怎么办？": "🔑 找回密码：\n1. 点击「忘记密码」\n2. 输入注册手机号\n3. 验证身份\n4. 设置新密码",
    # ... 更多答案
}

def build_faq_keyboard():
    """构建FAQ分类按钮"""
    rows = []
    for cat in FAQ_DATA:
        rows.append({
            "buttons": [
                {
                    "render_data": {"label": f"📋 {FAQ_DATA[cat]['q']}", "style": 1},
                    "action": {"type": 1, "data": f"faq:{cat}"}
                }
            ]
        })
    rows.append({
        "buttons": [
            {
                "render_data": {"label": "👤 转人工客服", "style": 2},
                "action": {"type": 1, "data": "human_service"}
            }
        ]
    })
    return rows

@bot.on_command(command=["客服", "帮助", "help"], valid_scenes=CommandValidScenes.ALL)
async def customer_service(msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage):
    # 发送 Embed 消息
    embed = MessagesModel.MessageEmbed(
        title="🤖 智能客服",
        prompt="欢迎使用智能客服",
        content=[
            "请选择问题分类",
            "或直接输入您的问题",
        ]
    )
    await msg.reply(embed)
    
    # 发送按钮键盘
    md = MessagesModel.MessageMarkdown(
        content="请选择：",
        keyboard_content={"rows": build_faq_keyboard()}
    )
    await msg.reply(md)

@bot.on_interaction
async def handle_interaction(msg: Model.Interaction) -> None:
    resolved = msg.data.resolved if msg.data and msg.data.resolved else None
    if not resolved:
        return
    button_data = resolved.button_data
    
    # 回应交互
    await bot.api.respond_interaction(interaction_id=msg.id, code=0)
    
    if button_data.startswith("faq:"):
        category = button_data.split(":")[1]
        info = FAQ_DATA[category]
        
        embed = MessagesModel.MessageEmbed(
            title=f"📋 {info['q']}",
            prompt=info['q'],
            content=[info['a'], "请选择具体问题："]
        )
        await msg.reply(embed)
    
    elif button_data.startswith("answer:"):
        question = button_data.split(":", 1)[1]
        answer = ANSWERS.get(question, "抱歉，暂无此问题的答案，请联系人工客服。")
        
        embed = MessagesModel.MessageEmbed(
            title=f"❓ {question}",
            prompt=question[:20],
            content=[answer]
        )
        await msg.reply(embed)

if __name__ == "__main__":
    bot.start()
```

## 关键知识点

1. **Embed 消息**：使用 `MessageEmbed(title, prompt, content, image)` 构建卡片消息
2. **按钮键盘**：通过 `MessageMarkdown(keyboard_content=...)` 发送按钮
3. **交互处理**：使用 `on_interaction` 处理按钮点击
4. **状态管理**：通过按钮 data 传递状态信息

## 扩展建议

- 接入真实的知识库 API
- 添加智能语义匹配
- 支持图片/视频回复
- 添加满意度评价
- 接入工单系统
