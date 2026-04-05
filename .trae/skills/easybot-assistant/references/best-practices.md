# EasyBot 最佳实践指南

## 目录

1. [代码规范](#代码规范)
2. [错误处理](#错误处理)
3. [性能优化](#性能优化)
4. [安全实践](#安全实践)

---

## 代码规范

### 项目结构

推荐的项目目录结构：

```
my_bot/
├── main.py              # 入口文件
├── config.py            # 配置管理
├── plugins/             # 插件目录
│   ├── __init__.py
│   ├── admin.py
│   ├── game.py
│   └── utils.py
├── utils/               # 工具函数
│   ├── __init__.py
│   └── helpers.py
├── sdk_data/            # SDK 数据目录
│   ├── bot_admins.yaml
│   └── sessions.pickle
├── requirements.txt
└── .env                 # 环境变量
```

### 配置管理

使用环境变量管理敏感配置：

```python
# config.py
import os
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv("EASYBOT_APP_ID")
APP_SECRET = os.getenv("EASYBOT_APP_SECRET")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
```

```bash
# .env
EASYBOT_APP_ID=your_app_id
EASYBOT_APP_SECRET=your_app_secret
DEBUG=true
```

### 类型注解

始终使用类型注解：

```python
from easybot import Bot, Model, CommandValidScenes
from typing import Optional

bot: Bot = Bot(app_id="...", app_secret="...")

@bot.on_guild_message
async def handle_guild(msg: Model.GuildMessage) -> None:
    await msg.reply("收到")

@bot.on_command(command="test")
async def test_cmd(msg: Model.MessageBase) -> None:
    result: Optional[str] = process_message(msg.treated_msg)
    if result:
        await msg.reply(result)

def process_message(text: str) -> Optional[str]:
    if not text:
        return None
    return text.upper()
```

### 异步编程规范

```python
# 正确：使用 async/await
@bot.on_guild_message
async def handle(msg: Model.GuildMessage) -> None:
    result = await some_async_operation()
    await msg.reply(result)

# 错误：阻塞事件循环
@bot.on_guild_message
async def handle(msg: Model.GuildMessage) -> None:
    import time
    time.sleep(5)  # 阻塞！
    await msg.reply("完成")

# 正确：使用异步等待
@bot.on_guild_message
async def handle(msg: Model.GuildMessage) -> None:
    import asyncio
    await asyncio.sleep(5)  # 非阻塞
    await msg.reply("完成")
```

### 日志规范

```python
# 使用 SDK 提供的日志器
bot.logger.debug("调试信息")
bot.logger.info("普通信息")
bot.logger.warning("警告信息")
bot.logger.error("错误信息")

# 带模块的日志器
logger = bot.logger.with_module("game")
logger.info("游戏模块日志")

# 记录上下文信息
@bot.on_guild_message
async def handle(msg: Model.GuildMessage) -> None:
    bot.logger.info(
        f"[频道消息] guild={msg.guild_id}, "
        f"channel={msg.channel_id}, "
        f"user={msg.author.id}: {msg.treated_msg}"
    )
```

---

## 错误处理

### 异常捕获

```python
from easybot import (
    EasyBotException,
    APIError,
    AuthenticationError,
    NetworkError,
    RateLimitError,
    ValidationError,
    WaitTimeoutError,
    WaitError,
)

@bot.on_command(command="test")
async def test_cmd(msg):
    try:
        result = await bot.api.get_guild("invalid_id")
        await msg.reply(f"结果: {result}")
    
    except AuthenticationError:
        await msg.reply("认证失败，请检查 AppID 和 Secret")
    
    except RateLimitError:
        await msg.reply("请求过于频繁，请稍后再试")
    
    except NetworkError as e:
        bot.logger.error(f"网络错误: {e}")
        await msg.reply("网络连接失败")
    
    except APIError as e:
        bot.logger.error(f"API 错误: {e}")
        await msg.reply(f"API 调用失败: {e}")
    
    except Exception as e:
        bot.logger.exception(f"未知错误: {e}")
        await msg.reply("发生未知错误")
```

### wait_for 错误处理

```python
from easybot import Scope, WaitTimeoutError, WaitError

@bot.on_command(command="游戏")
async def game(msg):
    with bot.session.bind(msg) as s:
        await msg.reply("请在30秒内回复")
        
        try:
            result = await s.wait_for(
                scopes=Scope.USER,
                timeout=30
            )
            await msg.reply(f"收到: {result.content}")
        
        except WaitTimeoutError:
            await msg.reply("⏰ 等待超时")
        
        except WaitError as e:
            bot.logger.error(f"等待错误: {e}")
            await msg.reply("等待过程出错")
```

### 全局异常处理

```python
@bot.on_guild_message
async def handle(msg: Model.GuildMessage):
    try:
        await process_message(msg)
    except Exception as e:
        bot.logger.exception(f"处理消息时出错: {e}")
        try:
            await msg.reply("处理消息时发生错误")
        except Exception:
            pass  # 发送错误消息失败时忽略

async def process_message(msg: Model.MessageBase) -> None:
    # 业务逻辑
    pass
```

### 重试机制

```python
import asyncio
from typing import TypeVar, Callable

T = TypeVar('T')

async def retry_async(
    func: Callable[..., T],
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0
) -> T:
    """带指数退避的重试装饰器"""
    last_error = None
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                wait_time = delay * (backoff ** attempt)
                await asyncio.sleep(wait_time)
    raise last_error

# 使用
result = await retry_async(
    lambda: bot.api.send_guild_message(channel_id="xxx", content="test"),
    max_retries=3
)
```

---

## 性能优化

### 并发处理

```python
import asyncio

# 并发发送多条消息
async def broadcast_messages(channel_ids: list[str], content: str):
    tasks = [
        bot.api.send_guild_message(channel_id=ch_id, content=content)
        for ch_id in channel_ids
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for ch_id, result in zip(channel_ids, results):
        if isinstance(result, Exception):
            bot.logger.error(f"发送到 {ch_id} 失败: {result}")
        else:
            bot.logger.info(f"发送到 {ch_id} 成功")
```

### 缓存策略

```python
from functools import lru_cache
from typing import Optional
import time

# 内存缓存
cache: dict[str, tuple[float, any]] = {}

def get_cached(key: str, ttl: int = 300) -> Optional[any]:
    """获取缓存值"""
    if key in cache:
        expire_time, value = cache[key]
        if time.time() < expire_time:
            return value
        del cache[key]
    return None

def set_cached(key: str, value: any, ttl: int = 300) -> None:
    """设置缓存值"""
    cache[key] = (time.time() + ttl, value)

# 使用 LRU 缓存
@lru_cache(maxsize=1000)
def get_user_info(user_id: str) -> dict:
    # 获取用户信息（会被缓存）
    return {"id": user_id, "name": "User"}
```

### 批量操作

```python
# 批量获取成员
async def get_all_members(guild_id: str) -> list:
    all_members = []
    after = "0"
    
    while True:
        members = await bot.api.get_guild_members(
            guild_id=guild_id,
            after=after,
            limit=100
        )
        if not members:
            break
        all_members.extend(members)
        after = members[-1].user.id
        
        # 避免请求过快
        await asyncio.sleep(0.1)
    
    return all_members
```

### 资源管理

```python
# 使用上下文管理器
async def process_file(file_path: str):
    async with aiofiles.open(file_path, 'rb') as f:
        data = await f.read()
    # 文件自动关闭

# 连接池管理
class HttpClientPool:
    _instance = None
    _client = None
    
    @classmethod
    async def get_client(cls):
        if cls._client is None:
            cls._client = aiohttp.ClientSession()
        return cls._client
    
    @classmethod
    async def close(cls):
        if cls._client:
            await cls._client.close()
            cls._client = None
```

---

## 安全实践

### 敏感信息保护

```python
# 不要硬编码敏感信息
# 错误
bot = Bot(app_id="123456", app_secret="secret123")

# 正确：使用环境变量
import os
bot = Bot(
    app_id=os.getenv("EASYBOT_APP_ID"),
    app_secret=os.getenv("EASYBOT_APP_SECRET")
)

# 日志脱敏
def sanitize_for_log(text: str) -> str:
    """脱敏敏感信息"""
    import re
    # 隐藏手机号
    text = re.sub(r'(\d{3})\d{4}(\d{4})', r'\1****\2', text)
    # 隐藏邮箱
    text = re.sub(r'(\w{2})\w+(@\w+)', r'\1***\2', text)
    return text

bot.logger.info(f"用户输入: {sanitize_for_log(user_input)}")
```

### 输入验证

```python
import re
from typing import Optional

def validate_user_input(text: str, max_length: int = 500) -> Optional[str]:
    """验证并清理用户输入"""
    if not text:
        return None
    
    # 限制长度
    if len(text) > max_length:
        return None
    
    # 移除危险字符
    text = text.strip()
    
    # 检查是否包含敏感词
    sensitive_words = ["敏感词1", "敏感词2"]
    for word in sensitive_words:
        if word in text:
            return None
    
    return text

@bot.on_command(command="提交")
async def submit(msg):
    cleaned = validate_user_input(msg.treated_msg)
    if not cleaned:
        await msg.reply("输入无效")
        return
    
    # 处理有效输入
    await process_input(cleaned)
```

### 权限检查

```python
from easybot import CommandValidScenes

# 命令级别权限
@bot.on_command(
    command="管理",
    is_require_admin=True,
    admin_error_msg="此命令仅频道管理员可用"
)
async def admin_cmd(msg):
    await msg.reply("管理员命令")

# 自定义权限检查
async def check_permission(msg, required_level: int) -> bool:
    """检查用户权限等级"""
    user_id = msg.author.id if hasattr(msg.author, 'id') else msg.author.user_openid
    
    # 从数据库或缓存获取用户等级
    user_level = await get_user_level(user_id)
    
    return user_level >= required_level

@bot.on_command(command="高级功能")
async def advanced_cmd(msg):
    if not await check_permission(msg, required_level=5):
        await msg.reply("权限不足")
        return
    
    await msg.reply("高级功能执行")
```

### 防止滥用

```python
from collections import defaultdict
import time

# 命令频率限制
rate_limits: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT = 5  # 每分钟最多5次
RATE_WINDOW = 60  # 60秒窗口

def check_rate_limit(user_id: str) -> bool:
    """检查用户是否超过频率限制"""
    now = time.time()
    user_calls = rate_limits[user_id]
    
    # 清理过期记录
    user_calls[:] = [t for t in user_calls if now - t < RATE_WINDOW]
    
    if len(user_calls) >= RATE_LIMIT:
        return False
    
    user_calls.append(now)
    return True

@bot.before_command(valid_scenes=CommandValidScenes.ALL)
async def rate_limit_check(msg):
    user_id = msg.author.id if hasattr(msg.author, 'id') else msg.author.user_openid
    
    if not check_rate_limit(user_id):
        await msg.reply("操作过于频繁，请稍后再试")
        raise StopProcessing()
```

### 安全配置

```python
# 生产环境配置
bot = Bot(
    app_id=os.getenv("EASYBOT_APP_ID"),
    app_secret=os.getenv("EASYBOT_APP_SECRET"),
    is_debug=False,  # 关闭调试模式
    is_sandbox=False,  # 关闭沙箱模式
    is_log_error=True,  # 记录错误日志
    no_permission_warning=True,  # 权限警告
)

# 禁止在日志中输出敏感信息
import logging
logging.getLogger("easybot").setLevel(logging.INFO)  # 不输出 DEBUG 日志
```
