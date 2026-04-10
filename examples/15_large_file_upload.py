#!/usr/bin/env python3
"""
EasyBot SDK 示例 15：大文件分片上传

展示 EasyBot 提供的大文件分片上传功能：
- 方式一：一键上传（推荐，最简单）
- 方式二：手动控制流程（适合显示进度）
- 方式三：底层控制（适合自定义上传逻辑）

适用场景：
- 单聊：user_openid
- 群聊：group_openid

运行前请将 app_id 和 app_secret 替换为你的机器人凭证
"""

import asyncio
import hashlib
from pathlib import Path
from re import compile as re_compile

from easybot import Bot, CommandValidScenes, Model


def main() -> None:
    bot: Bot = Bot(
        app_id="102024017",
        app_secret="jCf8b5Z3X1VzUzUzUzU0W2Y4a6c9gDkH",
        is_debug=True,
        is_sandbox=False,
        is_private=True,
    )

    # ==================== 15.1 一键上传（推荐） ====================
    @bot.on_command(
        regex=re_compile(r"上传视频\s+(.+)"),
        valid_scenes=CommandValidScenes.GROUP | CommandValidScenes.C2C,
    )
    async def cmd_upload_video(
        msg: Model.GroupMessage | Model.C2CMessage,
    ) -> None:
        """一键上传大文件（最简单的方式）

        用法：上传视频 <文件路径>
        示例：上传视频 ./videos/large_video.mp4
        """
        file_path = msg.treated_msg[0].strip()

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

    @bot.on_command(
        regex=re_compile(r"上传文件\s+(.+)"),
        valid_scenes=CommandValidScenes.GROUP | CommandValidScenes.C2C,
    )
    async def cmd_upload_file(
        msg: Model.GroupMessage | Model.C2CMessage,
    ) -> None:
        """上传文件示例

        用法：上传文件 <文件路径>
        示例：上传文件 ./documents/report.pdf
        """
        file_path = msg.treated_msg[0].strip()

        try:
            await msg.reply(f"⏳ 正在上传文件: {file_path}")

            if isinstance(msg, Model.GroupMessage):
                openid_param = {"group_openid": msg.group_openid}
            else:
                openid_param = {"user_openid": msg.author.user_openid}

            result = await bot.api.upload_large_file(
                file_path=file_path,
                file_type=4,  # 文件类型
                **openid_param,
            )

            await msg.reply(
                f"✅ 文件上传成功！",
                media_file_info=result.file_info,
            )

        except FileNotFoundError:
            await msg.reply(f"❌ 文件不存在: {file_path}")
        except Exception as e:
            bot.logger.error(f"上传失败: {e}")
            await msg.reply(f"❌ 上传失败: {e}")

    @bot.on_command(
        regex=re_compile(r"上传图片\s+(.+)"),
        valid_scenes=CommandValidScenes.C2C,
    )
    async def cmd_upload_image_c2c(msg: Model.C2CMessage) -> None:
        """单聊场景的大文件上传

        用法：上传图片 <文件路径>
        示例：上传图片 ./images/large_photo.png
        """
        file_path = msg.treated_msg[0].strip()

        try:
            await msg.reply(f"⏳ 正在上传图片: {file_path}")

            result = await bot.api.upload_large_file(
                file_path=file_path,
                file_type=1,  # 图片类型
                user_openid=msg.author.user_openid,
            )

            await msg.reply(
                "✅ 图片上传成功！",
                media_file_info=result.file_info,
            )

        except FileNotFoundError:
            await msg.reply(f"❌ 文件不存在: {file_path}")
        except Exception as e:
            bot.logger.error(f"上传失败: {e}")
            await msg.reply(f"❌ 上传失败: {e}")

    # ==================== 15.2 手动控制流程（显示进度） ====================
    @bot.on_command(
        regex=re_compile(r"上传并显示进度\s+(.+)"),
        valid_scenes=CommandValidScenes.GROUP | CommandValidScenes.C2C,
    )
    async def cmd_upload_with_progress(
        msg: Model.GroupMessage | Model.C2CMessage,
    ) -> None:
        """手动控制上传流程，显示进度

        用法：上传并显示进度 <文件路径>
        示例：上传并显示进度 ./videos/large_video.mp4
        """
        file_path = msg.treated_msg[0].strip()

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
            file_type = file_type_map.get(file_ext, 4)  # 默认为文件类型

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
                if i % 5 == 0 or i == total_parts:  # 每5个分片或最后一个更新一次
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

    # ==================== 15.3 并发上传（高级） ====================
    @bot.on_command(
        regex=re_compile(r"并发上传\s+(.+)"),
        valid_scenes=CommandValidScenes.GROUP | CommandValidScenes.C2C,
    )
    async def cmd_concurrent_upload(
        msg: Model.GroupMessage | Model.C2CMessage,
    ) -> None:
        """并发上传多个分片（提高上传速度）

        用法：并发上传 <文件路径>
        示例：并发上传 ./videos/large_video.mp4
        """
        file_path = msg.treated_msg[0].strip()

        try:
            await msg.reply(f"🚀 开始并发上传: {file_path}")

            # 读取文件
            with open(file_path, "rb") as f:
                file_data = f.read()

            # 计算哈希
            file_md5 = hashlib.md5(file_data).hexdigest()
            file_sha1 = hashlib.sha1(file_data).hexdigest()
            md5_10m = (
                hashlib.md5(file_data[:10002432]).hexdigest()
                if len(file_data) >= 10002432
                else file_md5
            )

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

            # 申请上传
            prepare = await bot.api.upload_prepare(
                file_type=file_type,
                file_name=Path(file_path).name,
                file_size=len(file_data),
                md5=file_md5,
                sha1=file_sha1,
                md5_10m=md5_10m,
                **openid_param,
            )

            # 使用信号量控制并发数
            semaphore = asyncio.Semaphore(3)  # 最多3个并发

            async def upload_single_part(part: Model.UploadPart) -> bool:
                """上传单个分片"""
                async with semaphore:
                    offset = (part.index - 1) * prepare.block_size
                    chunk_data = file_data[offset : offset + prepare.block_size]

                    return await bot.api.upload_part(
                        presigned_url=part.presigned_url,
                        part_data=chunk_data,
                        upload_id=prepare.upload_id,
                        part_index=part.index,
                        **openid_param,
                    )

            # 并发上传所有分片
            tasks = [upload_single_part(part) for part in prepare.parts]
            await asyncio.gather(*tasks)

            # 完成上传
            result = await bot.api.upload_complete(
                upload_id=prepare.upload_id,
                **openid_param,
            )

            await msg.reply(
                f"✅ 并发上传完成！\n" f"并发数: 3\n" f"分片数: {len(prepare.parts)}",
                media_file_info=result.file_info,
            )

        except FileNotFoundError:
            await msg.reply(f"❌ 文件不存在: {file_path}")
        except Exception as e:
            bot.logger.error(f"上传失败: {e}")
            await msg.reply(f"❌ 上传失败: {e}")

    # ==================== 15.4 断点续传（高级） ====================
    @bot.on_command(
        regex=re_compile(r"断点续传\s+(.+)"),
        valid_scenes=CommandValidScenes.GROUP | CommandValidScenes.C2C,
    )
    async def cmd_resume_upload(
        msg: Model.GroupMessage | Model.C2CMessage,
    ) -> None:
        """断点续传示例（需要自己保存上传状态）

        用法：断点续传 <文件路径>
        示例：断点续传 ./videos/large_video.mp4
        """
        file_path = msg.treated_msg[0].strip()

        try:
            # 在实际应用中，这些状态应该保存到数据库或文件中
            # 这里仅作演示
            saved_upload_id = None  # 从数据库读取
            saved_parts = []  # 已上传的分片索引列表

            # 读取文件
            with open(file_path, "rb") as f:
                file_data = f.read()

            # 计算哈希
            file_md5 = hashlib.md5(file_data).hexdigest()
            file_sha1 = hashlib.sha1(file_data).hexdigest()
            md5_10m = (
                hashlib.md5(file_data[:10002432]).hexdigest()
                if len(file_data) >= 10002432
                else file_md5
            )

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

            # 如果没有保存的上传ID，则申请新的
            if not saved_upload_id:
                prepare = await bot.api.upload_prepare(
                    file_type=file_type,
                    file_name=Path(file_path).name,
                    file_size=len(file_data),
                    md5=file_md5,
                    sha1=file_sha1,
                    md5_10m=md5_10m,
                    **openid_param,
                )
                saved_upload_id = prepare.upload_id
                # TODO: 保存 upload_id 到数据库
                await msg.reply(f"📋 创建新上传任务: {saved_upload_id}")
            else:
                # 从保存的状态恢复
                await msg.reply(f"🔄 恢复上传任务: {saved_upload_id}")
                # 需要重新获取 prepare 信息（这里简化处理）
                prepare = await bot.api.upload_prepare(
                    file_type=file_type,
                    file_name=Path(file_path).name,
                    file_size=len(file_data),
                    md5=file_md5,
                    sha1=file_sha1,
                    md5_10m=md5_10m,
                    **openid_param,
                )

            # 只上传未完成的分片
            for part in prepare.parts:
                if part.index not in saved_parts:
                    offset = (part.index - 1) * prepare.block_size
                    chunk_data = file_data[offset : offset + prepare.block_size]

                    await bot.api.upload_part(
                        presigned_url=part.presigned_url,
                        part_data=chunk_data,
                        upload_id=saved_upload_id,
                        part_index=part.index,
                        **openid_param,
                    )

                    # TODO: 保存已上传的分片索引到数据库
                    saved_parts.append(part.index)

                    # 显示进度
                    progress = int((len(saved_parts) / len(prepare.parts)) * 100)
                    await msg.reply(f"⏳ 上传进度: {progress}%")

            # 完成上传
            result = await bot.api.upload_complete(
                upload_id=saved_upload_id,
                **openid_param,
            )

            await msg.reply(
                "✅ 断点续传完成！",
                media_file_info=result.file_info,
            )

        except FileNotFoundError:
            await msg.reply(f"❌ 文件不存在: {file_path}")
        except Exception as e:
            bot.logger.error(f"上传失败: {e}")
            await msg.reply(f"❌ 上传失败: {e}")

    # ==================== 15.5 文件类型说明 ====================
    @bot.on_command(
        command="文件类型",
        valid_scenes=CommandValidScenes.GROUP | CommandValidScenes.C2C,
    )
    async def cmd_file_type_help(
        msg: Model.GroupMessage | Model.C2CMessage,
    ) -> None:
        """文件类型说明"""
        await msg.reply(
            "📁 文件类型说明：\n"
            "1 = 图片（PNG、JPG、GIF等）\n"
            "2 = 视频（MP4、AVI、MOV等）\n"
            "3 = 语音（MP3、WAV、AMR等）\n"
            "4 = 文件（PDF、DOC、ZIP等）\n\n"
            "使用示例：\n"
            "- 上传视频 ./videos/test.mp4\n"
            "- 上传文件 ./documents/report.pdf\n"
            "- 上传图片 ./images/photo.png\n"
            "- 上传并显示进度 ./videos/test.mp4\n"
            "- 并发上传 ./videos/test.mp4\n"
            "- 断点续传 ./videos/test.mp4"
        )

    bot.start()


if __name__ == "__main__":
    main()
