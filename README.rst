.. image:: https://socialify.git.ci/SaucePlum/easybot/image?custom_description=%E8%BD%BB%E9%87%8F%E7%BA%A7+QQ+%E6%9C%BA%E5%99%A8%E4%BA%BA+SDK%EF%BC%8C%E4%B8%93%E6%B3%A8%E4%BA%8E%E7%AE%80%E6%B4%81%E3%80%81%E5%AE%B9%E6%98%93%E4%B8%8A%E6%89%8B%E4%B8%94%E7%A8%B3%E5%AE%9A&description=1&forks=1&issues=1&language=1&name=1&owner=1&pattern=Circuit+Board&pulls=1&stargazers=1&theme=Auto
   :alt: easybot
   :target: https://github.com/SaucePlum/easybot

|

.. image:: https://img.shields.io/badge/language-python-green.svg?style=plastic
    :target: https://www.python.org/
    :alt: Python

.. image:: https://img.shields.io/badge/license-MIT-orange.svg?style=plastic
    :target: https://github.com/SaucePlum/easybot/blob/master/LICENSE
    :alt: License

.. image:: https://app.codacy.com/project/badge/Grade/f015549b3dba4602be2fe0f5d8b0a8d5
    :target: https://app.codacy.com/gh/SaucePlum/easybot/dashboard
    :alt: Codacy

.. image:: https://img.shields.io/pypi/dw/easybot-qq?style=plastic&color=blue
   :target: https://pypi.org/project/easybot-qq/
   :alt: Pypi Downloads

✨ 轻量级 QQ 官方机器人 SDK，极简 API 设计，~6 行代码即可启动 ✨

简介
====

**EasyBot** 是一款专为 QQ 官方机器人平台打造的轻量级 Python SDK，定位为面向初级开发者的入门级框架。其核心理念是「简洁、易上手、稳定」，通过极简的 API 设计和完善的抽象层，让开发者能够以最少的代码量快速构建功能完备的 QQ 机器人应用。

核心特性
========

- 🚀 **极简 API** — ~6 行代码启动机器人，无需继承任何类
- 🎯 **零继承装饰器范式** — ``@bot.on_guild_message`` 直接用，告别繁琐的 Client 子类重写
- 📦 **最小依赖** — 仅需 ``aiohttp`` + ``pyyaml`` 两个第三方库，安装即用
- 🔧 **三协议全支持** — WebSocket / Webhook / Remote Webhook 自由切换，适配任意部署环境
- 🌐 **全场景消息覆盖** — 频道、群聊、C2C 私聊、频道私信四大场景一站搞定
- 💬 **内置会话管理器** — Session + WaitFor 多轮对话原生支持，带超时回复与 GC 回收（业界独有）
- 🧩 **插件自动加载** — 扫描目录自动注册指令与预处理器，开箱即用的插件生态
- 🎮 **增强指令系统** — 正则匹配 / 管理员权限 / 短路机制 / 多场景隔离 / 预处理器五合一
- ⏰ **生命周期管理** — startup / shutdown / timer 三大内置事件，无需额外框架
- 🔒 **沙箱环境支持** — 一键开启沙箱模式，安全调试不干扰线上机器人
- 🏷️ **现代 Python 语法** — 基于 Python 3.10+，完整类型提示，IDE 智能补全无忧

安装
====

.. code-block:: bash

    pip install easybot-qq

快速开始
========

最简示例 — ~6 行启动机器人
----------------------------

.. code-block:: python

    from easybot import Bot

    bot = Bot(app_id="你的AppID", app_secret="你的AppSecret")

    @bot.on_guild_message
    async def on_message(msg):
        await msg.reply("Hello World!")

    bot.start()

多场景消息处理 — 一个 Bot 打天下
----------------------------------

.. code-block:: python

    from easybot import Bot, Model

    bot = Bot(app_id="你的AppID", app_secret="你的AppSecret")

    @bot.on_guild_message
    async def handle_guild(msg: Model.GuildMessage):
        await msg.reply(f"频道消息: {msg.treated_msg}")

    @bot.on_group_message
    async def handle_group(msg: Model.GroupMessage):
        await msg.reply(f"群聊消息: {msg.treated_msg}")

    @bot.on_c2c_message
    async def handle_c2c(msg: Model.C2CMessage):
        await msg.reply(f"私信消息: {msg.treated_msg}")

    bot.start()

亮点展示 — WaitFor 多轮对话 & 指令系统
-----------------------------------------

