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

EasyBot 提供了丰富的消息内容表达方式，支持多种消息格式：

- **普通消息参数**：直接通过发送接口 / `reply()` 传 `content`、`image`、`file_image`、`media_file_info`
- **MessageEmbed**：嵌入式卡片消息
- **MessageArk23/24/37**：模板消息
- **MessageMarkdown**：Markdown 格式消息

所有消息构建器都在 `MessagesModel` 类下：

```python
from easybot import MessagesModel
```

---

## 普通消息参数

### 文本消息

```python
await bot.api.send_guild_message(channel_id="xxx", content="Hello World")
# 或
await msg.reply("Hello World")
```

### 带图片消息

```python
# 通过 URL
await bot.api.send_guild_message(
    channel_id="xxx",
    content="图片消息",
    image="https://example.com/image.png",
)

# 通过本地文件路径
await bot.api.send_guild_message(
    channel_id="xxx",
    content="本地图片",
    file_image="./image.png",
)

# 通过二进制数据
with open("image.png", "rb") as f:
    await bot.api.send_guild_message(
        channel_id="xxx",
        content="二进制图片",
        file_image=f.read(),
    )
```

### Message 构建器

使用 `MessagesModel.Message` 构建器创建消息对象：

```python
from easybot import MessagesModel

# 文本消息
msg = MessagesModel.Message(content="Hello World")

# 文本 + 图片
msg = MessagesModel.Message(
    content="图片消息",
    image="https://example.com/image.png"
)

# 文本 + 本地图片
msg = MessagesModel.Message(
    content="本地图片",
    file_image="./image.png"
)

# 富媒体消息（群聊/单聊 v2 API）
msg = MessagesModel.Message(
    content="富媒体消息",
    media_file_info="file_info_string"
)

await bot.api.send_guild_message(channel_id="xxx", **msg.build())
```

**Message 参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| content | str \| int \| float | 否 | 消息文本内容 |
| image | str | 否 | 图片 URL（网络图片） |
| file_image | bytes \| BinaryIO \| str | 否 | 本地图片（bytes、文件对象或文件路径） |
| media_file_info | str | 否 | 富媒体文件信息（群聊/单聊 v2 API） |

**msg_type 属性**：

Message 构建器提供 `msg_type` 属性，用于标识消息类型：

- `msg_type = 0`：普通消息（默认）
- `msg_type = 7`：富媒体消息（使用 media_file_info 时）

```python
msg = MessagesModel.Message(content="普通消息")
print(msg.msg_type)  # 0

msg = MessagesModel.Message(media_file_info="file_info")
print(msg.msg_type)  # 7
```

### 简化写法

```python
# 直接传字符串
await msg.reply("Hello World")

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
    prompt="提示文本",  # 建议填写，消息列表显示的文本
    content=[
        "第一行内容",
        "第二行内容",
        "第三行内容",
    ],
    image="https://example.com/image.png"  # 可选图片
)

await msg.reply(embed)
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

await msg.reply(ark)
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

await msg.reply(ark)
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

await msg.reply(ark)
```

---

## Markdown 消息

### 原生 Markdown

```python
md = MessagesModel.MessageMarkdown(
    content="# 标题\n**粗体** *斜体*\n- 列表项1\n- 列表项2"
)

await msg.reply(md)
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

await msg.reply(md)
```

### 带 Keyboard 模板的消息

使用预定义的 Keyboard 模板：

```python
md = MessagesModel.MessageMarkdown(
    content="# 标题",
    keyboard_id="your_keyboard_template_id"  # Keyboard 模板 ID
)

await msg.reply(md)
```

### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| content | str | 否* | 原生 Markdown 内容（与 template_id 二选一） |
| template_id | str | 否* | Markdown 模板 ID（模板方式时必须提供 key_values） |
| key_values | dict \| list | 否 | 模板参数，格式 `{key: value}` 或 `[{"key": "k", "values": ["v"]}]` |
| keyboard_id | str | 否 | Keyboard 模板 ID（与 keyboard_content 二选一） |
| keyboard_content | dict | 否 | 原生 Keyboard 内容（与 keyboard_id 二选一） |

