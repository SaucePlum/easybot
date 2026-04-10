#!/usr/bin/env python3
"""
EasyBot SDK 示例 14：发送消息 API 全覆盖矩阵

本示例使用单文件命令驱动方式，覆盖四个发送消息 API 的主要发送能力：
- send_guild_message
- send_group_message
- send_c2c_message
- send_direct_message

覆盖范围包括：
- 普通文本平铺参数
- MessagesModel.Message 普通消息构建器
- MessageEmbed
- MessageArk23
- MessageArk24
- MessageArk37
- MessageMarkdown
- 场景支持的图片或富媒体发送
- 引用回复
- 单聊 is_wakeup

准备项：
- 将 app_id 和 app_secret 替换为真实凭证
- 准备本地测试图片：examples/images/test.png
- 群聊 / 单聊富媒体测试会先走 upload_media
- 某些消息类型受平台能力、模板配置或环境限制

可触发命令：

频道：
- guild_text
- guild_message
- guild_image
- guild_message_image
- guild_file_image
- guild_message_file_image
- guild_embed
- guild_ark23
- guild_ark24
- guild_ark37
- guild_markdown
- guild_reference
- guild_reference_ignore
- guild_event_id
- guild_error_mixed

群聊：
- group_text
- group_message
- group_media
- group_message_media
- group_embed
- group_ark23
- group_ark24
- group_ark37
- group_markdown
- group_reference
- group_reference_ignore
- group_event_id
- group_error_mixed
- group_error_no_content

单聊：
- c2c_text
- c2c_message
- c2c_media
- c2c_message_media
- c2c_embed
- c2c_ark23
- c2c_ark24
- c2c_ark37
- c2c_markdown
- c2c_reference
- c2c_reference_ignore
- c2c_event_id
- c2c_wakeup
- c2c_error_mixed
- c2c_error_wakeup_conflict

频道私信：
- direct_text
- direct_message
- direct_image
- direct_message_image
- direct_file_image
- direct_message_file_image
- direct_embed
- direct_ark23
- direct_ark24
- direct_ark37
- direct_markdown
- direct_reference
- direct_reference_ignore
- direct_event_id
- direct_error_mixed
"""

from pathlib import Path

from easybot import Bot, MessagesModel, Model

EXAMPLE_DIR = Path(__file__).resolve().parent
LOCAL_IMAGE_PATH = EXAMPLE_DIR / "images" / "test.png"
IMAGE_URL = "https://picsum.photos/seed/easybot-send-matrix/640/360"
LINK_URL = "https://bot.q.qq.com/wiki/"


def _ensure_local_image() -> None:
    if not LOCAL_IMAGE_PATH.exists():
        raise FileNotFoundError(f"测试图片不存在，请准备文件：{LOCAL_IMAGE_PATH}")


def _describe_result(result: object) -> str:
    for attr in ("id", "message_id", "msg_id"):
        value = getattr(result, attr, None)
        if value:
            return str(value)
    if hasattr(result, "to_dict"):
        data = result.to_dict()
        for key in ("id", "message_id", "msg_id"):
            value = data.get(key)
            if value:
                return str(value)
        return str(data)
    return repr(result)


def _passive_kwargs(msg, prefer_event_id: bool = False) -> dict[str, str | None]:
    if prefer_event_id:
        return {"msg_id": None, "event_id": msg.event_id or None}
    return {
        "msg_id": getattr(msg, "id", "") or None,
        "event_id": None if getattr(msg, "id", "") else (msg.event_id or None),
    }


def _group_like_kwargs(
    msg, prefer_event_id: bool = False
) -> dict[str, int | str | None]:
    kwargs = _passive_kwargs(msg, prefer_event_id=prefer_event_id)
    kwargs["msg_seq"] = 1
    return kwargs


def _message(text: str) -> MessagesModel.Message:
    return MessagesModel.Message(content=text)


def _message_image(text: str) -> MessagesModel.Message:
    return MessagesModel.Message(content=text, image=IMAGE_URL)


