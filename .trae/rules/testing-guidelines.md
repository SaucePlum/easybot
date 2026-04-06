---
alwaysApply: true
description: 测试编写规范，包括 pytest 使用、TDD 流程、fixtures 使用和覆盖率要求
---

# 测试规范

## 测试框架和工具

### 核心依赖（dev）
```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "isort>=5.12.0",
    "flake8>=6.0.0",
    "mypy>=1.0.0",
]
```

### 必须使用的工具
- **pytest** - 测试框架
- **pytest-asyncio** - 异步测试支持
- **pytest-cov** - 覆盖率报告

## TDD（测试驱动开发）流程

### 红-绿-重构循环
1. **红**：编写一个失败的测试，描述期望的行为
2. **绿**：编写最少代码使测试通过
3. **重构**：优化代码结构，保持测试通过

### 实施要求
- 在编写实现代码**之前**必须先编写测试
- 每个功能点至少有一个对应的测试用例
- 测试失败时优先修复测试或实现，不要跳过

## 测试文件组织

### 目录结构
```
tests/
├── __init__.py
├── conftest.py           # 全局 fixtures
├── fixtures/             # 测试数据文件
│   ├── sample_messages.json
│   └── sample_guilds.json
├── test_bot.py           # Bot 类测试
├── test_api.py           # API 类测试
├── test_models.py        # 数据模型测试
├── test_utils.py         # 工具函数测试
└── test_plugins.py       # 插件系统测试
```

### 命名约定
- 测试文件：`test_*.py` 或 `*_test.py`
- 测试类：`Test*`
- 测试方法：`test_*`

### 示例测试文件结构
```python
# tests/test_models.py
import pytest
from easybot.models import Model

class TestGuildModel:
    """Guild 模型测试"""

    def test_from_dict_with_valid_data(self):
        """从有效字典数据创建 Guild 实例"""
        data = {
            "id": "123456",
            "name": "Test Guild"
        }
        guild = Model.Guild.from_dict(data)
        assert guild.id == "123456"
        assert guild.name == "Test Guild"

    def test_from_dict_with_none(self):
        """传入 None 时返回 None"""
        result = Model.Guild.from_dict(None)
        assert result is None
```

## Fixtures 使用

### conftest.py 中的全局 fixtures
```python
# tests/conftest.py
import pytest
from easybot import Bot, Model

@pytest.fixture
def sample_bot():
    """提供测试用的 Bot 实例"""
    bot = Bot(
        app_id="test_app_id",
        app_secret="test_secret",
        is_sandbox=True
    )
    return bot

@pytest.fixture
def sample_message_data():
    """提供标准的消息测试数据"""
    return {
        "guild_id": "guild_001",
        "channel_id": "channel_001",
        "content": "Hello World"
    }
```

### Fixture 范围选择
| 范围 | 使用场景 | 示例 |
|------|----------|------|
| `function`（默认） | 大多数 fixture | 单个测试数据 |
| `class` | 类中共享的设置 | Mock 对象配置 |
| `module` | 模块级共享资源 | 数据库连接 |
| `session` | 跨模块共享 | 全局配置 |

### 自定义 Fixtures 最佳实践
```python
@pytest.fixture
async def async_client():
    """异步 HTTP 客户端 fixture"""
    client = AsyncHTTPClient()
    yield client
    await client.close()  # 清理资源
```

## 测试分类

### 单元测试
- **目标**：测试单个函数/类的行为
- **隔离性**：不依赖外部服务（使用 mock）
- **速度**：快速执行（毫秒级）

```python
def test_validate_id_with_valid_input():
    from easybot._internal.utils import validate_id
    # 不应抛出异常
    validate_id("123456")

def test_validate_id_with_empty_string():
    from easybot._internal.utils import validate_id
    with pytest.raises(ValueError, match="不能为空"):
        validate_id("")
```

### 集成测试
- **目标**：测试多个组件协作
- **依赖**：可使用真实依赖或高级 mock
- **场景**：API 调用流程、事件处理链路

### 端到端测试（可选）
- **目标**：测试完整用户场景
- **环境**：需要真实或模拟的 QQ 平台
- **频率**：较少运行，主要在发布前

## 异步测试

### 使用 pytest-asyncio
```python
import pytest

@pytest.mark.asyncio
async def test_async_api_call():
    """测试异步 API 调用"""
    api = API(mock_bot)
    result = await api.get_guild("12345")
    assert result.id == "12345"

@pytest.mark.asyncio
async def test_websocket_connection():
    """测试 WebSocket 连接建立"""
    protocol = Proto.websocket()
    # 连接测试逻辑...
```

### 异步 Fixture
```python
@pytest.fixture
@pytest.mark.asyncio
async def connected_bot():
    """已连接的 Bot 实例"""
    bot = Bot(app_id="test", app_secret="test")
    yield bot
    await bot.stop_async()
```

## Mock 和 Patching

### 使用 unittest.mock
```python
from unittest.mock import AsyncMock, MagicMock, patch

def test_api_call_with_mock():
    with patch('easybot.api.HTTPClient') as mock_http:
        mock_http.return_value.get = AsyncMock(return_value={"id": "123"})
        api = API(bot)
        result = asyncio.run(api.get_guild("123"))
        assert result.id == "123"
```

### Mock 原则
- Mock 外部依赖（网络、数据库、文件系统）
- 不要过度 mock（导致测试与实现脱节）
- 验证交互而不仅仅是返回值

## 断言最佳实践

### 使用清晰的断言消息
```python
assert response.status_code == 200, f"Expected 200, got {response.status_code}"
assert len(items) > 0, "Items list should not be empty"
```

### 测试边界条件
```python
def test_timestamp_conversion():
    # 正常情况
    assert timestamp_to_datetime(1704067200).year == 2026
    
    # 边界值：毫秒时间戳
    assert timestamp_to_datetime(1704067200000).year == 2026
    
    # 边界值：空字符串应抛出异常
    with pytest.raises(ValueError):
        timestamp_to_datetime("")
```

### 测试异常场景
```python
def test_api_error_handling():
    with pytest.raises(APIError) as exc_info:
        raise APIError(code=10001, message="Invalid params")
    
    assert exc_info.value.code == 10001
    assert "Invalid params" in str(exc_info.value.message)
```

## 覆盖率要求

### 配置 pytest-cov
```bash
# 运行测试并生成覆盖率报告
pytest --cov=easybot --cov-report=term-missing --cov-fail-under=80
```

### 目标指标
- **整体覆盖率**：≥ 80%
- **核心模块**（Bot, API, Models）：≥ 90%
- **工具函数**（utils）：≥ 95%

### 排除项
- `__init__.py` 文件（仅导出）
- `version.py`（仅版本号常量）
- 类型存根文件（`.pyi`）

## 运行测试

### 常用命令
```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_models.py

# 运行匹配名称的测试
pytest -k "test_from_dict"

# 显示详细输出
pytest -v

# 运行并显示覆盖率
pytest --cov=easybot --cov-report=html

# 只运行上次失败的测试
pytest --lf
```

### CI/CD 集成
测试必须在以下情况自动运行：
- 提交 Pull Request 前
- 合并到主分支时
- 发布新版本前