**注意**：`content` 和 `template_id` 必须二选一。

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

await msg.reply(md)
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
        "type": 0,  # 0=跳转
        "data": "https://example.com"  # 跳转URL或客户端可识别的小程序 scheme
    }
}

# 指令按钮（自动在输入框插入 @bot + data）
{
    "action": {
        "type": 2,  # 2=指令
        "data": "/help"
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
from easybot import Model

@bot.on_interaction
async def handle_interaction(msg: Model.Interaction) -> None:
    resolved = msg.data.resolved if msg.data and msg.data.resolved else None
    if not resolved:
        return
    button_data = resolved.button_data
    button_id = resolved.button_id
    
    # 回应交互
    await bot.api.respond_interaction(interaction_id=msg.id, code=0)
    
    # 处理逻辑
    if button_data == "callback_data_1":
        await msg.reply("你点击了按钮1")
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
# 直接通过 media_file_info 发送
await msg.reply(
    "图片消息",
    media_file_info=result.file_info,
)
```

---

## Builders 工具类

`Builders` 类提供了帖子内容构建器：

### ThreadContentBuilder - 帖子内容构建器

用于构建 ThreadContent 对象，简化 JSON 格式发帖。支持添加文本段落、图片段落和自定义段落。

```python
from easybot import Builders, Model

builder = Builders.ThreadContentBuilder()
builder.add_text_paragraph("第一段文字")
builder.add_image_paragraph("https://example.com/image.png")
builder.add_text_paragraph("第二段文字", bold=True, alignment=Model.Alignment.ALIGNMENT_CENTER)

content = builder.build()

await bot.api.create_thread(
    channel_id="forum_channel_id",
    title="帖子标题",
    content=content
)
```

**方法说明**：

| 方法 | 参数 | 说明 |
|------|------|------|
| `add_paragraph(paragraph)` | paragraph: ThreadContentParagraph 或 ParagraphBuilder | 添加段落对象或构建器 |
| `add_text_paragraph(text, bold=False, italic=False, underline=False, alignment=0)` | text: 文本内容<br>bold: 是否加粗<br>italic: 是否斜体<br>underline: 是否下划线<br>alignment: 对齐方式 | 添加纯文本段落（快捷方法） |
| `add_image_paragraph(third_url, width_percent=1.0, alignment=0)` | third_url: 图片链接<br>width_percent: 宽度比例<br>alignment: 对齐方式 | 添加图片段落（快捷方法） |
| `build()` | - | 构建 ThreadContent 对象 |

**高级用法 - 混合段落**：

```python
from easybot import Builders, Model

# 使用 ParagraphBuilder 创建复杂段落
paragraph_builder = Builders.ParagraphBuilder()
paragraph_builder.add_text("这是标题", bold=True)
paragraph_builder.add_text(" - ")
paragraph_builder.add_url("https://example.com", desc="点击查看")
paragraph_builder.set_alignment(Model.Alignment.ALIGNMENT_CENTER)

# 添加到帖子内容
content_builder = Builders.ThreadContentBuilder()
content_builder.add_paragraph(paragraph_builder)
content_builder.add_image_paragraph("https://example.com/image.png")
content_builder.add_text_paragraph("这是正文内容")

content = content_builder.build()
```

### ParagraphBuilder - 段落构建器

用于构建 ThreadContentParagraph 对象，提供流畅的 API。可以混合添加文本、图片、视频、链接等元素。

```python
from easybot import Builders

builder = Builders.ParagraphBuilder()
builder.add_text("普通文本")
builder.add_text("粗体文本", bold=True)
builder.add_text("斜体下划线", italic=True, underline=True)
builder.add_image("https://example.com/image.png")
builder.add_video("https://example.com/video.mp4")
builder.add_url("https://example.com", desc="访问链接")
builder.set_alignment(1)  # 居中对齐

paragraph = builder.build()
```

**方法说明**：

| 方法 | 参数 | 说明 |
|------|------|------|
| `add_text(text, bold=False, italic=False, underline=False)` | text: 文本内容<br>bold: 是否加粗<br>italic: 是否斜体<br>underline: 是否下划线 | 添加文本元素 |
| `add_image(third_url, width_percent=1.0)` | third_url: 图片链接<br>width_percent: 宽度比例（0.0-1.0） | 添加图片元素 |
| `add_video(third_url)` | third_url: 视频链接 | 添加视频元素 |
| `add_url(url, desc="")` | url: 链接地址<br>desc: 链接描述 | 添加链接元素 |
| `set_alignment(alignment)` | alignment: 对齐方式（使用 Alignment 枚举） | 设置段落对齐方式 |
| `build()` | - | 构建 ThreadContentParagraph 对象 |

**对齐方式枚举（Alignment）**：

```python
from easybot import Model

Model.Alignment.ALIGNMENT_LEFT    # 0 - 左对齐（默认）
Model.Alignment.ALIGNMENT_MIDDLE  # 1 - 居中对齐
Model.Alignment.ALIGNMENT_RIGHT   # 2 - 右对齐
```

### TextChainBuilder - 文本交互构建器

用于构建文本消息中的交互元素，如@用户、指令操作、跳转子频道等。

```python
from easybot import Builders

# @用户
at_text = Builders.TextChainBuilder.at_user("123456789")

# @全体成员
at_all = Builders.TextChainBuilder.at_everyone()

# 回车指令（点击后直接发送）
cmd = Builders.TextChainBuilder.cmd_enter("/help")

# 参数指令（点击后插入输入框）
cmd = Builders.TextChainBuilder.cmd_input("/search", show="点击搜索")

# 跳转子频道
link = Builders.TextChainBuilder.channel_link("123456789")

# 系统表情
emoji = Builders.TextChainBuilder.emoji("123")
```

**组合使用示例**：

```python
# 组合多个交互元素
content = (
    Builders.TextChainBuilder.at_user("123456789") +
    " 欢迎加入！\n" +
    Builders.TextChainBuilder.cmd_enter("/help") +
    " 查看帮助"
)

await msg.reply(content)
```

**可用方法**：

| 方法 | 说明 | 支持场景 |
|------|------|---------|
| `at_user(user_id)` | @指定用户 | 群聊、文字子频道 |
| `at_everyone()` | @全体成员 | 仅文字子频道 |
| `cmd_enter(text)` | 回车指令（直接发送） | 仅 Markdown 消息 |
| `cmd_input(text, show, reference)` | 参数指令（插入输入框） | 仅 Markdown 消息 |
| `channel_link(channel_id)` | 跳转子频道 | 仅频道 |
| `emoji(emoji_id)` | 系统表情 | 仅频道 |

---

## 消息类型对照表

| 类型 | msg_type | 用途 | 支持场景 |
|------|----------|------|----------|
| Message | 0 (普通) / 7 (富媒体) | 普通文本/图片 | 全部 |
| MessageEmbed | 4 | 卡片消息 | 频道、群聊、单聊 |
| MessageArk23 | 3 | 文本+链接列表 | 频道、群聊、单聊 |
| MessageArk24 | 3 | 图文卡片 | 频道、群聊、单聊 |
| MessageArk37 | 3 | 大图卡片 | 频道、群聊、单聊 |
| MessageMarkdown | 2 | Markdown+按钮 | 频道、群聊、单聊 |

**msg_type 说明**：

所有消息构建器都提供 `msg_type` 属性，用于标识消息类型：

```python
from easybot import MessagesModel

# 普通消息
msg = MessagesModel.Message(content="文本")
print(msg.msg_type)  # 0

# Embed 消息
embed = MessagesModel.MessageEmbed(title="标题")
print(embed.msg_type)  # 4

# Ark 消息
ark = MessagesModel.MessageArk23(content=["文本"], link=["链接"])
print(ark.msg_type)  # 3

# Markdown 消息
md = MessagesModel.MessageMarkdown(content="# 标题")
print(md.msg_type)  # 2
```
