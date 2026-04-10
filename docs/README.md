---
home: true
config:
  - type: banner
    banner: /bg.svg
    bannerMask:
      light: 0.1
      dark: 0.3
    hero:
      name: EasyBot SDK 帮助文档
      tagline: QQ 官方机器人平台轻量级 Python SDK
      text: 简洁 · 易上手 · 稳定
      actions:
        - text: 快速开始
          link: /02_快速入门
          theme: brand
        - text: 了解更多
          link: /01_简介
          theme: alt
  - type: features
    features:
      - title: 极简优先
        details: 5 行代码即可启动机器人，无需理解复杂的协议细节。SDK 内部封装 Intent 计算、Token 管理、消息去重、签名验证等所有底层逻辑。
        icon: 🚀
      - title: 官方合规
        details: 直接对接 QQ 开放平台官方 API，不存在封号风险。支持公域/私域机器人，稳定可靠，生产级质量。
        icon: ✅
      - title: 类型安全
        details: 基于 Python dataclass 构建的完整数据模型体系，所有 API 返回值和事件数据均为强类型对象，配合类型提示提供出色的 IDE 支持。
        icon: 🛡️
      - title: 灵活部署
        details: 支持 WebSocket、Webhook、远程 Webhook 三种连接模式，适配本地开发、服务器部署、云函数、内网穿透等多种场景。
        icon: 🔧
      - title: 丰富消息类型
        details: 支持文本、图片、Embed 卡片、Markdown、Ark 模板等多种消息类型，满足各种业务场景需求。
        icon: 💬
      - title: 插件与权限
        details: 内置命令注册、预处理器机制和权限控制系统，支持频道管理员权限和自定义机器人管理员权限。
        icon: 🔐
  - type: custom
---

## 快速开始

::: tip 环境要求
- Python 3.10+
- aiohttp >= 3.9.0
- pyyaml >= 6.0
:::

### 安装

::: code-tabs
@tab pip

```bash
pip install easybot-qq
```

@tab 源码安装

```bash
git clone https://github.com/SaucePlum/easybot.git
cd easybot
pip install -r requirements.txt
```

:::

### 代码示例

::: details 点击查看完整示例

```python
from easybot import Bot, Model

bot = Bot(app_id="你的AppID", app_secret="你的AppSecret")

@bot.on_guild_message
async def on_message(msg: Model.GuildMessage) -> None:
    await msg.reply("Hello World!")

bot.start()
```

:::

::: tip 提示
公域机器人只会收到频道内 @它 的消息；请在频道中 @机器人进行测试。
:::

::: details 推荐：加入最小错误处理

```python
from easybot import Bot, Model, APIError, NetworkError, RateLimitError

bot = Bot(app_id="你的AppID", app_secret="你的AppSecret")

@bot.on_guild_message
async def on_message(msg: Model.GuildMessage) -> None:
    try:
        await msg.reply(f"你说：{msg.treated_msg}")
    except RateLimitError as e:
        bot.logger.warning(f"触发频率限制：{e}")
    except (APIError, NetworkError) as e:
        bot.logger.error(f"回复失败：{e}")

bot.start()
```

:::

::: details 异步启动（自行管理事件循环）

```python
import asyncio
from easybot import Bot, Model

bot = Bot(app_id="你的AppID", app_secret="你的AppSecret")

@bot.on_guild_message
async def on_message(msg: Model.GuildMessage) -> None:
    await msg.reply("Hello World!")

asyncio.run(bot.start_async())
```

:::

::: warning 注意
运行前请确保已在 [QQ 开放平台](https://q.qq.com) 创建机器人应用并获取 AppID 和 AppSecret。
:::

## 核心功能

### 🎯 多场景消息收发

支持 QQ 平台全场景消息交互，一套代码适配多种场景：

| 场景 | 说明 | 适用范围 |
|------|------|----------|
| **频道消息** | 公域 @机器人消息、私域全量消息 | 频道社区 |
| **群聊消息** | 群内 @机器人消息 | QQ 群聊 |
| **单聊消息** | QQ 私聊消息 | 一对一聊天 |
| **频道私信** | 频道内私信对话 | 频道私信 |

### 🔌 完整 API 封装

全面覆盖 QQ 开放平台的 OpenAPI，提供类型安全的 Python 接口：

- **频道管理** - 创建、查询、修改子频道信息
- **成员管理** - 查询成员、踢出成员、设置禁言
- **身份组管理** - CRUD 操作、成员分配、权限配置
- **权限管理** - 用户权限、身份组权限的查询与修改
- **论坛系统** - 帖子、评论、回复事件监听
- **音频控制** - 播放、暂停、切歌等音频操作
- **消息管理** - 撤回消息、设置精华、获取引用

### 💬 会话管理系统

基于作用域的会话状态管理，轻松实现多轮对话：

- **五种作用域** - `USER` `GUILD` `CHANNEL` `GROUP` `GLOBAL`
- **会话超时** - 自动回收过期会话，释放资源
- **WaitFor 等待** - 实现多轮对话交互，等待用户输入
- **状态持久化** - 支持会话数据的持久化存储

::: details 查看 WaitFor 示例代码

```python
from easybot import Bot, Model, Scope, WaitTimeoutError

bot = Bot(app_id="你的AppID", app_secret="你的AppSecret")

@bot.on_guild_message
async def on_message(msg: Model.GuildMessage) -> None:
    with bot.session.bind(msg) as s:
        await msg.reply("请输入你的名字：")
        
        try:
            # 等待用户回复（任意输入）
            name_msg = await s.wait_for(
                scopes=Scope.USER,
                command=None,  # None 表示接受任意输入
                timeout=60  # 60秒超时
            )
            
            name = name_msg.treated_msg or name_msg.content
            await msg.reply(f"你好，{name}！")
        
        except WaitTimeoutError:
            await msg.reply("等待超时，请重新开始。")

bot.start()
```

:::

### 🛡️ 生产级特性

- **自动重连** - WebSocket 断线自动重连，保证连接稳定
- **消息去重** - 内置消息去重机制，避免重复处理
- **签名验证** - Webhook 消息签名验证，确保安全
- **Token 管理** - 自动刷新 Token，无需手动维护
- **错误处理** - 完善的异常体系，精准定位问题
- **日志系统** - 分级日志输出，便于调试和监控
