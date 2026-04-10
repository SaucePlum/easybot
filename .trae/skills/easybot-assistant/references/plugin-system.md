# EasyBot 插件系统完整文档

## 目录

1. [概述](#概述)
2. [命令注册](#命令注册)
3. [预处理器](#预处理器)
4. [权限控制](#权限控制)
5. [插件开发](#插件开发)
6. [插件自动加载](#插件自动加载)
7. [插件热重载](#插件热重载)
8. [生命周期钩子](#生命周期钩子)
9. [动态管理](#动态管理)
9. [类型定义](#类型定义)
10. [最佳实践](#最佳实践)

---

## 概述

EasyBot 插件系统提供了强大的命令处理和预处理器机制，支持：

- **命令注册**：精确匹配、正则匹配
- **预处理器**：在命令执行前统一处理
- **权限控制**：频道管理员、机器人管理员
- **短路机制**：命令匹配后停止后续处理
- **动态管理**：运行时启用/禁用命令

---

## 命令注册

### 基本用法

使用 `@bot.on_command` 装饰器注册命令：

```python
from easybot import Bot, CommandValidScenes, Model

bot = Bot(app_id="...", app_secret="...")

@bot.on_command(command="hello")
async def hello_cmd(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
) -> None:
    await msg.reply("Hello!")
```

### 命令参数

```python
@bot.on_command(
    command=["ping", "测试"],      # 多个触发词
    regex=None,                    # 或使用正则
    is_treat=True,                 # 处理 treated_msg
    is_require_at=False,           # 是否需要@
    is_short_circuit=True,         # 匹配后是否短路
    is_custom_short_circuit=False, # 自定义短路逻辑
    is_require_admin=False,        # 是否需要频道管理员
    admin_error_msg="权限不足",    # 权限不足时的提示
    valid_scenes=CommandValidScenes.ALL,  # 有效场景
    enabled=True,                  # 是否启用
    is_require_bot_admin=False,    # 是否需要机器人管理员
    bot_admin_error_msg=None,      # 机器人管理员权限不足提示
)
async def my_command(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
) -> None:
    await msg.reply("命令执行")
```

### 命令匹配方式

#### 精确匹配

```python
# 单个命令
@bot.on_command(command="ping")
async def ping(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
) -> None:
    await msg.reply("pong!")

# 多个命令（任意一个触发）
@bot.on_command(command=["hello", "你好", "hi"])
async def greet(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
) -> None:
    await msg.reply("你好！")
```

#### 正则匹配

```python
import re

# 正则表达式匹配
@bot.on_command(regex=re.compile(r"掷骰子(\d+)d(\d+)"))
async def dice(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
) -> None:
    # msg.treated_msg 包含 groups() 结果
    count, sides = msg.treated_msg
    await msg.reply(f"掷 {count} 个 {sides} 面骰子")

# 多个正则
@bot.on_command(regex=[r"\d+", r"数字"])
async def number_cmd(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
) -> None:
    await msg.reply(f"匹配到数字")
```

#### 接受任意输入

```python
# 不指定 command 或 regex，接受任意输入
@bot.on_command()
async def catch_all(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
) -> None:
    await msg.reply(f"收到：{msg.treated_msg}")
```

### 有效场景

使用 `CommandValidScenes` 限制命令生效的场景：

```python
from easybot import CommandValidScenes

# 仅频道
@bot.on_command(command="频道命令", valid_scenes=CommandValidScenes.GUILD)

# 仅群聊
@bot.on_command(command="群聊命令", valid_scenes=CommandValidScenes.GROUP)

# 仅单聊
@bot.on_command(command="私聊命令", valid_scenes=CommandValidScenes.C2C)

# 仅私信
@bot.on_command(command="私信命令", valid_scenes=CommandValidScenes.DM)

# 多个场景（位运算）
@bot.on_command(
    command="通用命令",
    valid_scenes=CommandValidScenes.GUILD | CommandValidScenes.GROUP
)

# 所有场景
@bot.on_command(command="全局命令", valid_scenes=CommandValidScenes.ALL)
```

### 短路机制

```python
# is_short_circuit=True（默认）：匹配后停止后续命令处理
@bot.on_command(command="stop", is_short_circuit=True)
async def stop_cmd(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
) -> None:
    await msg.reply("停止处理")

# is_short_circuit=False：继续尝试匹配其他命令
@bot.on_command(command="log", is_short_circuit=False)
async def log_cmd(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
) -> None:
    bot.logger.info(f"记录日志: {msg.treated_msg}")
    # 继续执行后续命令

# is_custom_short_circuit=True：根据返回值决定是否短路
@bot.on_command(command="check", is_custom_short_circuit=True)
async def check_cmd(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
) -> bool:
    if "敏感词" in msg.treated_msg:
        await msg.reply("包含敏感词，停止处理")
        return True  # 返回 True 表示短路
    return False  # 返回 False 继续处理
```

---

## 预处理器

预处理器在所有命令检查之前执行，适合用于日志记录、权限检查等。

### 注册预处理器

```python
@bot.before_command(valid_scenes=CommandValidScenes.ALL)
async def preprocessor(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
) -> None:
    bot.logger.info(f"收到消息: {msg.treated_msg}")
```

### 场景限制

```python
# 仅处理频道消息
@bot.before_command(valid_scenes=CommandValidScenes.GUILD)
async def guild_preprocessor(msg: Model.GuildMessage) -> None:
    bot.logger.info(f"频道消息: {msg.guild_id}")

# 处理群聊和单聊
@bot.before_command(
    valid_scenes=CommandValidScenes.GROUP | CommandValidScenes.C2C
)
async def qq_preprocessor(msg: Model.GroupMessage | Model.C2CMessage) -> None:
    bot.logger.info(f"QQ消息: {msg.treated_msg}")
```

### 预处理器用途

```python
from easybot import CommandValidScenes, Model, StopProcessing

# 消息日志
@bot.before_command(valid_scenes=CommandValidScenes.ALL)
async def log_all(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
) -> None:
    if isinstance(msg, Model.GuildMessage):
        bot.logger.info(f"[频道] {msg.author.username}: {msg.treated_msg}")
    elif isinstance(msg, Model.GroupMessage):
        bot.logger.info(f"[群聊] {msg.group_openid}: {msg.treated_msg}")
    elif isinstance(msg, Model.C2CMessage):
        bot.logger.info(f"[单聊] {msg.author.user_openid}: {msg.treated_msg}")

# 敏感词过滤
@bot.before_command(valid_scenes=CommandValidScenes.ALL)
async def filter_sensitive(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
) -> None:
    sensitive_words = ["违禁词1", "违禁词2"]
    for word in sensitive_words:
        if word in msg.treated_msg:
            await msg.reply("消息包含敏感词")
            raise StopProcessing()  # 停止后续处理

# 用户黑名单
blacklist = set()

@bot.before_command(valid_scenes=CommandValidScenes.ALL)
async def check_blacklist(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
) -> None:
    user_id = msg.author.id if hasattr(msg.author, "id") else msg.author.user_openid
    if user_id in blacklist:
        raise StopProcessing()
```

---

## 权限控制

### 频道管理员权限

```python
@bot.on_command(
    command="管理命令",
    is_require_admin=True,
    admin_error_msg="此命令仅频道管理员可用"
)
async def admin_cmd(msg: Model.GuildMessage) -> None:
    await msg.reply("管理员命令执行")
```

**注意**：`is_require_admin` 仅在频道场景生效，群聊和单聊中不生效。

### 机器人管理员权限

机器人管理员是全局的超管，通过 `BotAdminManager` 管理：

```python
# 添加机器人管理员（支持多个参数）- 异步方法
await bot.bot_admin_manager.add_admin("user_id_1", "user_id_2")

# 批量设置管理员列表（合并式，与现有数据取并集）- 异步方法
await bot.bot_admin_manager.set_bot_admins(["user_id_1", "user_id_2", "user_id_3"])

# 移除管理员（支持多个参数）- 异步方法
await bot.bot_admin_manager.remove_admin("user_id_1")

# 检查是否为管理员 - 同步方法
if bot.bot_admin_manager.is_admin("user_id"):
    print("是机器人管理员")

# 获取所有管理员（返回列表）- 同步方法
admins = bot.bot_admin_manager.bot_admins

# 获取所有管理员（返回集合）- 同步方法
admin_set = bot.bot_admin_manager.get_all_admins()

# 清空所有管理员 - 异步方法
await bot.bot_admin_manager.clear_admins()

# 使用命令装饰器
@bot.on_command(
    command="超管命令",
    is_require_bot_admin=True,
    bot_admin_error_msg="此命令仅机器人管理员可用"
)
async def super_admin_cmd(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
) -> None:
    await msg.reply("超管命令执行")
```

> **注意**: `add_admin()`, `set_bot_admins()`, `remove_admin()`, `clear_admins()` 都是异步方法，需要使用 `await` 调用。`is_admin()`, `bot_admins`, `get_all_admins()` 是同步方法。

### 组合权限

```python
# 同时要求频道管理员和机器人管理员
@bot.on_command(
    command="高级命令",
    is_require_admin=True,
    is_require_bot_admin=True,
)
async def advanced_cmd(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
) -> None:
    await msg.reply("高级命令执行")
```

---

## 插件开发

### 插件文件结构

```
plugins/
├── __init__.py
├── admin.py
├── game.py
└── utils.py
```

### 使用 Plugins 类注册

```python
# plugins/game.py
from easybot import Model, Plugins, CommandValidScenes

@Plugins.on_command(
    command=["game", "游戏"],
    valid_scenes=CommandValidScenes.ALL
)
async def game_cmd(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
) -> None:
    await msg.reply("游戏功能")

@Plugins.before_command(valid_scenes=CommandValidScenes.ALL)
def game_preprocessor(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
) -> None:
    print(f"游戏插件预处理: {msg.treated_msg}")
```

### 自动加载插件

```python
bot = Bot(
    app_id="...",
    app_secret="...",
    auto_load_plugins=True,      # 启用自动加载
    plugins_dir="plugins",       # 插件目录
    plugins_recursive=True,      # 递归扫描子目录
)
```

---

## 插件自动加载

### 启用自动加载

在 Bot 初始化时配置插件自动加载：

```python
bot = Bot(
    app_id="...",
    app_secret="...",
    auto_load_plugins=True,      # 启用自动加载
    plugins_dir="plugins",       # 插件目录（默认 "plugins"）
    plugins_recursive=False,     # 是否递归扫描子目录（默认 False）
)
```

### 加载过程

1. **初始化阶段**：预加载插件以注册 Intent
   - 扫描插件目录中的 `.py` 文件
   - 跳过以 `_` 开头或 `__init__.py` 的文件
   - 执行模块代码，注册命令和预处理器
   - 注册必要的 Intent

2. **启动阶段**：加载插件并输出日志
   - 统计加载的命令和预处理器数量
   - 输出详细的注册信息

### 加载日志示例

```
[INFO] 开始加载插件目录: /path/to/plugins
[INFO] 成功加载插件: admin.py
[INFO] 从Plugins注册 ALL 预处理器：log_all
[INFO] 从Plugins注册指令：[help, 帮助]
[INFO] 从Plugins注册指令：[admin, 管理]
[INFO] 插件注册完成：2 个指令，1 个预处理器
```

### 插件目录结构

#### 单层目录结构

```
plugins/
├── admin.py          # 管理插件
├── game.py           # 游戏插件
└── utils.py          # 工具插件
```

#### 多层目录结构（递归加载）

启用 `plugins_recursive=True` 时：

```
plugins/
├── admin/
│   ├── __init__.py
│   ├── admin.py      # 模块名: admin.admin
│   └── permissions.py # 模块名: admin.permissions
├── game/
│   ├── __init__.py
│   └── dice.py       # 模块名: game.dice
└── utils.py          # 模块名: utils
```

### 手动加载插件

在运行时手动加载插件（适用于动态添加新插件）：

```python
# 运行时加载插件
bot.load_plugins()
```

> **说明**：`load_plugins()` 会重新扫描插件目录并导入**尚未注册的** `.py` 文件。无论 `auto_load_plugins` 设置如何，调用此方法都会执行加载。已加载的插件会被安全跳过，不会产生重复注册。如需更新已有插件代码，请使用 `reload_plugin()`。

---

## 插件热重载

EasyBot 支持插件热重载，无需重启机器人即可更新插件代码。

### 热重载单个插件

```python
# 通过插件名重载
result = bot.reload_plugin("admin")

# 通过命令名重载
result = bot.reload_plugin("help")

# 通过完整模块名重载
result = bot.reload_plugin("admin.admin")
```

### 热重载所有插件

```python
results = bot.reload_all_plugins()
for result in results:
    if result["success"]:
        print(f"插件 {result['module']} 重载成功")
    else:
        print(f"插件 {result['module']} 重载失败: {result['error']}")
```

### 卸载插件

```python
# 卸载指定插件
stats = bot.unload_plugin("admin")
print(f"卸载了 {stats['commands']} 个命令，{stats['preprocessors']} 个预处理器")
```

### 获取已加载插件列表

```python
plugins = bot.get_loaded_plugins()
print(f"已加载的插件: {plugins}")
# 输出: ['admin', 'game', 'utils']
```

### 重载结果结构

`reload_plugin()` 返回 `PluginReloadResult` 字典：

```python
{
    "module": "admin",              # 模块名
    "unloaded": {                   # 卸载的内容
        "commands": 2,
        "preprocessors": 1
    },
    "loaded": {                     # 新加载的内容
        "commands": 3,
        "preprocessors": 1
    },
    "success": True,                # 是否成功
    "error": None                   # 错误信息（失败时）
}
```

失败时的返回：

```python
{
    "module": "nonexistent",
    "success": False,
    "error": "未找到插件或命令: nonexistent",
    "loaded_plugins": ["admin", "game"]  # 当前已加载的插件列表
}
```

### 热重载限制

⚠️ **重要限制**：

1. **仅支持 `@Plugins` 装饰器注册的内容**
   - ✅ 支持：`@Plugins.on_command()`
   - ✅ 支持：`@Plugins.before_command()`
   - ❌ 不支持：`@bot.on_command()`
   - ❌ 不支持：`@bot.before_command()`

2. **模块追踪机制**
   - SDK 会自动追踪每个命令和预处理器的归属模块
   - 热重载时会先卸载旧版本，再加载新版本
   - 修改插件代码后直接调用 `reload_plugin()` 即可生效

3. **依赖关系**
   - 如果插件之间有依赖，重载顺序可能影响结果
   - 建议插件保持独立，避免相互依赖

4. **生命周期钩子触发**
   - `bot.reload_plugin()` / `bot.unload_plugin()` → 自动触发 `on_plugin_unload` + `on_plugin_load` 钩子 ✅
   - `bot.reload_all_plugins()` → 依次触发每个插件的钩子 ✅
   - `Plugins.reload_plugin()` / `Plugins.unload_plugin()`（类方法）→ 仅数据操作，不触发钩子
   - Bot 关闭（`stop()` / Ctrl+C）→ 自动触发所有插件的 `on_plugin_unload` ✅

### 热重载使用场景

```python
# 开发环境：修改插件后立即重载
@bot.on_command(command="reload")
async def reload_cmd(msg: Model.GuildMessage):
    result = bot.reload_plugin("game")
    if result["success"]:
        await msg.reply(f"重载成功，加载了 {result['loaded']['commands']} 个命令")
    else:
        await msg.reply(f"重载失败: {result['error']}")

# 生产环境：定时检查更新并重载
@bot.on_timer(interval=300)  # 每5分钟检查一次
async def check_updates(event: Model.TimerEvent):
    # 检查文件修改时间，如有更新则重载
    pass
```

---

## 生命周期钩子

插件模块可以定义可选的**生命周期钩子函数**，在加载和卸载时自动被 SDK 调用，用于执行初始化或清理操作。

### 支持的钩子函数

| 钩子函数 | 触发时机 | 参数 | 返回值 |
|---------|---------|------|--------|
| `on_plugin_load(bot)` | 插件导入完成后（同步立即执行）以及 Bot 启动后（异步延迟） | `Bot` 实例 | 无（同步）或 `Awaitable[None]`（异步） |
| `on_plugin_unload(bot)` | 卸载插件前 + Bot 关闭时 | `Bot` 实例 | 无（同步）或 `Awaitable[None]`（异步） |

> **注意**：这两个函数名是 SDK 约定的特殊标识符，不会被注册为命令。

### 基本用法

```python
# plugins/my_plugin.py
from easybot import CommandValidScenes, Model, Plugins

_db_connection = None

def on_plugin_load(bot):
    """插件加载时初始化资源"""
    global _db_connection
    _db_connection = create_database_connection()
    bot.logger.info("my_plugin: 数据库连接已建立")


def on_plugin_unload(bot):
    """插件卸载时清理资源"""
    global _db_connection
    if _db_connection:
        _db_connection.close()
        _db_connection = None
    bot.logger.info("my_plugin: 资源已释放")


@Plugins.on_command(command="/query", valid_scenes=CommandValidScenes.GUILD)
async def query_cmd(msg: Model.GuildMessage) -> None:
    await msg.reply(f"查询结果")
```

### 异步钩子

如果钩子需要执行异步操作，可定义为 `async def`：

```python
_async_resource = None

async def on_plugin_load(bot):
    """异步钩子：将在 Bot 启动完成后的 _trigger_startup 阶段调用"""
    global _async_resource
    _async_resource = await async_init_resource()


async def on_plugin_unload(bot):
    """异步卸载钩子"""
    global _async_resource
    if _async_resource:
        await _async_resource.close()
        _async_resource = None
```

**异步钩子的调用时机**：
- 同步钩子 → 插件导入后**立即**调用
- 异步钩子 → 延迟到 Bot 的 `_trigger_startup` 阶段（WebSocket 连接建立后）

### 触发保证

SDK 保证以下场景都会触发 `on_plugin_unload`：
1. **手动卸载/热重载时**：`bot.unload_plugin()` / `bot.reload_plugin()`
2. **Bot 关闭时**：`bot.stop()` 或 Ctrl+C 信号

### 典型使用场景

- **数据库/Redis 连接管理**：加载时建立连接，卸载时关闭
- **定时任务注册/取消**：加载时注册周期性任务，卸载时取消
- **配置热加载**：加载时读取配置文件，卸载时保存状态
- **依赖检查**：加载时验证外部服务可用性

---

## 动态管理

### 查看所有命令

```python
# 获取所有命令（包括禁用的）
commands = Plugins.get_all_commands()
for cmd in commands:
    status = "✅" if cmd.enabled else "❌"
    names = ", ".join(cmd.command) if cmd.command else "正则"
    print(f"{status} {cmd.func.__name__}: {names}")
```

### 启用/禁用命令

```python
# 禁用命令
Plugins.disable_command("game_cmd")

# 启用命令
Plugins.enable_command("game_cmd")

# 检查命令状态
is_enabled = Plugins.is_command_enabled("game_cmd")
```

### 移除命令

```python
# 移除命令
Plugins.remove_command("old_cmd")
```

### 查找命令

```python
# 根据函数名查找命令对象
cmd = Plugins.find_command("game_cmd")
if cmd:
    print(f"命令: {cmd.command}")
    print(f"启用: {cmd.enabled}")
```

### 插件模块管理

#### 获取插件的命令列表

```python
# 获取指定插件注册的所有命令函数名
commands = bot.get_plugin_commands("admin")
print(f"admin 插件的命令: {commands}")
# 输出: ['help_cmd', 'admin_cmd']
```

#### 获取插件的预处理器列表

```python
# 获取指定插件注册的所有预处理器函数名
preprocessors = bot.get_plugin_preprocessors("admin")
print(f"admin 插件的预处理器: {preprocessors}")
# 输出: ['log_all']
```

#### 清空所有插件

```python
# 清空所有已注册的命令和预处理器
stats = bot.clear_all_plugins()
print(f"清空了 {stats['commands']} 个命令，{stats['preprocessors']} 个预处理器")
```

---

## 类型定义

### PluginStats

插件统计信息，用于表示命令和预处理器的数量：

```python
class PluginStats(TypedDict):
    commands: int        # 命令数量
    preprocessors: int   # 预处理器数量
```

### PluginReloadResult

插件重载结果，包含详细的加载信息：

```python
class PluginReloadResult(TypedDict, total=False):
    module: str                    # 模块名
    unloaded: PluginStats          # 卸载的内容统计
    loaded: PluginStats            # 新加载的内容统计
    success: bool                  # 是否成功
    error: str | None              # 错误信息（失败时）
    loaded_plugins: list[str]      # 当前已加载的插件列表（失败时）
```

### CommandValidScenes

命令有效场景枚举：

```python
class CommandValidScenes(int):
    GUILD = 1      # 频道
    DM = 2         # 频道私信
    GROUP = 4      # QQ群聊
    C2C = 8        # QQ单聊
    ALL = 15       # 所有场景（GUILD | DM | GROUP | C2C）
```

### BotCommandObject

命令对象，存储命令的所有配置信息：

```python
class BotCommandObject:
    command: Iterable[str] | None     # 触发命令列表
    regex: Iterable[Pattern] | None   # 正则表达式列表
    func: Callable                     # 回调函数
    treat: bool                        # 是否处理 treated_msg
    at: bool                           # 是否需要@
    short_circuit: bool                # 是否短路
    is_custom_short_circuit: bool      # 自定义短路
    admin: bool                        # 是否需要频道管理员
    admin_error_msg: str | None        # 权限不足提示
    valid_scenes: CommandValidScenes   # 有效场景
    enabled: bool                      # 是否启用
    is_require_bot_admin: bool         # 是否需要机器人管理员
    bot_admin_error_msg: str | None    # 机器人管理员权限不足提示
```

---

## 最佳实践

### 插件文件命名

- 使用小写字母和下划线：`admin_tools.py`、`game_dice.py`
- 避免使用中文或特殊字符
- 文件名应能反映插件的功能

### 插件模块组织

```python
# plugins/game.py - 游戏插件示例

from easybot import Plugins, CommandValidScenes, Model

# 插件内部配置
GAME_CONFIG = {
    "max_players": 10,
    "timeout": 60
}

# 预处理器：日志记录
@Plugins.before_command(valid_scenes=CommandValidScenes.ALL)
async def game_logger(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
) -> None:
    """记录游戏相关消息"""
    pass

# 命令：开始游戏
@Plugins.on_command(
    command=["开始游戏", "start"],
    valid_scenes=CommandValidScenes.ALL
)
async def start_game(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
) -> None:
    """开始一局新游戏"""
    pass

# 命令：游戏帮助
@Plugins.on_command(
    command=["游戏帮助", "game_help"],
    valid_scenes=CommandValidScenes.ALL
)
async def game_help(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
) -> None:
    """显示游戏帮助信息"""
    pass
```

### 避免循环依赖

```python
# ❌ 不好的做法：插件之间相互依赖
# plugins/admin.py
from .game import start_game  # 导入其他插件的函数

# ✅ 好的做法：插件保持独立
# plugins/admin.py
# 只使用 SDK 提供的公共 API
```

### 使用类型提示

```python
# ✅ 始终为消息参数添加类型提示
@Plugins.on_command(command="test", valid_scenes=CommandValidScenes.GUILD)
async def test_cmd(msg: Model.GuildMessage) -> None:
    print(msg.channel_id)  # IDE 可以正确推断

# ❌ 避免缺少类型提示
@Plugins.on_command(command="test", valid_scenes=CommandValidScenes.GUILD)
async def test_cmd(msg):  # 缺少类型提示
    pass
```

### 错误处理

```python
@Plugins.on_command(command="risky", valid_scenes=CommandValidScenes.ALL)
async def risky_cmd(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
) -> None:
    try:
        # 可能失败的操作
        result = await some_operation()
        await msg.reply(f"结果: {result}")
    except Exception as e:
        # 记录错误并给用户友好的提示
        await msg.reply("操作失败，请稍后重试")
        # 不要让异常传播到 SDK 层
```

### 热重载注意事项

1. **避免全局状态**
   ```python
   # ❌ 不好的做法：使用全局变量
   game_state = {}
   
   @Plugins.on_command(command="join")
   async def join(msg):
       game_state[msg.author.id] = True
   
   # ✅ 好的做法：使用会话管理
   @Plugins.on_command(command="join")
   async def join(msg):
       with bot.session.bind(msg) as s:
           await s.new(Scope.USER, "joined", True)
   ```

2. **模块级初始化**
   ```python
   # ❌ 不好的做法：模块加载时执行耗时操作
   expensive_data = load_large_database()  # 模块导入时执行
   
   # ✅ 好的做法：延迟初始化
   _data_cache = None
   
   def get_data():
       global _data_cache
       if _data_cache is None:
           _data_cache = load_large_database()
       return _data_cache
   ```

### 性能优化

1. **避免在预处理器中执行耗时操作**
   ```python
   # ❌ 不好的做法
   @Plugins.before_command(valid_scenes=CommandValidScenes.ALL)
   async def slow_preprocessor(msg):
       await asyncio.sleep(5)  # 阻塞所有命令处理
   
   # ✅ 好的做法
   @Plugins.before_command(valid_scenes=CommandValidScenes.ALL)
   async def fast_preprocessor(msg):
       # 快速检查，不阻塞
       if should_skip(msg):
           raise StopProcessing()
   ```

2. **合理使用短路机制**
   ```python
   # 日志记录命令：不短路，继续执行后续命令
   @Plugins.on_command(
       command="log",
       is_short_circuit=False,
       valid_scenes=CommandValidScenes.ALL
   )
   async def log_cmd(msg):
       bot.logger.info(f"日志: {msg.treated_msg}")
       # 继续执行其他命令
   
   # 停止命令：短路，停止后续处理
   @Plugins.on_command(
       command="stop",
       is_short_circuit=True,
       valid_scenes=CommandValidScenes.ALL
   )
   async def stop_cmd(msg):
       await msg.reply("已停止")
       # 不再执行其他命令
   ```
