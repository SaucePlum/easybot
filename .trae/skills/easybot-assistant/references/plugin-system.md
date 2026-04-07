# EasyBot 插件系统完整文档

## 目录

1. [概述](#概述)
2. [命令注册](#命令注册)
3. [预处理器](#预处理器)
4. [权限控制](#权限控制)
5. [插件开发](#插件开发)
6. [动态管理](#动态管理)

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

---

## BotCommandObject 属性

**重要**：`BotCommandObject` 的属性名与装饰器参数名不同！

| 装饰器参数名 | BotCommandObject 属性名 |
|-------------|------------------------|
| `is_treat` | `treat` |
| `is_require_at` | `at` |
| `is_short_circuit` | `short_circuit` |
| `is_require_admin` | `admin` |

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

## StopProcessing 异常

用于在预处理器中停止后续处理：

```python
from easybot import StopProcessing

@bot.before_command(valid_scenes=CommandValidScenes.ALL)
async def check_blacklist(
    msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage,
) -> None:
    if user_in_blacklist:
        raise StopProcessing()  # 停止后续命令处理
```
