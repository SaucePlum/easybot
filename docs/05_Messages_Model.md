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
| 简单文本回复 | `Message` | 最简单直接 |
| 文本 + 图片 | `Message(image=...)` | 一行代码搞定 |
| 结构化信息展示 | `MessageEmbed` | 清晰的字段布局 |
| 导航/链接列表 | `MessageArk23` | 多行可点击链接 |
| 推广/资讯卡片 | `MessageArk24/37` | 视觉吸引力强 |
| 富文本格式化 | `MessageMarkdown` | 支持标题/列表/加粗等 |

### 1.2 消息构建器列表

| 构建器 | 类名 | msg_type | 适用场景 |
|--------|------|----------|---------|
| 文本消息 | `Message` | 0 / 7 | 基础文本、图片、引用回复 |
| Embed 卡片 | `MessageEmbed` | 4 | 结构化信息展示 |
| Ark 23 链接列表 | `MessageArk23` | 3 | 多行链接列表 |
| Ark 24 图文卡片 | `MessageArk24` | 3 | 标题+描述+缩略图 |
| Ark 37 大图卡片 | `MessageArk37` | 3 | 大图展示模板 |
| Markdown | `MessageMarkdown` | 2 | 富文本格式消息 |

---

## 二、Message — 普通消息

最基础的消息类型，支持文本、图片、引用回复和富媒体。

### 2.1 构造参数

```python
MessagesModel.Message(
    content: str | int | float | None = None,   # 消息文本
    image: str | None = None,                    # 网络图片 URL
    file_image: bytes | BinaryIO | str | None = None,  # 本地图片
    media_file_info: str | None = None,          # 富媒体 file_info
    message_reference_id: str | None = None,     # 引用回复的消息 ID
    ignore_message_reference_error: bool = False,# 忽略引用错误
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
```

**文本 + 本地图片**：

```python
# 方式1：文件路径
msg = MessagesModel.Message(content="本地图片", file_image="./photo.png")

# 方式2：bytes 数据
msg = MessagesModel.Message(content="Bytes图片", file_image=image_bytes)
```

**引用回复**：

```python
msg = MessagesModel.Message(
    content="我同意你的观点",
    message_reference_id="原消息ID",
)
```

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
```

### 2.3 注意事项

- `image` 和 `file_image` 不能同时使用
- `media_file_info` 与 `image`/`file_image` 互斥
- `file_image` 仅适用于**频道消息**；群聊/单聊需使用 `media_file_info`

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
    key_values: dict[str, str | list[str]] | list[dict] | None = None,  # 模板参数
    keyboard_id: str | None = None,                       # Keyboard 模板 ID
    keyboard_content: dict | None = None,                  # 自定义 Keyboard 内容
)
```

**约束**: `content` 和 `template_id` 不可同时存在。

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
                        "action": {"type": 2, "data": "confirm", "reply": True}
                    },
                    {
                        "render_data": {"label": "取消"},
                        "action": {"type": 2, "data": "cancel", "reply": True}
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

## 九、在不同场景中使用

所有消息构建器均可在以下 API 中使用：

```python
# 频道消息 — 支持所有类型
await bot.api.send_guild_message(channel_id="xxx", content=任意消息对象)

# 群聊消息 — 支持 Message/Embed/Ark/Markdown
await bot.api.send_group_message(group_openid="xxx", content=任意消息对象)

# 单聊消息 — 支持 Message/Embed/Ark/Markdown
await bot.api.send_c2c_message(openid="xxx", content=任意消息对象)

# 频道私信 — 支持 Message/Embed/Ark/Markdown
await bot.api.send_direct_message(guild_id="xxx", content=md)
```

---

## 十、下一步

- [Model 库](./06_Model库.md) — 了解接收事件时的数据模型定义
- [插件与权限](./07_插件与权限.md) — 学习插件开发和命令注册
