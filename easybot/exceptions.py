#!/usr/bin/env python3
"""
EasyBot SDK 异常模块

定义 SDK 中使用的所有自定义异常类。
"""


class EasyBotException(Exception):
    """EasyBot 基础异常类"""

    pass


class APIError(EasyBotException):
    """
    API 调用错误

    当 API 返回错误响应时抛出此异常。

    Attributes:
        code: 错误码
        message: 错误信息
        trace_id: 请求追踪 ID
    """

    def __init__(self, code: int, message: str, trace_id: str | None = None):
        self.code = code
        self.message = message
        self.trace_id = trace_id
        error_msg = f"[{code}] {message}"
        if trace_id:
            error_msg += f" (TraceID: {trace_id})"
        super().__init__(error_msg)


class AuthenticationError(EasyBotException):
    """
    认证错误

    当认证失败时抛出此异常，例如：
    - access_token 无效或过期
    - app_id 或 app_secret 错误
    """

    pass


class PermissionError(EasyBotException):
    """
    权限错误

    当机器人没有足够权限执行操作时抛出此异常。
    """

    pass


class RateLimitError(EasyBotException):
    """
    频率限制错误

    当请求超过频率限制时抛出此异常。

    Attributes:
        retry_after: 建议等待的秒数
    """

    def __init__(self, retry_after: int | None = None):
        self.retry_after = retry_after
        if retry_after:
            message = f"频率限制，请等待 {retry_after} 秒后重试"
        else:
            message = "频率限制"
        super().__init__(message)


class NetworkError(EasyBotException):
    """
    网络错误

    当发生网络连接问题时抛出此异常，例如：
    - 连接超时
    - DNS 解析失败
    - 连接被拒绝
    """

    pass


class ValidationError(EasyBotException):
    """
    参数验证错误

    当传入的参数不符合要求时抛出此异常。
    """

    pass


class StopProcessing(EasyBotException):
    """
    停止处理异常

    在预处理器中抛出此异常可中断整个处理流程，
    后续的命令匹配和执行将被跳过。
    """

    pass


class WaitError(EasyBotException):
    """
    等待错误

    当 wait_for() 注册的等待任务被意外删除时抛出，
    通常发生在并发场景下多个处理器竞争同一消息时。
    """

    pass


class WaitTimeoutError(EasyBotException):
    """
    等待超时错误

    当 wait_for() 在指定的超时时间内未收到匹配的消息时抛出，
    调用方可以捕获此异常来执行超时后的处理逻辑。
    """

    pass
