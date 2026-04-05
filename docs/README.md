---
home: true
modules:
  - bannerBrand
  - features
  - mdContent
  - footer
bannerBrand:
  title: EasyBot SDK
  description: QQ 官方机器人平台轻量级 Python SDK
  tagline: 简洁 · 易上手 · 稳定
  heroImage: /easybot/logo.svg
  bgImage: /easybot/bg.svg
  buttons:
    - text: 快速开始
      link: /02_快速入门
      type: link
    - text: 了解更多
      link: /01_简介
      type: link
features:
  - title: 极简优先
    details: 5 行代码即可启动机器人，无需理解复杂的协议细节。SDK 内部封装 Intent 计算、Token 管理、消息去重、签名验证等所有底层逻辑。
  - title: 官方合规
    details: 直接对接 QQ 开放平台官方 API，不存在封号风险。支持公域/私域机器人，稳定可靠，生产级质量。
  - title: 类型安全
    details: 基于 Python dataclass 构建的完整数据模型体系，所有 API 返回值和事件数据均为强类型对象，配合类型提示提供出色的 IDE 支持。
  - title: 灵活部署
    details: 支持 WebSocket、Webhook、远程 Webhook 三种连接模式，适配本地开发、服务器部署、云函数、内网穿透等多种场景。
  - title: 丰富消息类型
    details: 支持文本、图片、Embed 卡片、Markdown、Ark 模板等多种消息类型，满足各种业务场景需求。
  - title: 插件与权限
    details: 内置命令注册、预处理器机制和权限控制系统，支持频道管理员权限和自定义机器人管理员权限。
footer:
  startYear: 2026
---

## 快速开始

::: tip 环境要求
- Python 3.10+
- aiohttp >= 3.9.0
- pyyaml >= 6.0
:::

### 安装

:::: code-group
::: code-group-item pip

```bash
pip install easybot-sdk
```

:::
::: code-group-item 源码安装

```bash
git clone https://github.com/SaucePlum/easybot.git
cd easybot
pip install -r requirements.txt
```

:::
::::

### 代码示例

::: details 点击查看完整示例

```python
from easybot import Bot

bot = Bot(app_id="你的AppID", app_secret="你的AppSecret")

@bot.on_guild_message
async def on_message(msg):
    await msg.reply("Hello World!")

bot.start()
```

:::

::: warning 注意
运行前请确保已在 [QQ 开放平台](https://q.qq.com) 创建机器人应用并获取 AppID 和 AppSecret。
:::

## 核心功能

### 多场景消息收发
- **频道消息**: 公域 @机器人消息、私域全量消息
- **群聊消息**: 群内 @机器人消息
- **单聊消息**: QQ 私聊消息
- **频道私信**: 频道内私信对话

### 完整 API 封装
覆盖 QQ 开放平台的全部 OpenAPI：
- 频道管理（创建/查询/修改子频道）
- 成员管理（查询/踢出/禁言）
- 身份组管理（CRUD 及成员分配）
- 权限管理（用户/身份组权限查询与修改）
- 论坛帖子/评论/回复事件
- 音频控制、消息撤回等

### 会话管理
基于作用域的会话系统，支持：
- 五种作用域：`USER` / `GUILD` / `CHANNEL` / `GROUP` / `GLOBAL`
- 会话超时与自动回收
- **WaitFor 命令等待**：实现多轮对话交互
