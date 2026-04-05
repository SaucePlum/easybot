# EasyBot 消息构建器完整文档

## 目录

1. [概述](#概述)
2. [普通消息](#普通消息)
3. [Embed 消息](#embed-消息)
4. [Ark 模板消息](#ark-模板消息)
5. [Markdown 消息](#markdown-消息)
6. [按钮键盘](#按钮键盘)
7. [富媒体消息](#富媒体消息)
8. [Builders 工具类](#builders-工具类)

---

## 概述

EasyBot 提供了丰富的消息构建器，支持多种消息格式：

- **Message**：普通文本+图片消息
- **MessageEmbed**：嵌入式卡片消息
- **MessageArk23/24/37**：模板消息
- **MessageMarkdown**：Markdown 格式消息

所有消息构建器都在 `MessagesModel` 类下：

```python
from easybot import MessagesModel
```

---

## 普通消息

### 文本消息

```python
msg = MessagesModel.Message(content="Hello World")

# 发送
await bot.api.send_guild_message(channel_id="xxx", content=msg)
# 或
await msg_obj.reply(msg)
```

### 带图片消息

```python
# 通过 URL
msg = MessagesModel.Message(
    content="图片消息",
    image="https://example.com/image.png"
)

# 通过本地文件路径
msg = MessagesModel.Message(
    content="本地图片",
    file_image="./image.png"
)

# 通过二进制数据
with open("image.png", "rb") as f:
    msg = MessagesModel.Message(
        content="二进制图片",
        file_image=f.read()
    )
```

### 简化写法

```python
# 直接传字符串
await msg_obj.reply("Hello World")

# 字符串 + 图片
await bot.api.send_guild_message(
    channel_id="xxx",
    content="图片",
    image="https://example.com/image.png"
)
```

---

## Embed 消息

Embed 是一种卡片式消息，适合展示结构化信息。

### 基本结构

```python
embed = MessagesModel.MessageEmbed(
    title="标题",
    prompt="提示文本",  # 必填，消息列表显示的文本
    content=[
        "第一行内容",
        "第二行内容",
        "第三行内容",
    ],
    image="https://example.com/image.png"  # 可选图片
)

await msg_obj.reply(embed)
```

### 完整示例

```python
# 用户信息卡片
embed = MessagesModel.MessageEmbed(
    title="用户信息",
    prompt="查看用户详情",
    content=[
        f"昵称: {user.name}",
        f"等级: Lv.{user.level}",
        f"积分: {user.points}",
    ],
    image=user.avatar_url
)

# 商品展示卡片
embed = MessagesModel.MessageEmbed(
    title="商品详情",
    prompt="限时特惠",
    content=[
        f"商品名: {product.name}",
        f"价格: ¥{product.price}",
        f"库存: {product.stock}件",
    ],
    image=product.image_url
)
```

### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | str | 否 | 卡片标题 |
| prompt | str | 否 | 提示文本（消息列表显示） |
| content | list[str] \| str | 否 | 内容行列表或单个字符串 |
| image | str | 否 | 图片 URL |

---

## Ark 模板消息

Ark 模板消息需要预先在 QQ 开放平台创建模板。

### Ark23 模板（文本+链接列表）

```python
ark = MessagesModel.MessageArk23(
    content=["第一行", "第二行", "第三行"],
    link=["https://link1.com", "https://link2.com"],
    desc="描述文本",
    prompt="提示文本"
)

await msg_obj.reply(ark)
```

### Ark24 模板（图文卡片）

```python
ark = MessagesModel.MessageArk24(
    title="标题",
    content="内容描述",
    subtitle="副标题",
    link="https://example.com",
    image="https://example.com/image.png",
    desc="详细描述",
    prompt="提示文本"
)

await msg_obj.reply(ark)
```

### Ark37 模板（大图卡片）

```python
ark = MessagesModel.MessageArk37(
    title="标题",
    content="内容描述",
    link="https://example.com",
    image="https://example.com/image.png",
    prompt="提示文本"
)

await msg_obj.reply(ark)
```

---

## Markdown 消息

### 原生 Markdown

```python
md = MessagesModel.MessageMarkdown(
    content="# 标题\n**粗体** *斜体*\n- 列表项1\n- 列表项2"
)

await msg_obj.reply(md)
```

### 模板 Markdown

使用预定义模板，通过变量替换生成内容：

```python
md = MessagesModel.MessageMarkdown(
    template_id="your_template_id",  # 模板ID（字符串）
    key_values={
        "title": "标题内容",
        "content": ["行1", "行2"],  # 支持列表
    }
)

await msg_obj.reply(md)
```

### Markdown 示例

```python
# 公告消息
md = MessagesModel.MessageMarkdown(
    content="""# 📢 公告

## 更新内容

1. **新功能**: 支持XX功能
2. **优化**: 提升YY性能
3. **修复**: 解决ZZ问题

---
*发布时间: 2024-01-01*"""
)

# 帮助文档
md = MessagesModel.MessageMarkdown(
    content="""# 📖 帮助文档

## 可用命令

| 命令 | 说明 |
|------|------|
| /help | 显示帮助 |
| /ping | 测试连接 |
| /info | 查看信息 |

## 联系方式

如有问题请联系管理员"""
)
```

---

## 按钮键盘

按钮键盘通过 `MessageMarkdown` 的 `keyboard_content` 参数发送。

### 基本按钮

```python
md = MessagesModel.MessageMarkdown(
    content="请选择操作：",
    keyboard_content={
        "rows": [
            {
                "buttons": [
                    {
                        "render_data": {"label": "按钮1", "style": 1},
                        "action": {"type": 1, "data": "callback_data_1"}
                    },
                    {
                        "render_data": {"label": "按钮2", "style": 2},
                        "action": {"type": 1, "data": "callback_data_2"}
                    }
                ]
            }
        ]
    }
)

await msg_obj.reply(md)
```

### 按钮类型

```python
# 回调按钮（点击后触发 on_interaction 事件）
{
    "action": {
        "type": 1,  # 1=回调
        "data": "callback_data",
        "reply": True,  # 是否在消息中显示按钮点击
        "enter": True,  # 是否自动发送
    }
}

# 跳转按钮
{
    "action": {
        "type": 2,  # 2=跳转
        "data": "https://example.com"  # 跳转URL
    }
}
```

### 按钮权限

```python
# 仅特定用户可见
{
    "action": {
        "type": 1,
        "data": "action",
        "permission": {
            "type": 0,  # 0=指定用户
            "specify_user_ids": ["user_id_1", "user_id_2"]
        }
    }
}

# 仅管理员可见
{
    "action": {
        "type": 1,
        "data": "action",
        "permission": {"type": 1}  # 1=管理员
    }
}

# 所有人可见
{
    "action": {
        "type": 1,
        "data": "action",
        "permission": {"type": 2}  # 2=所有人
    }
}
```

### 处理按钮点击

```python
@bot.on_interaction
async def handle_interaction(msg):
    button_data = msg.data.resolved.button_data
    button_id = msg.data.resolved.button_id
    
    # 回应交互
    await bot.api.respond_interaction(interaction_id=msg.id, code=0)
    
    # 处理逻辑
    if button_data == "callback_data_1":
        await bot.api.send_c2c_message(
            openid=msg.user_openid,
            content="你点击了按钮1",
            event_id=msg.id
        )
```

### 完整示例

```python
# 菜单选择
md = MessagesModel.MessageMarkdown(
    content="📋 请选择操作：",
    keyboard_content={
        "rows": [
            {
                "buttons": [
                    {
                        "render_data": {"label": "📋 查看列表", "style": 1},
                        "action": {"type": 1, "data": "action:list"}
                    },
                    {
                        "render_data": {"label": "➕ 添加项目", "style": 1},
                        "action": {"type": 1, "data": "action:add"}
                    }
                ]
            },
            {
                "buttons": [
                    {
                        "render_data": {"label": "⚙️ 设置", "style": 2},
                        "action": {"type": 1, "data": "action:settings"}
                    },
                    {
                        "render_data": {"label": "❓ 帮助", "style": 2},
                        "action": {"type": 1, "data": "action:help"}
                    }
                ]
            }
        ]
    }
)
```

---

## 富媒体消息

### 上传媒体文件

```python
# 上传图片
result = await bot.api.upload_media(
    file_type=1,  # 1=图片, 2=视频, 3=语音, 4=文件
    file_data="./image.png",
    user_openid="user_openid"
)

# result.file_info 用于发送
```

### 发送富媒体消息

```python
# 使用 Message 发送
msg = MessagesModel.Message(
    content="图片消息",
    media_file_info=result.file_info
)

await bot.api.send_c2c_message(
    openid="user_openid",
    content=msg,
    event_id="event_id"
)
```

---

## Builders 工具类

`Builders` 类提供了帖子内容构建器：

### ThreadContentBuilder - 帖子内容构建器

```python
from easybot import Builders

builder = Builders.ThreadContentBuilder()
builder.add_text_paragraph("第一段文字")
builder.add_image_paragraph("https://example.com/image.png")
builder.add_text_paragraph("第二段文字", bold=True)

content = builder.build()

await bot.api.create_thread(
    channel_id="forum_channel_id",
    title="帖子标题",
    content=content
)
```

### ParagraphBuilder - 段落构建器

```python
builder = Builders.ParagraphBuilder()
builder.add_text("普通文本")
builder.add_text("粗体文本", bold=True)
builder.add_image("https://example.com/image.png")

paragraph = builder.build()
```

---

## 消息类型对照表

| 类型 | 用途 | 支持场景 |
|------|------|----------|
| Message | 普通文本/图片 | 全部 |
| MessageEmbed | 卡片消息 | 频道、群聊、单聊 |
| MessageArk23 | 文本+链接列表 | 频道、群聊、单聊 |
| MessageArk24 | 图文卡片 | 频道、群聊、单聊 |
| MessageArk37 | 大图卡片 | 频道、群聊、单聊 |
| MessageMarkdown | Markdown+按钮 | 频道、群聊、单聊 |