def _message_file_image(text: str) -> MessagesModel.Message:
    _ensure_local_image()
    return MessagesModel.Message(content=text, file_image=str(LOCAL_IMAGE_PATH))


def _message_media(text: str, file_info: str) -> MessagesModel.Message:
    return MessagesModel.Message(content=text, media_file_info=file_info)


def _embed(label: str) -> MessagesModel.MessageEmbed:
    return MessagesModel.MessageEmbed(
        title=f"{label} Embed",
        content=["第一行", "第二行"],
        image=IMAGE_URL,
        prompt=f"{label} Embed 提醒",
    )


def _ark23(label: str) -> MessagesModel.MessageArk23:
    return MessagesModel.MessageArk23(
        content=[f"{label} 链接一", f"{label} 链接二"],
        link=[LINK_URL, f"{LINK_URL}develop/"],
        desc=f"{label} Ark23 描述",
        prompt=f"{label} Ark23 提醒",
    )


def _ark24(label: str) -> MessagesModel.MessageArk24:
    return MessagesModel.MessageArk24(
        title=f"{label} Ark24 标题",
        content=f"{label} Ark24 内容",
        subtitle=f"{label} 副标题",
        link=LINK_URL,
        image=IMAGE_URL,
        desc=f"{label} Ark24 描述",
        prompt=f"{label} Ark24 提醒",
    )


def _ark37(label: str) -> MessagesModel.MessageArk37:
    return MessagesModel.MessageArk37(
        title=f"{label} Ark37 标题",
        content=f"{label} Ark37 内容",
        link=LINK_URL,
        image=IMAGE_URL,
        prompt=f"{label} Ark37 提醒",
    )


def _markdown(label: str) -> MessagesModel.MessageMarkdown:
    return MessagesModel.MessageMarkdown(
        content=f"# {label}\n\n这是一条 Markdown 测试消息。"
    )


async def _upload_group_media(bot: Bot, msg: Model.GroupMessage) -> str:
    _ensure_local_image()
    result = await bot.api.upload_media(
        file_type=1,
        file_data=str(LOCAL_IMAGE_PATH),
        group_openid=msg.group_openid,
    )
    return result.file_info


async def _upload_c2c_media(bot: Bot, msg: Model.C2CMessage) -> str:
    _ensure_local_image()
    result = await bot.api.upload_media(
        file_type=1,
        file_data=str(LOCAL_IMAGE_PATH),
        user_openid=msg.author.user_openid,
    )
    return result.file_info


async def _run_case(bot: Bot, msg, label: str, coro) -> None:
    try:
        bot.logger.info(f"开始测试：{label}")
        result = await coro
        bot.logger.info(f"{label} 发送成功：{_describe_result(result)}")
    except Exception as e:
        bot.logger.error(f"{label} 发送失败：{e}")
        await msg.reply(f"❌ {label} 失败：{e}")


async def _run_expected_error(bot: Bot, msg, label: str, coro) -> None:
    try:
        bot.logger.info(f"开始测试预期失败用例：{label}")
        await coro
        bot.logger.error(f"{label} 未按预期失败")
        await msg.reply(f"❌ {label} 未按预期失败")
    except Exception as e:
        bot.logger.info(f"{label} 预期失败通过：{e}")
        await msg.reply(f"✅ {label} 预期失败通过：{e}")


