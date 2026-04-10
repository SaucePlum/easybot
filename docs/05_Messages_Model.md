# Messages Model — 消息构建器

本章介绍 EasyBot SDK 中的消息构建器，用于构建发送消息的内容。

---

## 一、概述

**模块**: `easybot.builders`  
**导入**: `from easybot import MessagesModel`

MessagesModel 提供多种消息构建器，用于构造不同类型的消息内容。

### 1.1 消息类型选择指南

根据实际需求选择合适的消息类型：

| 需求 | 推荐类型 | 说明 |
|------|---------|------|
| 简单文本回复 | `str` | 直接通过发送接口传入 |
| 文本 + 图片 | `Message` 或接口参数 `image` / `file_image` | 普通消息既可直接传参，也可显式构建 |
| 结构化信息展示 | `MessageEmbed` | 清晰的字段布局 |
| 导航/链接列表 | `MessageArk23` | 多行可点击链接 |
| 推广/资讯卡片 | `MessageArk24/37` | 视觉吸引力强 |
| 富文本格式化 | `MessageMarkdown` | 支持标题/列表/加粗等 |

### 1.2 消息构建器列表

| 构建器 | 类名 | msg_type | 适用场景 |
|--------|------|----------|---------|
| 普通消息 | `Message` | 0 / 7 | 文本、图片、富媒体 |
| Embed 卡片 | `MessageEmbed` | 4 | 结构化信息展示 |
| Ark 23 链接列表 | `MessageArk23` | 3 | 多行链接列表 |
| Ark 24 图文卡片 | `MessageArk24` | 3 | 标题+描述+缩略图 |
| Ark 37 大图卡片 | `MessageArk37` | 3 | 大图展示模板 |
| Markdown | `MessageMarkdown` | 2 | 富文本格式消息 |

### 1.3 官方接口视角速查

| 场景 | 发送接口 | 常用消息类型 | 图片/富媒体方式 | 特别限制 |
|------|----------|--------------|-----------------|----------|
| 频道消息 | `send_guild_message()` | `str/Message/Embed/Ark/Markdown` | `image` 或 `file_image` | 支持引用回复 |
| 频道私信 | `send_direct_message()` | `str/Message/Embed/Ark/Markdown` | `image` 或 `file_image` | 支持引用回复 |
| 群聊 v2 | `send_group_message()` | `str/Message/Embed/Ark/Markdown` | `media_file_info` | 普通消息路径必须有文本内容，SDK 自动补 `msg_type` |
| QQ 单聊 v2 | `send_c2c_message()` | `str/Message/Embed/Ark/Markdown` | `media_file_info` | SDK 自动补 `msg_type`，`is_wakeup` 仅此场景可用 |

| 普通消息参数形态 | 官方字段方向 | 推荐场景 |
|------------------|--------------|----------|
| `content="文本"` | `content + msg_type=0` | 四种发送场景 |
| `image="https://..."` | 顶级 `image` | 频道消息、频道私信 |
| `file_image=...` | multipart `file_image` | 频道消息、频道私信 |
| `media_file_info=...` | `media.file_info + msg_type=7` | 群聊 v2、QQ 单聊 v2 |
| `is_wakeup=True` | 顶级 `is_wakeup` | 仅 QQ 单聊 v2 |

---

## 二、Message — 普通消息

`MessagesModel.Message` 是普通消息构建器，用于构建文本、图片和富媒体消息体。普通消息也支持直接通过发送接口或 `reply()` 平铺传参，SDK 内部会统一归一为 `MessagesModel.Message`。

### 2.1 构造参数

```python
MessagesModel.Message(
    content: str | int | float | None = None,
    image: str | None = None,
    file_image: bytes | BinaryIO | str | None = None,
    media_file_info: str | None = None,
)
```

### 2.2 使用示例

**纯文本**：

```python
msg = MessagesModel.Message(content="Hello World!")
await bot.api.send_guild_message(channel_id="xxx", content=msg)
```

**文本 + 网络图片**：

```python
msg = MessagesModel.Message(
    content="看看这张图",
    image="https://example.com/image.png",
)
await bot.api.send_guild_message(channel_id="xxx", content=msg)
```

**文本 + 本地图片**：

