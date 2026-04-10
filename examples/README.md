# EasyBot SDK 示例代码

本目录包含 EasyBot SDK 的各种使用示例，按从简单到复杂的顺序排列。

## 示例列表

| 编号 | 文件名 | 难度 | 主要内容 |
|------|--------|------|----------|
| 01 | [01_simple_workflow.py](01_simple_workflow.py) | ⭐ | 最简单的机器人示例：创建 Bot、注册事件、启动 |
| 02 | [02_protocols.py](02_protocols.py) | ⭐ | 三种连接协议：WebSocket、Webhook、远程 Webhook |
| 03 | [03_reply.py](03_reply.py) | ⭐ | reply() 快速回复：文本、图片、Embed、Ark、Markdown |
| 04 | [04_event_decorators.py](04_event_decorators.py) | ⭐⭐ | 事件装饰器：消息、成员、生命周期、互动事件 |
| 05 | [05_lifecycle_events.py](05_lifecycle_events.py) | ⭐⭐ | 生命周期事件：on_startup、on_shutdown、on_timer |
| 06 | [06_message_builder.py](06_message_builder.py) | ⭐⭐ | 消息构建器：MessagesModel 各类消息详解 |
| 07 | [07_local_image.py](07_local_image.py) | ⭐⭐ | 发送图片：频道/群聊/单聊的不同方式 |
| 08 | [08_plugins_permissions.py](08_plugins_permissions.py) | ⭐⭐⭐ | 插件与权限：指令注册、权限控制、预处理器 |
| 09 | [09_session_waitfor.py](09_session_waitfor.py) | ⭐⭐⭐ | Session 与 wait_for：会话管理、等待用户输入 |
| 10 | [10_api_usage.py](10_api_usage.py) | ⭐⭐⭐ | API 使用：频道管理、消息管理、禁言、身份组 |
| 11 | [11_complete_game.py](11_complete_game.py) | ⭐⭐⭐⭐ | 完整示例：猜数字游戏（综合运用） |
| 12 | [12_optimized_waitfor.py](12_optimized_waitfor.py) | ⭐⭐⭐⭐ | 快捷方式、BotCommandObject 高级用法、谓词函数 |
| 13 | [13_hot_reload.py](13_hot_reload.py) | ⭐⭐⭐⭐ | 热重载：文件变化自动重启机器人 |
| 14 | [14_send_api_matrix.py](14_send_api_matrix.py) | ⭐⭐⭐⭐ | 发送 API 矩阵：各场景发送方式对比 |
| 15 | [15_large_file_upload.py](15_large_file_upload.py) | ⭐⭐⭐ | 大文件分片上传：一键上传、手动控制、并发上传 |

## 快速开始

### 1. 配置机器人凭证

在每个示例文件中，将以下代码中的 `your_app_id` 和 `your_app_secret` 替换为你的 QQ 机器人凭证：

```python
bot = Bot(
    app_id="your_app_id",        # 替换为你的 AppID
    app_secret="your_app_secret", # 替换为你的 AppSecret
)
```

### 2. 运行示例

```bash
# 运行简单工作流示例
python 01_simple_workflow.py

# 运行其他示例
python 02_protocols.py
python 03_reply.py
# ...
```

## 示例详解

### 01. 简单工作流

展示最简单的机器人结构：
- 创建 Bot 实例
- 注册事件处理器（频道、群聊、单聊）
- 启动机器人

**适合人群**：第一次使用 EasyBot 的开发者

### 02. 三种协议

展示 EasyBot 支持的三种连接方式：
- **WebSocket**（推荐）：自动维持长连接，适合大多数场景
- **Webhook**：需要公网 IP 或内网穿透
- **远程 Webhook**：连接远程 Webhook 服务器

**适合人群**：需要选择连接方式的开发者

### 03. reply() 快速回复

展示如何使用 `reply()` 方法回复各种类型的消息：
- 纯文本
- 网络图片、本地图片（仅频道）
- Embed 消息
- Ark 模板消息（23、24、37）
- Markdown 消息
- 引用回复

**适合人群**：需要发送不同类型消息的开发者

### 04. 事件装饰器

展示 EasyBot 提供的各种事件装饰器：
- 消息事件：`@bot.on_guild_message`、`@bot.on_group_message` 等
- 成员事件：`@bot.on_guild_member_add`、`@bot.on_guild_member_remove` 等
- 生命周期事件：`@bot.on_guild_create`、`@bot.on_group_add` 等
- 互动事件：`@bot.on_interaction`、`@bot.on_reaction_add` 等
- 批量订阅：`@bot.on_default_public_events`、`@bot.on_all_intent_events`

**适合人群**：需要订阅各种事件的开发者

### 05. 生命周期事件

展示机器人的生命周期管理：
- `on_startup`：启动时触发，适合初始化操作
- `on_shutdown`：关闭时触发，适合清理操作
- `on_timer`：定时触发，适合定时任务

