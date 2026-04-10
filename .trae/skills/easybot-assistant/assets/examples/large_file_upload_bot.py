"""
大文件分片上传机器人
====================
展示如何使用 EasyBot SDK 上传大文件（视频、文档等）。

运行方式：
1. 设置环境变量 EASYBOT_APP_ID 和 EASYBOT_APP_SECRET
2. 准备要上传的文件
3. python large_file_upload_bot.py
"""

import os

from easybot import Bot, CommandValidScenes, Model

bot = Bot(
    app_id=os.getenv("EASYBOT_APP_ID", "your_app_id"),
    app_secret=os.getenv("EASYBOT_APP_SECRET", "your_app_secret"),
    is_debug=True,
)


# 方式一：一键上传（推荐）
@bot.on_command(
    command="上传视频",
    valid_scenes=CommandValidScenes.GROUP | CommandValidScenes.C2C,
)
async def upload_video(msg: Model.GroupMessage | Model.C2CMessage) -> None:
    """一键上传视频文件"""
    import hashlib

    # 从消息中获取文件路径（实际应用中可以从参数获取）
    file_path = "./test_video.mp4"

    try:
        await msg.reply(f"⏳ 正在上传视频: {file_path}")

        # 根据场景获取 openid
        if isinstance(msg, Model.GroupMessage):
            openid_param = {"group_openid": msg.group_openid}
        else:
            openid_param = {"user_openid": msg.author.user_openid}

        # 一行代码完成所有操作
        result = await bot.api.upload_large_file(
            file_path=file_path,
            file_type=2,  # 1=图片, 2=视频, 3=语音, 4=文件
            **openid_param,
        )

        # 上传成功，发送消息
        await msg.reply(
            f"✅ 视频上传成功！\n"
            f"文件ID: {result.file_uuid}\n"
            f"有效期: {result.ttl}秒",
            media_file_info=result.file_info,
        )

    except FileNotFoundError:
        await msg.reply(f"❌ 文件不存在: {file_path}")
    except Exception as e:
        bot.logger.error(f"上传失败: {e}")
        await msg.reply(f"❌ 上传失败: {e}")


# 方式二：手动控制流程（显示进度）
@bot.on_command(
    command="上传文件带进度",
    valid_scenes=CommandValidScenes.GROUP | CommandValidScenes.C2C,
)
async def upload_with_progress(msg: Model.GroupMessage | Model.C2CMessage) -> None:
    """手动控制上传流程，显示进度"""
    import hashlib
    from pathlib import Path

    file_path = "./large_document.pdf"

    try:
        # 步骤1：读取文件并计算哈希
        await msg.reply(f"📊 正在计算文件哈希: {file_path}")
        with open(file_path, "rb") as f:
            file_data = f.read()
            file_md5 = hashlib.md5(file_data).hexdigest()
            file_sha1 = hashlib.sha1(file_data).hexdigest()
            md5_10m = (
                hashlib.md5(file_data[:10002432]).hexdigest()
                if len(file_data) >= 10002432
                else file_md5
            )

        # 步骤2：申请上传
        await msg.reply("📤 正在申请上传...")

        if isinstance(msg, Model.GroupMessage):
            openid_param = {"group_openid": msg.group_openid}
        else:
            openid_param = {"user_openid": msg.author.user_openid}

        # 根据文件扩展名判断文件类型
        file_ext = Path(file_path).suffix.lower()
        file_type_map = {
            ".png": 1,
            ".jpg": 1,
            ".jpeg": 1,
            ".gif": 1,
            ".mp4": 2,
            ".avi": 2,
            ".mov": 2,
            ".mp3": 3,
            ".wav": 3,
            ".amr": 3,
        }
        file_type = file_type_map.get(file_ext, 4)

        prepare = await bot.api.upload_prepare(
            file_type=file_type,
            file_name=Path(file_path).name,
            file_size=len(file_data),
            md5=file_md5,
            sha1=file_sha1,
            md5_10m=md5_10m,
            **openid_param,
        )

        total_parts = len(prepare.parts)
        await msg.reply(
            f"📋 上传任务已创建\n"
            f"分片数量: {total_parts}\n"
            f"分片大小: {prepare.block_size / 1024 / 1024:.2f}MB"
        )

        # 步骤3：逐个上传分片并显示进度
        for i, part in enumerate(prepare.parts, 1):
            # 读取分片数据
            offset = (part.index - 1) * prepare.block_size
            chunk_data = file_data[offset : offset + prepare.block_size]

            # 上传分片
            await bot.api.upload_part(
                presigned_url=part.presigned_url,
                part_data=chunk_data,
                upload_id=prepare.upload_id,
                part_index=part.index,
                **openid_param,
            )

            # 显示进度
            progress = int((i / total_parts) * 100)
            if i % 5 == 0 or i == total_parts:
                await msg.reply(f"⏳ 上传进度: {progress}% ({i}/{total_parts})")

        # 步骤4：完成上传
        await msg.reply("🔄 正在合并文件...")
        result = await bot.api.upload_complete(
            upload_id=prepare.upload_id,
            **openid_param,
        )

        await msg.reply(
            f"✅ 上传完成！\n" f"文件ID: {result.file_uuid}",
            media_file_info=result.file_info,
        )

    except FileNotFoundError:
        await msg.reply(f"❌ 文件不存在: {file_path}")
    except Exception as e:
        bot.logger.error(f"上传失败: {e}")
        await msg.reply(f"❌ 上传失败: {e}")


# 帮助命令
@bot.on_command(
    command="帮助",
    valid_scenes=CommandValidScenes.GROUP | CommandValidScenes.C2C,
)
async def help_command(msg: Model.GroupMessage | Model.C2CMessage) -> None:
    """显示帮助信息"""
    await msg.reply(
        "📁 大文件上传机器人\n\n"
        "可用命令：\n"
        "- 上传视频 - 一键上传视频文件\n"
        "- 上传文件带进度 - 手动控制上传并显示进度\n"
        "- 帮助 - 显示此帮助信息\n\n"
        "文件大小限制：\n"
        "- 图片：10MB\n"
        "- 视频：100MB\n"
        "- 语音：10MB\n"
        "- 文件：100MB"
    )


if __name__ == "__main__":
    bot.start()