```python
# 方式1：文件路径
msg = MessagesModel.Message(content="本地图片", file_image="./photo.png")
await bot.api.send_guild_message(channel_id="xxx", content=msg)

# 方式2：bytes 数据
msg = MessagesModel.Message(content="Bytes图片", file_image=image_bytes)
await bot.api.send_guild_message(channel_id="xxx", content=msg)
```
**引用回复**：

```python
# 方式一：使用 reply() 的 reference 参数（推荐）
# 适用于所有场景（频道/群聊/单聊/私信）
await msg.reply("我同意你的观点", reference=True)

# 方式二：主动发送时使用拆分引用参数
await bot.api.send_guild_message(
    channel_id="xxx",
    content="我同意你的观点",
    message_reference_id=msg.id,
)
```

**单聊互动召回消息**：

```python
await bot.api.send_c2c_message(openid="xxx", content="回来看看我吧", is_wakeup=True)
```

### 2.3 注意事项

**富媒体（群聊/单聊）**：

```python
# 先上传图片获取 file_info
file_info = await bot.api.upload_media(
    file_type=1,  # 1=图片
    file_data="./image.png",
    group_openid="xxx",
)

# 发送富媒体消息
msg = MessagesModel.Message(
    content="图片消息",
    media_file_info=file_info.file_info,
)
await bot.api.send_group_message(group_openid="xxx", content=msg)
```

**注意事项**：
- `MessagesModel.Message` 中 `media_file_info` 与 `image`/`file_image` 互斥
- `file_image` 仅适用于**频道消息**；群聊/单聊需使用 `media_file_info`
- `is_wakeup` 仅适用于 **QQ 单聊 v2 接口**，且官方要求与 `msg_id`、`event_id` 互斥
- 同时传入 `image` 和 `file_image` 时，当前 SDK 实现会优先使用 `image`
- 频道消息接口支持 `image` 或 `file_image` 发送图片；其中 `file_image` 属于 multipart/form-data 上传方式

---

## 三、MessageEmbed — Embed 卡片

用于发送结构化的信息卡片，包含标题、内容行列表、缩略图和通知文本。

### 3.1 构造参数

```python
MessagesModel.MessageEmbed(
    title: str | None = None,           # 卡片标题
    content: list[str] | str | None = None,  # 内容行（每项一行）
    image: str | None = None,            # 缩略图 URL
    prompt: str | None = None,           # 消息弹窗通知文本
)
```

### 3.2 使用示例

**基础卡片**：

```python
embed = MessagesModel.MessageEmbed(
    title="🎮 服务器状态",
    content=[
        "在线人数: 128",
        "延迟: 25ms",
        "运行时间: 3天",
    ],
    prompt="点击查看详情",
)
await bot.api.send_guild_message(channel_id="xxx", content=embed)
```

**带缩略图的卡片**：

```python
embed = MessagesModel.MessageEmbed(
    title="📢 公告",
    content=["系统维护通知", "时间: 今晚 22:00-23:00"],
    image="https://example.com/notice.png",
    prompt="维护公告",
)
```

**单行内容**：

```python
embed = MessagesModel.MessageEmbed(title="提示", content="这是一条单行内容")
```

---

## 四、MessageArk23 — 链接列表模板

适用于展示多行链接列表的场景，如「快捷导航」「相关推荐」等。

### 4.1 构造参数

```python
MessagesModel.MessageArk23(
    content: list[str],          # 显示文本列表（每项一行）
    link: list[str],             # 对应的跳转链接 URL 列表
    desc: str | None = None,     # 描述文本
    prompt: str | None = None,    # 通知文本
)
```

**约束**: `content` 和 `link` 的长度必须一致。

### 4.2 使用示例

```python
ark = MessagesModel.MessageArk23(
    content=["GitHub 主页", "API 文档", "Issue 跟踪"],
    link=[
        "https://github.com/SaucePlum/easybot",
        "https://docs.easybot.dev",
        "https://github.com/SaucePlum/easybot/issues",
    ],
    desc="快速链接",
    prompt="查看文档",
)
await bot.api.send_guild_message(channel_id="xxx", content=ark)
```

---

## 五、MessageArk24 — 图文卡片模板

适用于展示带标题、描述和缩略图的信息卡片。

### 5.1 构造参数

