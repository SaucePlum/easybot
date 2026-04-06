---
alwaysApply: true
description: 日志系统使用规范，包括 Logger 类的使用、日志级别选择、格式要求和最佳实践
---

# 日志规范

## 日志系统架构

### 组件结构
```
Logger (用户接口)
  └── LoggerManager (单例管理器，共享 handler)
        ├── TimedRotatingFileHandler (按天轮转的文件日志)
        │     └── 路径: logs/{bot_id}/YYYY-MM-DD.log
        └── StreamHandler (控制台输出，支持彩色)
              └── ColoredFormatter (ANSI 颜色格式化)
```

### 核心特性
- **按机器人分目录**：每个 bot_id 有独立的日志文件夹
- **按天自动轮转**：每天生成新日志文件，保留历史记录
- **控制台彩色输出**：根据日志级别自动着色
- **共享 handler**：避免重复创建文件和控制台处理器

## Logger 初始化

### 基本用法
```python
from easybot.logger import Logger

class Bot:
    def __init__(self, ..., is_debug: bool = False):
        self.logger = Logger(
            bot_id=app_id,
            is_debug=is_debug,
            module_name="bot"  # 模块标识
        )
```

### 参数说明
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `bot_id` | str | 必填 | 机器人 AppID，用于区分不同机器人的日志 |
| `log_dir` | str \| None | None | 日志根目录，默认为当前目录下的 `logs` 文件夹 |
| `level` | int \| None | None | 显式指定日志级别（若指定则忽略 is_debug） |
| `is_debug` | bool | False | 是否调试模式（True=DEBUG 级别，False=INFO 级别） |
| `console_output` | bool | True | 是否输出到控制台 |
| `use_color` | bool | True | 控制台是否使用彩色输出 |
| `module_name` | str | "core" | 模块名称标识，用于区分不同模块的日志 |

### 创建子模块 Logger
```python
# 在 API 类中复用 bot 的 logger 配置
class API:
    def __init__(self, bot: "Bot"):
        self._logger = bot.logger.with_module("api")
```

## 日志级别使用指南

### 级别定义
```python
from easybot.logger import DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### 使用场景

#### DEBUG - 调试信息
- **用途**：详细的诊断信息，仅在调试时启用
- **场景**：
  - 变量值跟踪
  - 函数调用进入/退出
  - 内部状态变化
  - Intent 计算过程
  ```python
  self.logger.debug(f"Bot 初始化完成: is_private={is_private}, protocol={type(self.protocol).__name__}")
  ```

#### INFO - 一般信息
- **用途**：正常运行的关键节点信息
- **场景**：
  - 启动和停止事件
  - 事件订阅成功
  - 重要状态变更
  - 操作完成确认
  ```python
  self.logger.info(f"本次程序进程ID：{os.getpid()} | SDK版本：{__version__} | 即将开始运行机器人……")
  self.logger.info(f"{display_name}事件订阅成功")
  ```

#### WARNING - 警告信息
- **用途**：潜在问题或非预期情况
- **场景**：
  - 使用了不推荐的功能
  - 公域机器人尝试注册私域事件
  - 可恢复的错误
  - 配置不合理但可运行
  ```python
  if not self.is_private:
      self.logger.warning(
          f"on_guild_full_message 仅私域机器人可用，当前为公域机器人"
      )
  ```

#### ERROR - 错误信息
- **用途**：操作失败但程序可继续运行
- **场景**：
  - API 调用失败
  - 网络请求超时
  - 数据解析错误
  - 资源释放失败
  ```python
  except Exception as e:
      self.logger.error(f"关闭生命周期管理器时出错: {e}")
  ```

#### CRITICAL - 严重错误
- **用途**：程序可能无法继续运行的致命错误
- **场景**：
  - 认证完全失败
  - 关键资源不可用
  - 数据损坏检测到
  ```python
  # 极少使用，仅用于无法恢复的情况
  self.logger.critical("认证密钥无效，无法启动")
  ```

## 日志格式规范

### 统一格式模板
```
[时间戳] [级别] [模块名] 消息内容
```

### 示例输出
```
[2026-01-01 10:30:45] [INFO] [bot] 本次程序进程ID：12345 | SDK版本：1.0.0 | 即将开始运行机器人……
[2026-01-01 10:30:46] [DEBUG] [api] HTTP 客户端已创建
[2026-01-01 10:31:00] [WARNING] [bot] on_guild_full_message 仅私域机器人可用
[2026-01-01 10:31:05] [ERROR] [protocol] WebSocket 连接断开: Connection reset
```

### 彩色输出方案
| 级别 | 颜色 | ANSI 码 |
|------|------|---------|
| DEBUG | 青色 | `\033[1;36m` |
| INFO | 绿色 | `\033[1;32m` |
| WARNING | 黄色 | `\033[1;33m` |
| ERROR | 红色 | `\033[1;31m` |
| CRITICAL | 红色背景 | `\033[1;41m` |

## 最佳实践

### DO（应该做的）
✅ **包含上下文信息**
```python
self.logger.info(f"正在启动机器人 (AppID: {self.app_id})")
# 而不是：self.logger.info("正在启动机器人")
```

✅ **在关键操作前后记录日志**
```python
self.logger.debug("HTTP 客户端已创建")
# ... 使用客户端 ...
self.logger.debug("HTTP 客户端已关闭")
```

✅ **异常日志使用 exception() 方法**
```python
except Exception as e:
    self.logger.exception(f"未捕获异常: {e}")  # 自动包含堆栈信息
```

✅ **使用 f-string 格式化消息**
```python
self.logger.info(f"频道 {guild_id} 的名称是 {name}")
```

### DON'T（不应该做的）
❌ **不要在生产环境输出过多 DEBUG 日志**
```python
# 避免在循环中频繁输出 debug
for item in items:
    self.logger.debug(f"处理项目: {item}")  # 可能导致性能问题
```

❌ **不要记录敏感信息**
```python
# 禁止记录 token、密码等
self.logger.info(f"使用密钥: {app_secret}")  # ❌ 危险！
self.logger.info(f"正在初始化机器人: {app_id}")  # ✅ 只记录 ID
```

❌ **不要在异常处理中丢失原始异常**
```python
except Exception:
    self.logger.error("出错了")  # ❌ 丢失了异常信息
    self.logger.exception(f"API 调用失败: {e}")  # ✅ 包含完整堆栈
```

❌ **不要使用 print() 输出日志**
```python
print("调试信息")  # ❌ 不遵循日志规范
self.logger.debug("调试信息")  # ✅ 正确做法
```

## 性能考虑

### 延迟初始化
- Logger 在首次使用时才创建 handler
- 避免在模块导入时就初始化日志系统

### 共享机制
- 同一 bot_id + log_dir 组合共享 LoggerManager 实例
- 全局共享控制台 handler，避免重复输出
- 文件 handler 按日志文件路径缓存

### 异步安全
- Logger 的所有方法都是同步的，可在异步代码中直接调用
- 底层 logging 模块本身是线程安全的
