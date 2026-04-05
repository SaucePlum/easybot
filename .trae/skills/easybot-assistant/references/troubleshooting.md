# EasyBot 故障排除指南

## 目录

1. [常见错误码](#常见错误码)
2. [连接问题](#连接问题)
3. [消息发送问题](#消息发送问题)
4. [权限问题](#权限问题)
5. [调试技巧](#调试技巧)
6. [常见问题 FAQ](#常见问题-faq)

---

## 常见错误码

### API 错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| 10001 | 系统错误 | 稍后重试，如持续出现请联系官方 |
| 10002 | 参数错误 | 检查 API 参数是否正确 |
| 10003 | 资源不存在 | 检查 ID 是否正确，资源是否已删除 |
| 10004 | 资源已存在 | 检查是否重复创建 |
| 10005 | 权限不足 | 检查机器人权限配置 |
| 10006 | 频率限制 | 降低请求频率，实现重试机制 |
| 10007 | Token 过期 | SDK 会自动刷新，检查网络连接 |
| 10008 | Token 无效 | 检查 AppID 和 Secret 是否正确 |
| 10009 | 签名错误 | 检查 Secret 是否正确 |
| 10010 | 机器人被封禁 | 联系官方客服 |

### SDK 异常类型

```python
from easybot import (
    EasyBotException,    # 基础异常
    APIError,            # API 调用错误
    AuthenticationError, # 认证错误
    NetworkError,        # 网络错误
    RateLimitError,      # 频率限制
    ValidationError,     # 参数验证错误
    PermissionError,     # 权限错误
    WaitTimeoutError,    # 等待超时
    WaitError,           # 等待错误
    StopProcessing,      # 停止处理
)
```

---

## 连接问题

### WebSocket 连接失败

**症状：**
- 日志显示 "WebSocket connection failed"
- 机器人无法接收事件

**排查步骤：**

1. 检查网络连接
```python
# 测试网络
import asyncio
import aiohttp

async def test_connection():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.sgroup.qq.com") as resp:
                print(f"连接状态: {resp.status}")
    except Exception as e:
        print(f"连接失败: {e}")

asyncio.run(test_connection())
```

2. 检查 AppID 和 Secret
```python
# 验证凭证
bot = Bot(app_id="your_id", app_secret="your_secret", is_debug=True)
# 查看启动日志是否有认证错误
```

3. 检查防火墙设置
- 确保允许访问 `api.sgroup.qq.com`
- 确保允许 WebSocket 连接

### Webhook 连接问题

**症状：**
- Webhook 端点无法访问
- 收不到事件推送

**排查步骤：**

1. 检查端口是否被占用
```bash
# Windows
netstat -ano | findstr :8080

# Linux
netstat -tlnp | grep 8080
```

2. 检查公网 IP 是否正确
- Webhook 需要公网 IP
- 确保端口已开放

3. 使用远程 Webhook
```python
# 如果没有公网 IP，使用远程 Webhook
bot = Bot(
    app_id="...",
    app_secret="...",
    protocol=Proto.remote_webhook(url="wss://your-server.com")
)
```

### 连接频繁断开

**可能原因：**
- 网络不稳定
- 心跳超时
- 服务器端问题

**解决方案：**

```python
# 调整心跳和超时参数
bot = Bot(
    app_id="...",
    app_secret="...",
    protocol=Proto.websocket(
        connect_timeout=60,  # 增加连接超时
        disable_reconnect_on_not_recv_msg=1800,  # 增加无消息超时
    )
)
```

---

## 消息发送问题

### 消息发送失败

**症状：**
- `send_guild_message` 返回错误
- 消息未送达

**常见原因：**

1. **msg_id 过期**（超过5分钟）
```python
# 错误：msg_id 过期
await bot.api.send_guild_message(
    channel_id="xxx",
    content="回复",
    msg_id=old_msg_id  # 超过5分钟
)

# 解决：不传 msg_id，使用主动消息
await bot.api.send_guild_message(
    channel_id="xxx",
    content="主动消息"
)
```

2. **消息内容为空**
```python
# 错误：内容为空
await bot.api.send_guild_message(channel_id="xxx", content="")

# 解决：提供有效内容
await bot.api.send_guild_message(channel_id="xxx", content="有效内容")
```

3. **群聊消息缺少文本**
```python
# 错误：群聊纯图片
await bot.api.send_group_message(
    group_openid="xxx",
    content=MessagesModel.Message(image="url")  # 群聊必须有文本
)

# 解决：添加文本
await bot.api.send_group_message(
    group_openid="xxx",
    content=MessagesModel.Message(content="图片", image="url")
)
```

### 图片发送失败

**可能原因：**
- 图片 URL 不可访问
- 图片格式不支持
- 图片大小超限

**解决方案：**

```python
# 使用本地文件
await bot.api.send_guild_message(
    channel_id="xxx",
    content="图片",
    file_image="./image.png"
)

# 或上传后发送
result = await bot.api.upload_media(
    file_type=1,
    file_data="./image.png",
    user_openid="xxx"
)
await bot.api.send_c2c_message(
    openid="xxx",
    content=MessagesModel.MessageMedia(file_info=result.file_info),
    event_id="event_id"
)
```

### 消息被审核拦截

**症状：**
- 消息发送成功但用户看不到
- 收到审核事件

**解决方案：**

```python
# 监听审核事件
@bot.on_message_audit_reject
async def on_audit_reject(event):
    bot.logger.warning(f"消息被拒绝: {event}")

@bot.on_message_audit_pass
async def on_audit_pass(event):
    bot.logger.info(f"消息审核通过: {event}")
```

---

## 权限问题

### 频道权限不足

**症状：**
- API 返回权限错误
- 某些功能无法使用

**解决方案：**

1. 检查机器人权限
```python
# 获取机器人权限
permissions = await bot.api.get_guild_api_permissions(guild_id)
for api in permissions.apis:
    print(f"{api.path}: {api.auth_status}")
```

2. 申请权限
```python
# 发送权限申请链接
await bot.api.demand_guild_api_permission(
    guild_id="xxx",
    channel_id="xxx",
    api_path="/guilds/{guild_id}/members/{user_id}",
    api_method="DELETE",
    desc="踢人功能需要此权限"
)
```

### 命令权限问题

**症状：**
- 命令不触发
- 权限检查失败

**排查步骤：**

1. 检查命令场景限制
```python
# 确保命令在正确的场景
@bot.on_command(
    command="测试",
    valid_scenes=CommandValidScenes.ALL  # 确保包含目标场景
)
```

2. 检查管理员权限
```python
# 频道管理员检查
@bot.on_command(
    command="管理",
    is_require_admin=True,
    admin_error_msg="需要频道管理员权限"
)

# 机器人管理员检查
@bot.on_command(
    command="超管",
    is_require_bot_admin=True,
    bot_admin_error_msg="需要机器人管理员权限"
)

# 添加机器人管理员
bot.bot_admin_manager.add_admin("user_id")
```

---

## 调试技巧

### 开启调试模式

```python
bot = Bot(
    app_id="...",
    app_secret="...",
    is_debug=True,  # 开启调试日志
)
```

### 查看详细日志

```python
import logging

# 设置全局日志级别
logging.basicConfig(level=logging.DEBUG)

# 或只设置 EasyBot 日志
logging.getLogger("easybot").setLevel(logging.DEBUG)
```

### 打印事件数据

```python
@bot.on_all_intent_events
async def debug_all(event):
    import json
    bot.logger.debug(f"事件数据: {json.dumps(event.to_dict(), ensure_ascii=False, indent=2)}")
```

### 测试 API 连接

```python
async def test_api():
    try:
        me = await bot.api.get_me()
        print(f"机器人ID: {me.id}")
        print(f"机器人名称: {me.username}")
        
        gateway = await bot.api.get_gateway_bot()
        print(f"Gateway URL: {gateway.url}")
        print(f"建议分片数: {gateway.shards}")
        
    except Exception as e:
        print(f"API 测试失败: {e}")

# 在启动前测试
import asyncio
asyncio.run(test_api())
```

### 使用沙箱环境

```python
bot = Bot(
    app_id="...",
    app_secret="...",
    is_sandbox=True,  # 使用沙箱环境测试
)
```

---

## 常见问题 FAQ

### Q: 机器人收不到消息？

**A:** 检查以下几点：
1. 是否正确注册了事件处理器
2. 是否订阅了正确的 Intent
3. 消息是否@了机器人（公域机器人）
4. 是否在沙箱环境测试

```python
# 确保注册了事件处理器
@bot.on_guild_message
async def handle(msg):
    print(f"收到消息: {msg.treated_msg}")  # 确认能收到
```

### Q: wait_for 一直等待？

**A:** 检查：
1. 是否正确绑定了消息对象
2. 用户回复是否匹配条件
3. 是否有其他处理器拦截了消息

```python
# 正确使用 wait_for
with bot.session.bind(msg) as s:
    result = await s.wait_for(
        scopes=Scope.USER,  # 确保作用域正确
        timeout=30
    )
```

### Q: 会话数据丢失？

**A:** 检查：
1. `sdk_data` 目录是否存在
2. 是否有写入权限
3. 程序是否正常退出

```python
# 手动保存会话
bot.session.commit_data()
```

### Q: 插件不加载？

**A:** 检查：
1. `auto_load_plugins` 是否为 True
2. 插件目录路径是否正确
3. 插件文件是否包含 `register` 函数或使用了装饰器

```python
bot = Bot(
    app_id="...",
    app_secret="...",
    auto_load_plugins=True,
    plugins_dir="plugins",  # 确保路径正确
)
```

### Q: 如何处理大量消息？

**A:** 使用队列和异步处理：

```python
import asyncio
from collections import deque

message_queue = deque()

async def process_queue():
    while True:
        if message_queue:
            msg = message_queue.popleft()
            await process_message(msg)
        await asyncio.sleep(0.01)

@bot.on_guild_message
async def handle(msg):
    message_queue.append(msg)

# 启动队列处理
asyncio.create_task(process_queue())
```

### Q: 如何实现定时任务？

**A:** 使用 `on_timer` 装饰器：

```python
@bot.on_timer(interval=60)  # 每60秒执行
async def scheduled_task(event):
    bot.logger.info(f"定时任务执行，第 {event.tick_count} 次")
```

### Q: 如何优雅关闭？

**A:** 使用生命周期事件：

```python
@bot.on_shutdown
async def cleanup(event):
    bot.logger.info("正在清理资源...")
    await bot.session.commit_data()  # 保存会话
    # 其他清理操作
    bot.logger.info("清理完成")
```

---

## 获取帮助

如果以上方法无法解决问题：

1. 查看官方文档：https://bot.q.qq.com/wiki/
2. 查看 SDK 源码和示例
3. 提交 Issue 到 GitHub
4. 联系技术支持