```python
MessagesModel.MessageArk24(
    title: str | None = None,       # 主标题
    content: str | None = None,      # 详情描述
    subtitle: str | None = None,     # 副标题
    link: str | None = None,         # 点击跳转链接
    image: str | None = None,        # 缩略图 URL
    desc: str | None = None,         # 描述文本
    prompt: str | None = None,       # 通知文本
)
```

### 5.2 使用示例

```python
ark = MessagesModel.MessageArk24(
    title="EasyBot SDK 发布 v0.1.0",
    content="全新重构的 QQ 机器人开发框架，支持 WebSocket/Webhook/远程 Webhook。",
    subtitle="轻量 · 易用 · 稳定",
    link="https://github.com/SaucePlum/easybot",
    image="https://example.com/cover.png",
    prompt="了解更多",
)
await bot.api.send_guild_message(channel_id="xxx", content=ark)
```

---

## 六、MessageArk37 — 大图卡片模板

适用于以大图为主的展示场景，如活动海报、封面推广等。

### 6.1 构造参数

```python
MessagesModel.MessageArk37(
    title: str | None = None,       # 标题
    content: str | None = None,      # 内容描述
    link: str | None = None,         # 跳转链接
    image: str | None = None,        # 大图 URL
    prompt: str | None = None,       # 通知文本
)
```

### 6.2 使用示例

```python
ark = MessagesModel.MessageArk37(
    title="🎉 新年活动",
    content="参与活动赢取丰厚奖励！",
    link="https://example.com/event",
    image="https://example.com/poster.png",
    prompt="立即参与",
)
await bot.api.send_guild_message(channel_id="xxx", content=ark)
```

---

## 七、MessageMarkdown — Markdown 消息

支持原生 Markdown 内容和模板两种方式，可搭配 Keyboard 按钮实现交互式消息。

### 7.1 构造参数

```python
MessagesModel.MessageMarkdown(
    content: str | None = None,                          # 原生 Markdown 内容
    template_id: str | None = None,                       # 模板 ID（与 content 二选一）
    key_values: dict[str, str | list[str]] | list[dict] | None = None,  # 模板参数（模板方式必填）
    keyboard_id: str | None = None,                       # Keyboard 模板 ID（与 keyboard_content 二选一）
    keyboard_content: dict | None = None,                  # 自定义 Keyboard 内容（与 keyboard_id 二选一）
)
```

**约束**：
- `content` 和 `template_id` 不可同时存在
- 必须提供 `content` 或 `template_id` 其中之一
- 使用 `template_id` 时必须提供 `key_values`
- `keyboard_id` 和 `keyboard_content` 应二选一

### 7.2 原生 Markdown

```python
md = MessagesModel.MessageMarkdown(content="""# 📋 今日任务清单

- [x] 完成 API 文档编写
- [x] 修复 #42 号 Bug
- [ ] 编写单元测试
- [ ] 性能优化

**截止日期**: 2026-01-15""")

await bot.api.send_guild_message(channel_id="xxx", content=md)
```

### 7.3 模板 Markdown

```python
md = MessagesModel.MessageMarkdown(
    template_id="模板ID从QQ开放平台获取",
    key_values={
        "title": "公告标题",
        "content": ["第一段内容", "第二段内容"],
        "footer": "— EasyBot 团队",
    },
)
await bot.api.send_guild_message(channel_id="xxx", content=md)
```

### 7.4 Markdown + Keyboard 按钮

`keyboard_content` 中的按钮动作 `action.type` 说明：

| type | 类型 | data 说明 |
|------|------|----------|
| 0 | 跳转按钮 | `http(s)` 或客户端可识别的小程序 scheme |
| 1 | 回调按钮 | 回调后台接口，`data` 原样透传给后台 |
| 2 | 指令按钮 | 自动在输入框插入 `@bot` + `data` |

```python
# 使用 Keyboard 模板
md = MessagesModel.MessageMarkdown(
    content="# 请选择操作",
    keyboard_id="键盘模板ID_123",
)

# 使用自定义 Keyboard
md = MessagesModel.MessageMarkdown(
    content="# 操作菜单",
    keyboard_content={
        "rows": [
            {
                "buttons": [
                    {
                        "render_data": {"label": "确认"},
                        "action": {"type": 1, "data": "confirm", "reply": True}
                    },
                    {
                        "render_data": {"label": "取消"},
                        "action": {"type": 1, "data": "cancel", "reply": True}
                    },
                ]
            }
        ]
    },
)
```

