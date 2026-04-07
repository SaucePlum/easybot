#!/usr/bin/env python3
"""
EasyBot SDK 示例 05：注册开始/结束/定时事件

展示如何使用生命周期事件：
- on_startup: 机器人启动时触发
- on_shutdown: 机器人关闭时触发
- on_timer: 定时周期性触发

运行前请将 app_id 和 app_secret 替换为你的机器人凭证
"""

from easybot import Bot, Model


def main() -> None:
    bot: Bot = Bot(
        app_id="your_app_id",
        app_secret="your_app_secret",
    )

    # ==================== 5.1 启动事件 ====================
    @bot.on_startup
    async def on_startup(event: Model.StartupEvent) -> None:
        """
        机器人启动时触发

        适用场景：
        - 加载配置文件
        - 连接数据库
        - 初始化缓存
        - 发送启动通知
        """
        bot.logger.info("=" * 50)
        bot.logger.info(f"机器人启动成功！")
        bot.logger.info(f"启动时间：{event.timestamp}")
        bot.logger.info(f"机器人ID：{bot.bot_id}")
        bot.logger.info("=" * 50)

        # 示例：加载配置
        # config = load_config()
        # bot.logger.info("配置加载完成")

        # 示例：连接数据库
        # await db.connect()
        # bot.logger.info("数据库连接成功")

    # ==================== 5.2 关闭事件 ====================
    @bot.on_shutdown
    async def on_shutdown(event: Model.ShutdownEvent) -> None:
        """
        机器人关闭时触发

        适用场景：
        - 保存数据到文件
        - 关闭数据库连接
        - 清理资源
        - 发送关闭通知
        """
        bot.logger.info("=" * 50)
        bot.logger.info(f"机器人正在关闭...")
        bot.logger.info(f"关闭时间：{event.timestamp}")
        bot.logger.info("=" * 50)

        # 示例：保存数据
        # save_data()
        # bot.logger.info("数据已保存")

        # 示例：关闭数据库连接
        # await db.close()
        # bot.logger.info("数据库连接已关闭")

    # ==================== 5.3 定时事件 ====================
    @bot.on_timer(interval=60)  # 每60秒执行一次
    async def on_timer(event: Model.TimerEvent) -> None:
        """
        定时任务

        适用场景：
        - 定时推送消息
        - 清理过期数据
        - 同步数据
        - 健康检查

        参数：
        - interval: 定时间隔（秒）
        - event.tick_count: 第几次触发（从1开始）
        """
        bot.logger.info(f"定时任务执行，第 {event.tick_count} 次")

        # 示例：每小时执行一次清理
        if event.tick_count % 60 == 0:
            bot.logger.info("执行每小时清理任务")
            # cleanup_expired_data()

    # ==================== 多个不同间隔的定时任务 ====================
    @bot.on_timer(interval=300)  # 每5分钟
    async def on_timer_5min(event: Model.TimerEvent) -> None:
        """5分钟定时任务"""
        bot.logger.info("5分钟定时任务执行")

    @bot.on_timer(interval=3600)  # 每小时
    async def on_timer_hourly(event: Model.TimerEvent) -> None:
        """每小时定时任务"""
        bot.logger.info("每小时定时任务执行")

    bot.start()


if __name__ == "__main__":
    main()