def main() -> None:
    bot = Bot(
        app_id="your_app_id",
        app_secret="your_app_secret",
    )

    @bot.on_guild_message
    async def handle_guild(msg: Model.GuildMessage) -> None:
        command = msg.treated_msg.strip()
        kwargs = _passive_kwargs(msg)

        match command:
            case "guild_text":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_guild_message(
                        msg.channel_id,
                        content="guild_text 测试消息",
                        **kwargs,
                    ),
                )
            case "guild_message":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_guild_message(
                        msg.channel_id,
                        content=_message("guild_message 测试消息"),
                        **kwargs,
                    ),
                )
            case "guild_image":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_guild_message(
                        msg.channel_id,
                        content="guild_image 测试消息",
                        image=IMAGE_URL,
                        **kwargs,
                    ),
                )
            case "guild_message_image":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_guild_message(
                        msg.channel_id,
                        content=_message_image("guild_message_image 测试消息"),
                        **kwargs,
                    ),
                )
            case "guild_file_image":
                _ensure_local_image()
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_guild_message(
                        msg.channel_id,
                        content="guild_file_image 测试消息",
                        file_image=str(LOCAL_IMAGE_PATH),
                        **kwargs,
                    ),
                )
            case "guild_message_file_image":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_guild_message(
                        msg.channel_id,
                        content=_message_file_image(
                            "guild_message_file_image 测试消息"
                        ),
                        **kwargs,
                    ),
                )
            case "guild_embed":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_guild_message(
                        msg.channel_id,
                        content=_embed(command),
                        **kwargs,
                    ),
                )
            case "guild_ark23":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_guild_message(
                        msg.channel_id,
                        content=_ark23(command),
                        **kwargs,
                    ),
                )
            case "guild_ark24":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_guild_message(
                        msg.channel_id,
                        content=_ark24(command),
                        **kwargs,
                    ),
                )
            case "guild_ark37":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_guild_message(
                        msg.channel_id,
                        content=_ark37(command),
                        **kwargs,
                    ),
                )
            case "guild_markdown":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_guild_message(
                        msg.channel_id,
                        content=_markdown(command),
                        **kwargs,
                    ),
                )
            case "guild_reference":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_guild_message(
                        msg.channel_id,
                        content="guild_reference 测试消息",
                        message_reference_id=msg.id,
                        **kwargs,
                    ),
                )
            case "guild_reference_ignore":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_guild_message(
                        msg.channel_id,
                        content="guild_reference_ignore 测试消息",
                        message_reference_id=msg.id,
                        ignore_message_reference_error=True,
                        **kwargs,
                    ),
                )
            case "guild_event_id":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_guild_message(
                        msg.channel_id,
                        content="guild_event_id 测试消息",
                        **_passive_kwargs(msg, prefer_event_id=True),
                    ),
                )
            case "guild_error_mixed":
                await _run_expected_error(
                    bot,
                    msg,
                    command,
                    bot.api.send_guild_message(
                        msg.channel_id,
                        content=_message("guild_error_mixed"),
                        image=IMAGE_URL,
                        **kwargs,
                    ),
                )

    @bot.on_group_message
    async def handle_group(msg: Model.GroupMessage) -> None:
        command = msg.treated_msg.strip()
        kwargs = _group_like_kwargs(msg)

        match command:
            case "group_text":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_group_message(
                        msg.group_openid,
                        content="group_text 测试消息",
                        **kwargs,
                    ),
                )
            case "group_message":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_group_message(
                        msg.group_openid,
                        content=_message("group_message 测试消息"),
                        **kwargs,
                    ),
                )
            case "group_media":
                file_info = await _upload_group_media(bot, msg)
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_group_message(
                        msg.group_openid,
                        content="group_media 测试消息",
                        media_file_info=file_info,
                        **kwargs,
                    ),
                )
            case "group_message_media":
                file_info = await _upload_group_media(bot, msg)
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_group_message(
                        msg.group_openid,
                        content=_message_media(
                            "group_message_media 测试消息", file_info
                        ),
                        **kwargs,
                    ),
                )
            case "group_embed":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_group_message(
                        msg.group_openid,
                        content=_embed(command),
                        **kwargs,
                    ),
                )
            case "group_ark23":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_group_message(
                        msg.group_openid,
                        content=_ark23(command),
                        **kwargs,
                    ),
                )
            case "group_ark24":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_group_message(
                        msg.group_openid,
                        content=_ark24(command),
                        **kwargs,
                    ),
                )
            case "group_ark37":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_group_message(
                        msg.group_openid,
                        content=_ark37(command),
                        **kwargs,
                    ),
                )
            case "group_markdown":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_group_message(
                        msg.group_openid,
                        content=_markdown(command),
                        **kwargs,
                    ),
                )
            case "group_reference":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_group_message(
                        msg.group_openid,
                        content="group_reference 测试消息",
                        message_reference_id=msg.id,
                        **kwargs,
                    ),
                )
            case "group_reference_ignore":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_group_message(
                        msg.group_openid,
                        content="group_reference_ignore 测试消息",
                        message_reference_id=msg.id,
                        ignore_message_reference_error=True,
                        **kwargs,
                    ),
                )
            case "group_event_id":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_group_message(
                        msg.group_openid,
                        content="group_event_id 测试消息",
                        **_group_like_kwargs(msg, prefer_event_id=True),
                    ),
                )
            case "group_error_mixed":
                file_info = await _upload_group_media(bot, msg)
                await _run_expected_error(
                    bot,
                    msg,
                    command,
                    bot.api.send_group_message(
                        msg.group_openid,
                        content=_message("group_error_mixed"),
                        media_file_info=file_info,
                        **kwargs,
                    ),
                )
            case "group_error_no_content":
                file_info = await _upload_group_media(bot, msg)
                await _run_expected_error(
                    bot,
                    msg,
                    command,
                    bot.api.send_group_message(
                        msg.group_openid,
                        media_file_info=file_info,
                        **kwargs,
                    ),
                )

    @bot.on_c2c_message
    async def handle_c2c(msg: Model.C2CMessage) -> None:
        command = msg.treated_msg.strip()
        kwargs = _group_like_kwargs(msg)

        match command:
            case "c2c_text":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_c2c_message(
                        msg.author.user_openid,
                        content="c2c_text 测试消息",
                        **kwargs,
                    ),
                )
            case "c2c_message":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_c2c_message(
                        msg.author.user_openid,
                        content=_message("c2c_message 测试消息"),
                        **kwargs,
                    ),
                )
            case "c2c_media":
                file_info = await _upload_c2c_media(bot, msg)
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_c2c_message(
                        msg.author.user_openid,
                        content="c2c_media 测试消息",
                        media_file_info=file_info,
                        **kwargs,
                    ),
                )
            case "c2c_message_media":
                file_info = await _upload_c2c_media(bot, msg)
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_c2c_message(
                        msg.author.user_openid,
                        content=_message_media("c2c_message_media 测试消息", file_info),
                        **kwargs,
                    ),
                )
            case "c2c_embed":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_c2c_message(
                        msg.author.user_openid,
                        content=_embed(command),
                        **kwargs,
                    ),
                )
            case "c2c_ark23":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_c2c_message(
                        msg.author.user_openid,
                        content=_ark23(command),
                        **kwargs,
                    ),
                )
            case "c2c_ark24":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_c2c_message(
                        msg.author.user_openid,
                        content=_ark24(command),
                        **kwargs,
                    ),
                )
            case "c2c_ark37":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_c2c_message(
                        msg.author.user_openid,
                        content=_ark37(command),
                        **kwargs,
                    ),
                )
            case "c2c_markdown":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_c2c_message(
                        msg.author.user_openid,
                        content=_markdown(command),
                        **kwargs,
                    ),
                )
            case "c2c_reference":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_c2c_message(
                        msg.author.user_openid,
                        content="c2c_reference 测试消息",
                        message_reference_id=msg.id,
                        **kwargs,
                    ),
                )
            case "c2c_reference_ignore":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_c2c_message(
                        msg.author.user_openid,
                        content="c2c_reference_ignore 测试消息",
                        message_reference_id=msg.id,
                        ignore_message_reference_error=True,
                        **kwargs,
                    ),
                )
            case "c2c_event_id":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_c2c_message(
                        msg.author.user_openid,
                        content="c2c_event_id 测试消息",
                        **_group_like_kwargs(msg, prefer_event_id=True),
                    ),
                )
            case "c2c_wakeup":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_c2c_message(
                        msg.author.user_openid,
                        content="c2c_wakeup 测试消息",
                        is_wakeup=True,
                    ),
                )
            case "c2c_error_mixed":
                file_info = await _upload_c2c_media(bot, msg)
                await _run_expected_error(
                    bot,
                    msg,
                    command,
                    bot.api.send_c2c_message(
                        msg.author.user_openid,
                        content=_message("c2c_error_mixed"),
                        media_file_info=file_info,
                        **kwargs,
                    ),
                )
            case "c2c_error_wakeup_conflict":
                await _run_expected_error(
                    bot,
                    msg,
                    command,
                    bot.api.send_c2c_message(
                        msg.author.user_openid,
                        content="c2c_error_wakeup_conflict 测试消息",
                        is_wakeup=True,
                        msg_id=msg.id,
                    ),
                )

    @bot.on_direct_message
    async def handle_direct(msg: Model.DirectMessage) -> None:
        command = msg.treated_msg.strip()
        kwargs = _passive_kwargs(msg)

        match command:
            case "direct_text":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_direct_message(
                        msg.guild_id,
                        content="direct_text 测试消息",
                        **kwargs,
                    ),
                )
            case "direct_message":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_direct_message(
                        msg.guild_id,
                        content=_message("direct_message 测试消息"),
                        **kwargs,
                    ),
                )
            case "direct_image":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_direct_message(
                        msg.guild_id,
                        content="direct_image 测试消息",
                        image=IMAGE_URL,
                        **kwargs,
                    ),
                )
            case "direct_message_image":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_direct_message(
                        msg.guild_id,
                        content=_message_image("direct_message_image 测试消息"),
                        **kwargs,
                    ),
                )
            case "direct_file_image":
                _ensure_local_image()
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_direct_message(
                        msg.guild_id,
                        content="direct_file_image 测试消息",
                        file_image=str(LOCAL_IMAGE_PATH),
                        **kwargs,
                    ),
                )
            case "direct_message_file_image":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_direct_message(
                        msg.guild_id,
                        content=_message_file_image(
                            "direct_message_file_image 测试消息"
                        ),
                        **kwargs,
                    ),
                )
            case "direct_embed":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_direct_message(
                        msg.guild_id,
                        content=_embed(command),
                        **kwargs,
                    ),
                )
            case "direct_ark23":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_direct_message(
                        msg.guild_id,
                        content=_ark23(command),
                        **kwargs,
                    ),
                )
            case "direct_ark24":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_direct_message(
                        msg.guild_id,
                        content=_ark24(command),
                        **kwargs,
                    ),
                )
            case "direct_ark37":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_direct_message(
                        msg.guild_id,
                        content=_ark37(command),
                        **kwargs,
                    ),
                )
            case "direct_markdown":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_direct_message(
                        msg.guild_id,
                        content=_markdown(command),
                        **kwargs,
                    ),
                )
            case "direct_reference":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_direct_message(
                        msg.guild_id,
                        content="direct_reference 测试消息",
                        message_reference_id=msg.id,
                        **kwargs,
                    ),
                )
            case "direct_reference_ignore":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_direct_message(
                        msg.guild_id,
                        content="direct_reference_ignore 测试消息",
                        message_reference_id=msg.id,
                        ignore_message_reference_error=True,
                        **kwargs,
                    ),
                )
            case "direct_event_id":
                await _run_case(
                    bot,
                    msg,
                    command,
                    bot.api.send_direct_message(
                        msg.guild_id,
                        content="direct_event_id 测试消息",
                        **_passive_kwargs(msg, prefer_event_id=True),
                    ),
                )
            case "direct_error_mixed":
                await _run_expected_error(
                    bot,
                    msg,
                    command,
                    bot.api.send_direct_message(
                        msg.guild_id,
                        content=_message("direct_error_mixed"),
                        image=IMAGE_URL,
                        **kwargs,
                    ),
                )

    bot.start()


if __name__ == "__main__":
    main()