---

## 八、论坛内容构建器

用于构建 JSON 格式发帖内容（`format=4`）。

**模块**: `easybot.builders`  
**导入**: `from easybot import Builders`

### 8.1 ThreadContentBuilder — 帖子内容构建器

```python
from easybot import Builders

# 构建帖子内容
content = (Builders.ThreadContentBuilder()
    .add_text_paragraph("第一段文字")
    .add_image_paragraph("https://example.com/image.png")
    .add_text_paragraph("第二段文字", bold=True)
    .build())

# 发帖
await bot.api.create_thread(channel_id="xxx", title="帖子标题", content=content)
```

### 8.2 ParagraphBuilder — 段落构建器

用于构建更复杂的段落内容：

```python
# 复杂段落（混合内容）
paragraph = (Builders.ParagraphBuilder()
    .add_text("文字", bold=True)
    .add_url("https://example.com", "链接描述")
    .add_image("https://example.com/image.png")
    .set_alignment(Model.Alignment.ALIGNMENT_CENTER)
    .build())

content = (Builders.ThreadContentBuilder()
    .add_paragraph(paragraph)
    .build())
```

### 8.3 可用方法

**段落元素方法**：

| 方法 | 说明 |
|------|------|
| `add_text(text, bold, italic, underline)` | 添加文本 |
| `add_image(third_url, width_percent)` | 添加图片 |
| `add_video(third_url)` | 添加视频 |
| `add_url(url, desc)` | 添加链接 |
| `set_alignment(alignment)` | 设置对齐方式 |

**帖子内容构建方法**：

| 方法 | 说明 |
|------|------|
| `add_paragraph(paragraph)` | 添加段落对象 |
| `add_text_paragraph(text, ...)` | 快捷添加文本段落 |
| `add_image_paragraph(third_url, ...)` | 快捷添加图片段落 |

---

## 九、TextChainBuilder — 文本交互构建器

用于构建文本消息中的交互元素，如@用户、指令操作、跳转子频道等。

**模块**: `easybot.builders`  
**导入**: `from easybot import Builders`

### 9.1 基本使用

```python
from easybot import Builders

# @用户
content = Builders.TextChainBuilder.at_user("123456789")

# @全体成员
content = Builders.TextChainBuilder.at_everyone()

# 回车指令（点击后直接发送）
content = Builders.TextChainBuilder.cmd_enter("/help")

# 参数指令（点击后插入输入框）
content = Builders.TextChainBuilder.cmd_input("/search", show="点击搜索")

# 跳转子频道
content = Builders.TextChainBuilder.channel_link("123456789")

# 系统表情
content = Builders.TextChainBuilder.emoji("123")
```

### 9.2 组合使用

可以将多个交互元素拼接在一起：

```python
from easybot import Builders

# 组合使用
content = (
    Builders.TextChainBuilder.at_user("123456789") +
    " 欢迎加入！\n" +
    Builders.TextChainBuilder.cmd_enter("/help") +
    " 查看帮助"
)

await msg.reply(content)
```

### 9.3 可用方法

| 方法 | 说明 | 支持场景 |
|------|------|---------|
| `at_user(user_id)` | @指定用户 | 群聊、文字子频道 |
| `at_everyone()` | @全体成员 | 仅文字子频道 |
| `cmd_enter(text)` | 回车指令（直接发送） | 仅 Markdown 消息 |
| `cmd_input(text, show, reference)` | 参数指令（插入输入框） | 仅 Markdown 消息 |
| `channel_link(channel_id)` | 跳转子频道 | 仅频道 |
| `emoji(emoji_id)` | 系统表情 | 仅频道 |

### 9.4 方法详解

#### at_user(user_id)

构建@用户文本标签。

```python
# 示例
at_text = Builders.TextChainBuilder.at_user("123456789")
# 返回: '<@!123456789>'
```

**参数**：
- `user_id` (str): 用户 ID

**返回**: `str` - @用户的文本标签

#### at_everyone()

构建@全体成员文本标签。

```python
# 示例
at_text = Builders.TextChainBuilder.at_everyone()
# 返回: '<@everyone>'
```