**适合人群**：需要管理机器人生命周期的开发者

### 06. 消息构建器

详细展示 `MessagesModel` 的各种消息类型：
- `Message`：普通消息（文本、图片、引用）
- `MessageEmbed`：Embed 消息
- `MessageArk23`：Ark 23 模板（链接列表）
- `MessageArk24`：Ark 24 模板（图文）
- `MessageArk37`：Ark 37 模板（大图）
- `MessageMarkdown`：Markdown 消息（原生、模板）

**适合人群**：需要构建复杂消息的开发者

### 07. 发送图片

展示不同场景下发送图片的方式：

| 场景 | 支持方式 |
|------|---------|
| 频道 | `file_image` 参数（路径/bytes/文件对象）、`image` 参数（URL） |
| 群聊 | `upload_media` API（file_data 或 url） |
| 单聊 | `upload_media` API（file_data 或 url） |

**适合人群**：需要发送图片的开发者

### 08. 插件与权限

展示 EasyBot 的插件系统和权限管理：
- 基础指令注册
- 多指令别名
- 正则指令
- 限制有效场景（群聊、单聊、频道）
- 权限控制（频道管理员、机器人管理员）
- 运行时管理管理员
- 预处理器

**适合人群**：需要实现指令系统和权限控制的开发者

### 09. Session 与 wait_for

展示会话管理和等待用户输入：
- 基础 session 使用（bind 上下文管理器）
- `with_session` 装饰器简化
- `wait_for` 等待用户输入
- 复杂的多步骤流程
- 不同作用域的 session（USER、GROUP、CHANNEL、GLOBAL）

**适合人群**：需要实现交互式对话的开发者

### 10. API 使用

展示 EasyBot 提供的完整 API 封装：
- 发送消息（频道、群聊、单聊）
- 频道管理（获取信息、子频道、成员）
- 消息管理（获取、撤回）
- 身份组管理
- 禁言管理
- 互动事件处理
- 富媒体上传

**适合人群**：需要调用 QQ 官方 API 的开发者

### 11. 完整示例：猜数字游戏

综合运用以下功能的完整游戏：
- session 会话管理
- 正则匹配
- 指令系统
- 多步骤流程

**游戏规则**：
1. 用户发送 "猜数字" 开始游戏
2. 机器人生成 1-100 的随机数
3. 用户输入数字进行猜测
4. 机器人提示大了还是小了
5. 猜对后显示猜测次数

**适合人群**：想学习如何综合运用各种功能的开发者

### 12. 高级插件开发

展示模块化插件开发：
- 创建独立的插件文件
- 使用 `Plugins` 类注册命令和预处理器
- 在主程序中加载和注册插件
- 动态加载插件目录

**目录结构**：
```
plugins/
├── __init__.py        # 插件包初始化
├── base.py            # 插件基类（可选）
├── weather.py         # 天气查询插件
├── translate.py       # 翻译插件
└── admin_tools.py     # 管理工具插件
```

### 13. 热重载

展示热重载功能，文件变化时自动重启机器人。

**适合人群**：需要频繁调试的开发者

### 14. 发送 API 矩阵

展示各场景下发送消息的 API 用法对比。

**适合人群**：需要在多场景发送消息的开发者

### 15. 大文件分片上传

展示大文件分片上传的三种方式：
- **一键上传**：最简单，适合大多数场景
- **手动控制**：显示进度，适合需要反馈的场景
- **并发上传**：提高上传速度
- **断点续传**：支持中断后继续上传

**适合人群**：需要上传大文件（视频、文档等）的开发者

## 常见问题

### Q: 如何获取 app_id 和 app_secret？

A: 需要在 [QQ 开放平台](https://q.qq.com/) 注册并创建机器人应用，在应用详情页可以获取到 AppID 和 AppSecret。

### Q: 公域机器人和私域机器人有什么区别？

A:
- **公域机器人**：只能接收被@的消息，无法接收全量消息
- **私域机器人**：可以接收全量消息（需要申请私域权限）

在创建 Bot 时通过 `is_private` 参数指定：
```python
bot = Bot(
    app_id="...",
    app_secret="...",
    is_private=False,  # True=私域, False=公域（默认）
)
```

### Q: 如何调试机器人？

A: 开启调试模式可以输出详细日志：
```python
bot = Bot(
    app_id="...",
    app_secret="...",
    is_debug=True,  # 开启调试模式
)
```

### Q: 示例运行报错怎么办？

A: 请检查以下几点：
1. 是否正确填写了 `app_id` 和 `app_secret`
2. 机器人是否已在 QQ 开放平台发布
3. 机器人是否已被添加到测试群/频道
4. 网络连接是否正常

## 更多资源

- [EasyBot SDK 源码](../easybot/)
- [QQ 机器人官方文档](https://bot.q.qq.com/wiki/)

## 贡献

如果你发现了问题或有改进建议，欢迎提交 Issue 或 PR。
