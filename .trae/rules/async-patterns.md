---
alwaysApply: true
description: 异步编程规范，涵盖 asyncio 使用、资源管理、HTTP 客户端和并发控制
---

# 异步编程规范

## 基本原则

### 异步优先
- 所有 I/O 操作必须使用 `async/await` 语法
- 网络请求、文件读写等阻塞操作必须在异步上下文中执行
- **禁止**在异步代码中使用同步阻塞调用（如 `requests.get()`, `time.sleep()`）

### 事件循环管理
- 入口点使用 `asyncio.run()` 启动事件循环（参考 Bot.start()）
- 需要外部管理事件循环时提供 `start_async()` 方法
- 不要手动创建和销毁事件循环（除非有特殊需求）

## 资源管理模式

### HTTP 客户端生命周期
```python
class API:
    def __init__(self, bot: "Bot"):
        self._http = None  # 延迟初始化

    async def _get_http(self) -> HTTPClient:
        """延迟创建，避免初始化时无事件循环"""
        if self._http is None:
            self._http = HTTPClient(self._bot)
        return self._http

    async def close(self) -> None:
        """显式关闭，释放连接池"""
        if self._http:
            await self._http.close()
```

### 上下文管理器支持
支持 `async with` 语法的类必须实现 `__aenter__` 和 `__aexit__`：
```python
async def __aenter__(self) -> "Bot":
    return self

async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
    await self.stop_async()
    return False
```

### 资源清理顺序
在关闭方法中按依赖关系逆序清理：
1. 先关闭业务逻辑（生命周期管理器）
2. 再关闭 API 客户端
3. 最后关闭协议连接
4. 每个清理步骤都使用 try-except 避免单个失败导致整体中断

## 异步方法设计

### 同步/异步双版本
为需要在外部管理事件循环的场景提供双版本：
```python
def start(self) -> None:
    """同步版本：内部调用 asyncio.run()"""
    try:
        asyncio.run(self.start_async())
    except KeyboardInterrupt:
        # 处理中断信号
        pass

async def start_async(self) -> None:
    """异步版本：供外部事件循环调用"""
    # 实际启动逻辑
    pass
```

### 错误处理模式
```python
async def some_operation(self):
    try:
        result = await self.api.call()
        return result
    except APIError as e:
        self.logger.error(f"API 调用失败: {e}")
        raise
    except Exception as e:
        self.logger.exception(f"未预期的异常: {e}")
        raise
```

## 并发控制

### 任务调度
- 使用 `asyncio.create_task()` 创建并发任务
- 对于需要等待的任务集合，使用 `asyncio.gather()` 或 `asyncio.wait()`
- 避免使用 `asyncio.ensure_future()`（已不推荐）

### 防止阻塞
- CPU 密集型操作使用 `loop.run_in_executor()` 在线程池中执行
- 文件 I/O 使用 `aiofiles` 或 `run_in_executor()`
- 设置合理的超时时间避免永久等待：
```python
try:
    result = await asyncio.wait_for(some_coro(), timeout=30.0)
except asyncio.TimeoutError:
    self.logger.warning("操作超时")
```

### 共享状态保护
- 异步代码中的共享可变状态需要使用 `asyncio.Lock` 保护
- 日志系统的共享 handler 已内置线程安全机制（参考 LoggerManager）

## WebSocket 连接管理

### 连接生命周期
- 使用 `aiohttp.ClientWebSocketResponse` 进行 WebSocket 通信
- 实现自动重连机制（配置重试次数）
- 心跳检测保持连接活跃
- 优雅关闭：发送关闭帧 → 等待确认 → 清理资源

### 消息处理
- 消息接收和处理解耦
- 使用事件分发器将消息路由到对应处理器
- 处理器执行异常不应影响主循环

## 性能优化建议

### 连接复用
- HTTP 客户端使用连接池（aiohttp 默认行为）
- 避免频繁创建和销毁会话对象
- 合理设置连接超时和读取超时

### 内存管理
- 及时释放不再需要的引用
- 大数据处理使用流式而非一次性加载
- 注意闭包中的变量捕获导致的内存泄漏
