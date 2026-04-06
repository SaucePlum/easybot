# Changelog

All notable changes to this project will be documented in this file.

## [1.0.1] - 2026-04-07

### 新增 (Features)

- **消息构建器重构**: 将 `messages_model.py` 重构为 `builders.py`，新增 `ThreadContentBuilder` 和 `ParagraphBuilder` 用于构建 JSON 格式帖子内容
  - 支持 ThreadContent（帖子内容）和 Paragraph（段落）的链式构建
  - 新增 `Elem` 等富文本元素模型定义
  - `API.create_thread()` 方法支持 JSON 格式帖子发送
  - `Model` 类新增 `to_dict()` 方法用于序列化

- **EasyBot 开发助手 Skill**: 添加完整的开发辅助技能模块
  - API 参考文档（API Reference）
  - 最佳实践指南（Best Practices）
  - 消息构建器使用说明
  - 会话管理完整指南
  - 插件系统开发文档
  - 故障排查手册
  - 多个示例项目：客服机器人、猜数字游戏、待办事项机器人

- **项目开发规范体系**: 建立完整的开发规范文档体系
  - 架构设计原则（SOLID、设计模式、公共 API 设计）
  - 代码格式与风格规范（Black/isort 配置、命名规范）
  - Python 语言约定（Dataclass、异常体系、类型系统）
  - 异步编程规范（asyncio 使用、资源管理、并发控制）
  - 日志系统使用规范（级别选择、格式要求）
  - 测试编写规范（TDD 流程、pytest 使用）

- **文档站点**: 搭建 VuePress 文档站点
  - 添加 GitHub Actions CI 自动部署工作流
  - 配置站点主题、导航和资源文件

- **插件热重载功能**: 大幅增强插件系统的运行时管理能力
  - Bot 类新增 `reload_plugin()`、`reload_all_plugins()`、`unload_plugin()` 等热重载 API
  - Bot 类新增 `enable_command()`、`disable_command()`、`remove_command()` 命令动态管理接口
  - Plugins 类扩展，支持命令启用/禁用、插件卸载/重载、完整查询接口
  - 新增 `clear_all_plugins()` 一键清空所有已加载插件
  - 事件分发器优化，支持更灵活的事件处理和调度
  - 新增 [examples/13_hot_reload.py](examples/13_hot_reload.py) 完整示例

### 改进 (Improvements)

- **消息类型处理优化**: 将 `MessageBase` 抽象基类替换为具体消息类型的联合类型（Union），提升类型安全性和代码可读性
- **会话管理优化**: 优化会话管理逻辑，支持多作用域匹配，改进 `wait_for` 方法
- **SDK 启动链路优化**: 分析并重构 Bot 类启动流程，优化 WebSocket 客户端连接管理
- **频道类型常量更新**: 更新 `Channel` 模型中的频道类型常量值，确保与最新接口保持一致
- **代码格式统一**: 使用 Black 和 isort 对全项目代码进行自动格式化

### 文档 (Documentation)

- 更新消息构建器使用方法和示例代码
- 更新会话管理文档，补充 `wait_for` 方法签名和参数说明
- 修复文档中的图片路径问题
- 移除不再使用的 sitemap 插件并优化 CI 配置

### 变更文件清单

```
easybot/__init__.py          # 公共 API 导出调整
easybot/bot.py               # 启动链路重构 + 热重载 API
easybot/builders.py          # 新文件：重构自 messages_model.py
easybot/models.py            # 消息类型优化、新增帖子相关模型
easybot/session.py           # 会话管理优化
easybot/api.py               # create_thread 支持 JSON 格式
easybot/plugins.py           # 插件系统大幅扩展（热重载、命令管理）
easybot/_internal/event_dispatcher.py  # 事件分发器优化
easybot/_internal/event_utils.py       # 事件工具函数调整
easybot/_internal/ws_client.py         # WebSocket 连接管理优化
easybot/_internal/reply_strategy.py    # 回复策略微调
easybot/version.py           # 版本号更新
examples/08_plugins_permissions.py     # 示例代码适配
examples/13_hot_reload.py              # 新增：热重载功能示例
docs/07_插件与权限.md                  # 插件文档更新
```

## [1.0.0] - 初始版本

初始发布版本。