.. code-block:: python

    from easybot import Bot, Model, Scope

    bot = Bot(app_id="你的AppID", app_secret="你的AppSecret")

    # 指令系统：正则 + 管理员权限 + 短路机制，一行搞定
    @bot.on_command(regex=r"^查询 (.+)$", is_require_admin=True)
    async def query(msg: Model.GuildMessage):
        await msg.reply(f"查询结果: {msg.command_args[0]}")

    # 会话管理：WaitFor 等待用户回复，天然支持多轮对话
    @bot.on_command(command=["签到"])
    async def check_in(msg, session=None):
        with bot.session.bind(msg) as s:
            s.new(Scope.USER, "check_in", {"step": "confirm"})
            await msg.reply("确认签到吗？(回复 yes/no)")
            reply = await s.wait_for(Scope.USER, ["yes", "no"], timeout=30)
            if reply.treated_msg == "yes":
                await msg.reply("✅ 签到成功！")
            else:
                await msg.reply("已取消签到。")

    bot.start()

功能特性
========

消息类型支持
------------

=================  ========================
类型               说明
=================  ========================
Message            文本 / 图片 / 引用消息
MessageEmbed       Embed 卡片消息
MessageArk23       Ark 23 链接模板
MessageArk24       Ark 24 图文模板
MessageArk37       Ark 37 大图模板
MessageMarkdown    Markdown 消息
=================  ========================

连接协议
--------

==================  ==================================
协议                适用场景
==================  ==================================
WebSocket           本地 / 服务器直连（默认）
Webhook             公网 IP / 云函数部署
Remote Webhook      内网穿透 / 远程中转
==================  ==================================

核心能力一览
============

================  =====================================================
能力              说明
================  =====================================================
🤖 **事件系统**   40+ 事件装饰器，覆盖频道 / 群聊 / C2C / 私信 / 论坛 / 音频等全场景
💬 **会话管理**   Session 五级作用域 + WaitFor 异步等待，超时自动回复 + GC 回收
🎮 **指令系统**   关键词 / 正则匹配、管理员权限、短路机制、多场景隔离、预处理器
🧩 **插件生态**   自动扫描目录加载，支持 register() 函数与装饰器两种注册方式
⏰ **生命周期**   startup / shutdown / timer 三大内置事件
🔒 **沙箱模式**   一键开启沙箱环境，安全调试不干扰线上
================  =====================================================

文档
====

完整文档请参阅 `docs <https://github.com/SaucePlum/easybot/tree/main/docs>`_ 目录：

==========================  ====================================================
文档                        内容
==========================  ====================================================
简介_                       设计理念、核心价值、与其他方案对比
快速入门_                   从安装到第一个机器人的完整指南
`SDK 组件`_                 Bot / API / Protocol / Logger 等核心组件详解
`API 参考`_                 完整 API 接口文档
`Messages Model`_           消息构建器（Embed / Ark / Markdown 等）
`Model 库`_                 数据模型定义与字段说明
`插件与权限`_               插件开发、指令系统、权限管理
`Session 会话管理器`_       会话 API 与 WaitFor 多轮对话详解
`常见问题 Q&A`_             FAQ 与问题排查
`联系和反馈`_               问题提交与社区交流
==========================  ====================================================

.. _简介: https://github.com/SaucePlum/easybot/blob/main/docs/01_简介.md
.. _快速入门: https://github.com/SaucePlum/easybot/blob/main/docs/02_快速入门.md
.. _SDK 组件: https://github.com/SaucePlum/easybot/blob/main/docs/03_SDK组件.md
.. _API 参考: https://github.com/SaucePlum/easybot/blob/main/docs/04_API参考.md
.. _Messages Model: https://github.com/SaucePlum/easybot/blob/main/docs/05_Messages_Model.md
.. _Model 库: https://github.com/SaucePlum/easybot/blob/main/docs/06_Model库.md
.. _插件与权限: https://github.com/SaucePlum/easybot/blob/main/docs/07_插件与权限.md
.. _Session 会话管理器: https://github.com/SaucePlum/easybot/blob/main/docs/08_Session会话管理器.md
.. _常见问题 Q&A: https://github.com/SaucePlum/easybot/blob/main/docs/09_常见问题Q&A.md
.. _联系和反馈: https://github.com/SaucePlum/easybot/blob/main/docs/10_联系和反馈.md

环境要求
========

- Python >= 3.10
- aiohttp >= 3.9.0
- pyyaml >= 6.0

获取机器人凭证
==============

1. 访问 `QQ 开放平台 <https://q.qq.com>`_ 并登录
2. 创建一个机器人应用
3. 获取 **AppID** 和 **AppSecret**

许可证
======

本项目采用 `MIT <LICENSE>`_ 许可证。

联系方式
========

- 作者：小念同学
- 邮箱：2660422452@qq.com
- GitHub：https://github.com/SaucePlum/easybot