**注意**: 需要机器人拥有发送"@全体成员"消息的权限。

#### cmd_enter(text)

构建回车指令文本标签。用户点击后，文本直接发送。

```python
# 示例
cmd_text = Builders.TextChainBuilder.cmd_enter("/help")
# 返回: '<qqbot-cmd-enter text="%2Fhelp" />'
```

**参数**：
- `text` (str): 点击后发送的文本，最多 100 字符

**返回**: `str` - 回车指令标签

#### cmd_input(text, show, reference)

构建参数指令文本标签。用户点击后，文本插入输入框，用户可自行编辑发送。

```python
# 示例 1: 基本用法
cmd_text = Builders.TextChainBuilder.cmd_input("/search", show="点击搜索")
# 返回: '<qqbot-cmd-input text="%2Fsearch" show="%E7%82%B9%E5%87%BB%E6%90%9C%E7%B4%A2" reference="false" />'

# 示例 2: 带回复引用
cmd_text = Builders.TextChainBuilder.cmd_input("/reply", reference=True)
# 返回: '<qqbot-cmd-input text="%2Freply" reference="true" />'
```

**参数**：
- `text` (str): 点击后插入输入框的文本，最多 100 字符
- `show` (str | None): 用户在消息内看到的文本；不传时 SDK 不会输出 `show` 属性，最多 100 字符
- `reference` (bool): 插入输入框时是否带消息原文回复引用，默认 `False`

**返回**: `str` - 参数指令标签

#### channel_link(channel_id)

构建跳转子频道文本标签。

```python
# 示例
link_text = Builders.TextChainBuilder.channel_link("123456789")
# 返回: '<#123456789>'
```

**参数**：
- `channel_id` (str): 子频道 ID

**注意**: 仅支持当前频道内的子频道。

**返回**: `str` - 跳转子频道标签

#### emoji(emoji_id)

构建系统表情文本标签。

```python
# 示例
emoji_text = Builders.TextChainBuilder.emoji("123")
# 返回: '<emoji:123>'
```

**参数**：
- `emoji_id` (str): 系统表情 ID（仅支持 type=1 的系统表情）

**注意**: type=2 的 emoji 表情直接按字符串填写即可。

**返回**: `str` - 表情标签

---

## 十、在不同场景中使用

### 10.1 按发送场景对照

| 场景 | 允许的构建器 | 图片发送方式 | 富媒体发送方式 | 其他说明 |
|------|--------------|--------------|----------------|----------|
| 频道消息 | `str/Embed/Ark/Markdown` | `image`、`file_image` | 不支持 `media_file_info` | 支持 `message_reference` |
| 频道私信 | `str/Embed/Ark/Markdown` | `image`、`file_image` | 不支持 `media_file_info` | 支持 `message_reference` |
| 群聊 v2 | `str/Embed/Ark/Markdown` | 不支持 `image`、`file_image` | `media_file_info` | 普通消息路径必须有文本内容 |
| QQ 单聊 v2 | `str/Embed/Ark/Markdown` | 不支持 `image`、`file_image` | `media_file_info` | 支持 `is_wakeup=True` |

### 10.2 官方字段映射理解

```python
# 频道消息 / 频道私信
await bot.api.send_guild_message(channel_id="xxx", content="文本", image="https://...")
await bot.api.send_guild_message(channel_id="xxx", content="文本", file_image="./image.png")

# 群聊 / QQ 单聊 v2
await bot.api.send_group_message(
    group_openid="xxx",
    content="文本",
    media_file_info=file_info.file_info,
)

# QQ 单聊 v2 互动召回
await bot.api.send_c2c_message(openid="xxx", content="回来看看我吧", is_wakeup=True)
```

**补充说明**：

- 群聊和 QQ 单聊 v2 由 SDK 自动补 `msg_type`
- `media_file_info` 与 `image` / `file_image` 互斥
- `is_wakeup=True` 仅适用于 QQ 单聊 v2，且与 `msg_id`、`event_id` 互斥
- 当前 SDK 对频道消息和频道私信统一支持 `message_reference`

---

## 十一、下一步

- [Model 库](./06_Model库.md) — 了解接收事件时的数据模型定义
- [插件与权限](./07_插件与权限.md) — 学习插件开发和命令注册
