#!/usr/bin/env python3
"""
EasyBot SDK 构建器模块

提供所有消息和内容的构建类，用于构建发送消息所需的参数。

使用示例：
    # 普通消息
    msg = MessagesModel.Message(content="Hello", image="https://...")

    # Embed 消息
    embed = MessagesModel.MessageEmbed(title="标题", content=["行1", "行2"])

    # Ark 消息
    ark = MessagesModel.MessageArk23(content=["文本1", "文本2"], link=["link1", "link2"])

    # Markdown 消息
    md = MessagesModel.MessageMarkdown(template_id="xxx", key_values={"key": "value"})

    # 帖子内容（JSON 格式发帖）
    content = (Builders.ThreadContentBuilder()
        .add_text_paragraph("第一段文字")
        .add_image_paragraph("https://example.com/image.png")
        .build())
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, BinaryIO

if TYPE_CHECKING:
    from .models import ThreadContent, ThreadContentParagraph


class MessagesModel:
    """
    消息模型入口类

    所有消息构建类都通过 MessagesModel.xxx 访问。

    使用示例：
        msg = MessagesModel.Message(content="Hello")
        embed = MessagesModel.MessageEmbed(title="标题")
        ark = MessagesModel.MessageArk23(content=["文本"], link=["link"])
        md = MessagesModel.MessageMarkdown(content="# 标题")
    """

    class Message:
        """
        普通消息构建类

        用于构建文本、图片、引用等普通消息。

        Args:
            content: 消息文本
            image: 图片 URL（网络图片）
            file_image: 本地图片（bytes/BinaryIO/文件路径）
            media_file_info: 富媒体文件信息（v2 API）
            message_reference_id: 引用消息 ID
            ignore_message_reference_error: 是否忽略引用消息错误
            is_wakeup: 是否为互动召回消息（仅单聊 v2 API）

        使用示例：
            # 纯文本
            msg = MessagesModel.Message(content="Hello World")

            # 图片
            msg = MessagesModel.Message(content="图片", image="https://example.com/image.png")

            # 本地图片
            msg = MessagesModel.Message(content="图片", file_image="./image.png")

            # 引用回复
            msg = MessagesModel.Message(content="回复", message_reference_id="msg_id")

            # 富媒体（v2 API）
            msg = MessagesModel.Message(media_file_info="file_info_string")
        """

        def __init__(
            self,
            content: str | int | float | None = None,
            image: str | None = None,
            file_image: bytes | BinaryIO | str | None = None,
            media_file_info: str | None = None,
            message_reference_id: str | None = None,
            ignore_message_reference_error: bool = False,
            is_wakeup: bool = False,
        ):
            if content is not None and not isinstance(content, str):
                content = str(content)

            self._content = content
            self._image = image
            self._file_image = file_image
            self._media_file_info = media_file_info
            self._message_reference_id = message_reference_id
            self._ignore_message_reference_error = ignore_message_reference_error
            self._is_wakeup = is_wakeup
            self._msg_type = 7 if media_file_info else 0

        def __repr__(self) -> str:
            return (
                f"<Message content={self._content}, image={self._image}, "
                f"media_file_info={self._media_file_info}>"
            )

        @property
        def msg_type(self) -> int:
            """消息类型"""
            return self._msg_type

        def build(self) -> dict[str, Any]:
            """
            构建消息数据

            Returns:
                dict: 用于 API 请求的数据
            """
            if (self._image or self._file_image) and self._media_file_info:
                raise ValueError("image/file_image 与 media_file_info 不可同时存在")

            data: dict[str, Any] = {}

            if self._content:
                data["content"] = self._content

            if self._message_reference_id:
                data["message_reference"] = {
                    "message_id": self._message_reference_id,
                    "ignore_get_message_error": self._ignore_message_reference_error,
                }

            if self._is_wakeup:
                data["is_wakeup"] = self._is_wakeup

            if self._media_file_info:
                data["media"] = {"file_info": self._media_file_info}
            elif self._image:
                data["image"] = self._image
            elif self._file_image is not None:
                data["file_image"] = self._read_file_image()

            return data

        def _read_file_image(self) -> bytes:
            """读取文件图片"""
            if isinstance(self._file_image, bytes):
                return self._file_image

            if hasattr(self._file_image, "read"):
                return self._file_image.read()

            if isinstance(self._file_image, str):
                path = Path(self._file_image)
                if path.exists():
                    return path.read_bytes()
                if self._file_image.startswith("http"):
                    raise ValueError("发送网络图片请使用 image 参数，而非 file_image")
                raise FileNotFoundError(f"图片文件不存在: {self._file_image}")

            raise TypeError(f"file_image 不支持 {type(self._file_image)} 类型")

    class MessageEmbed:
        """
        Embed 消息构建类

        Args:
            title: 标题文本
            content: 内容文本列表，每项一行
            image: 缩略图 URL
            prompt: 消息弹窗通知文本

        使用示例：
            embed = MessagesModel.MessageEmbed(
                title="标题",
                content=["第一行", "第二行"],
                image="https://example.com/thumb.png",
                prompt="通知文本"
            )
        """

        def __init__(
            self,
            title: str | None = None,
            content: list[str] | str | None = None,
            image: str | None = None,
            prompt: str | None = None,
        ):
            self._title = title
            self._content = (
                content if isinstance(content, list) else [content] if content else []
            )
            self._image = image
            self._prompt = prompt
            self._msg_type = 4

        def __repr__(self) -> str:
            return f"<MessageEmbed title={self._title}, prompt={self._prompt}>"

        @property
        def msg_type(self) -> int:
            """消息类型"""
            return self._msg_type

        def build(self) -> dict[str, Any]:
            """构建 Embed 消息数据"""
            embed: dict[str, Any] = {
                "title": self._title,
                "prompt": self._prompt,
                "fields": [{"name": line} for line in self._content],
            }
            if self._image:
                embed["thumbnail"] = {"url": self._image}
            return {"embed": embed}

    class MessageArk23:
        """
        Ark 23 模板消息（链接+文本列表）

        Args:
            content: 内容文本列表
            link: 链接 URL 列表，长度应与 content 一致
            desc: 描述文本
            prompt: 消息弹窗通知文本

        使用示例：
            ark = MessagesModel.MessageArk23(
                content=["文本1", "文本2"],
                link=["https://link1.com", "https://link2.com"],
                desc="描述",
                prompt="通知"
            )
        """

        def __init__(
            self,
            content: list[str],
            link: list[str],
            desc: str | None = None,
            prompt: str | None = None,
        ):
            if len(content) != len(link):
                raise ValueError("content 与 link 长度必须一致")

            self._content = content
            self._link = link
            self._desc = desc
            self._prompt = prompt
            self._msg_type = 3

        def __repr__(self) -> str:
            return f"<MessageArk23 items={len(self._content)}>"

        @property
        def msg_type(self) -> int:
            """消息类型"""
            return self._msg_type

        def build(self) -> dict[str, Any]:
            """构建 Ark 23 消息数据"""
            obj_list = []
            for text, link in zip(self._content, self._link):
                obj_list.append(
                    {
                        "obj_kv": [
                            {"key": "desc", "value": text},
                            {"key": "link", "value": link},
                        ]
                    }
                )

            ark = {
                "template_id": 23,
                "kv": [
                    {"key": "#DESC#", "value": self._desc},
                    {"key": "#PROMPT#", "value": self._prompt},
                    {"key": "#LIST#", "obj": obj_list},
                ],
            }
            return {"ark": ark}

    class MessageArk24:
        """
        Ark 24 模板消息（文本+缩略图）

        Args:
            title: 标题文本
            content: 详情描述文本
            subtitle: 副标题文本
            link: 跳转链接 URL
            image: 缩略图 URL
            desc: 描述文本
            prompt: 消息弹窗通知文本

        使用示例：
            ark = MessagesModel.MessageArk24(
                title="标题",
                content="内容描述",
                subtitle="副标题",
                link="https://example.com",
                image="https://example.com/thumb.png"
            )
        """

        def __init__(
            self,
            title: str | None = None,
            content: str | None = None,
            subtitle: str | None = None,
            link: str | None = None,
            image: str | None = None,
            desc: str | None = None,
            prompt: str | None = None,
        ):
            self._title = title
            self._content = content
            self._subtitle = subtitle
            self._link = link
            self._image = image
            self._desc = desc
            self._prompt = prompt
            self._msg_type = 3

        def __repr__(self) -> str:
            return f"<MessageArk24 title={self._title}>"

        @property
        def msg_type(self) -> int:
            """消息类型"""
            return self._msg_type

        def build(self) -> dict[str, Any]:
            """构建 Ark 24 消息数据"""
            ark = {
                "template_id": 24,
                "kv": [
                    {"key": "#DESC#", "value": self._desc},
                    {"key": "#PROMPT#", "value": self._prompt},
                    {"key": "#TITLE#", "value": self._title},
                    {"key": "#METADESC#", "value": self._content},
                    {"key": "#IMG#", "value": self._image},
                    {"key": "#LINK#", "value": self._link},
                    {"key": "#SUBTITLE#", "value": self._subtitle},
                ],
            }
            return {"ark": ark}

    class MessageArk37:
        """
        Ark 37 模板消息（大图）

        Args:
            title: 标题文本
            content: 内容文本
            link: 跳转链接 URL
            image: 大图 URL
            prompt: 消息弹窗通知文本

        使用示例：
            ark = MessagesModel.MessageArk37(
                title="标题",
                content="内容",
                link="https://example.com",
                image="https://example.com/cover.png"
            )
        """

        def __init__(
            self,
            title: str | None = None,
            content: str | None = None,
            link: str | None = None,
            image: str | None = None,
            prompt: str | None = None,
        ):
            self._title = title
            self._content = content
            self._link = link
            self._image = image
            self._prompt = prompt
            self._msg_type = 3

        def __repr__(self) -> str:
            return f"<MessageArk37 title={self._title}>"

        @property
        def msg_type(self) -> int:
            """消息类型"""
            return self._msg_type

        def build(self) -> dict[str, Any]:
            """构建 Ark 37 消息数据"""
            ark = {
                "template_id": 37,
                "kv": [
                    {"key": "#PROMPT#", "value": self._prompt},
                    {"key": "#METATITLE#", "value": self._title},
                    {"key": "#METASUBTITLE#", "value": self._content},
                    {"key": "#METACOVER#", "value": self._image},
                    {"key": "#METAURL#", "value": self._link},
                ],
            }
            return {"ark": ark}

    class MessageMarkdown:
        """
        Markdown 消息构建类

        Args:
            content: 原生 Markdown 内容（与 template_id 二选一）
            template_id: Markdown 模板 ID
            key_values: 模板参数，格式 {key: value} 或 [{"key": "k", "values": ["v"]}]
            keyboard_id: Keyboard 模板 ID（与 keyboard_content 二选一）
            keyboard_content: 原生 Keyboard 内容

        使用示例：
            # 原生 Markdown
            md = MessagesModel.MessageMarkdown(content="# 标题\\n内容")

            # 模板方式
            md = MessagesModel.MessageMarkdown(
                template_id="template_123",
                key_values={"key1": "value1", "key2": "value2"}
            )

            # 带 Keyboard 模板 ID
            md = MessagesModel.MessageMarkdown(
                content="# 标题",
                keyboard_id="kb_template"
            )

            # 带自定义 Keyboard
            md = MessagesModel.MessageMarkdown(
                content="# 标题",
                keyboard_content={"rows": [{"buttons": [...]}]}
            )
        """

        def __init__(
            self,
            content: str | None = None,
            template_id: str | None = None,
            key_values: dict[str, str | list[str]] | list[dict] | None = None,
            keyboard_id: str | None = None,
            keyboard_content: dict | None = None,
        ):
            if content and template_id:
                raise ValueError("content 与 template_id 不可同时存在")

            self._content = content
            self._template_id = template_id
            self._key_values = key_values
            self._keyboard_id = keyboard_id
            self._keyboard_content = keyboard_content
            self._msg_type = 2

        def __repr__(self) -> str:
            return f"<MessageMarkdown template_id={self._template_id}>"

        @property
        def msg_type(self) -> int:
            """消息类型"""
            return self._msg_type

        def build(self) -> dict[str, Any]:
            """构建 Markdown 消息数据"""
            data: dict[str, Any] = {}

            if self._content:
                # markdown.content: Markdown 对象的内容，用于渲染 Markdown 消息
                data["markdown"] = {"content": self._content}
                # 顶级 content: 消息文本内容，群聊场景必填，用于消息列表预览、通知显示等
                data["content"] = self._content
            elif self._template_id:
                if not self._key_values:
                    raise ValueError("使用模板时必须提供 key_values")

                params = self._build_params()
                data["markdown"] = {
                    "custom_template_id": self._template_id,
                    "params": params,
                }
                text_values = []
                for p in params:
                    text_values.extend(p.get("values", []))
                data["content"] = " ".join(text_values)
            else:
                raise ValueError("必须提供 content 或 template_id")

            if self._keyboard_content:
                data["keyboard"] = {"content": self._keyboard_content}
            elif self._keyboard_id:
                data["keyboard"] = {"id": self._keyboard_id}

            return data

        def _build_params(self) -> list[dict]:
            """构建模板参数"""
            if isinstance(self._key_values, list):
                return self._key_values

            params = []
            for k, v in self._key_values.items():
                if isinstance(v, list):
                    params.append({"key": k, "values": v})
                else:
                    params.append({"key": k, "values": [str(v)]})
            return params


class ParagraphBuilder:
    """
    段落构建器

    用于构建 ThreadContentParagraph 对象，提供流畅的 API。

    使用示例:
        paragraph = (ParagraphBuilder()
            .add_text("Hello World", bold=True)
            .add_image("https://example.com/image.png")
            .set_alignment(Alignment.ALIGNMENT_CENTER)
            .build())
    """

    def __init__(self):
        self._elems: list = []
        self._alignment: int = 0

    def add_text(
        self,
        text: str,
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
    ) -> "ParagraphBuilder":
        """
        添加文本元素

        Args:
            text: 文本内容
            bold: 是否加粗
            italic: 是否斜体
            underline: 是否下划线

        Returns:
            ParagraphBuilder: 构建器实例
        """
        from .models import TextProps, ThreadContentElem, ThreadContentText

        text_props = TextProps(font_bold=bold, italic=italic, underline=underline)
        text_elem = ThreadContentText(text=text, props=text_props)
        elem = ThreadContentElem(type=ThreadContentElem.TYPE_TEXT, text=text_elem)
        self._elems.append(elem)
        return self

    def add_image(
        self,
        third_url: str,
        width_percent: float = 1.0,
    ) -> "ParagraphBuilder":
        """
        添加图片元素

        Args:
            third_url: 第三方图片链接
            width_percent: 宽度比例

        Returns:
            ParagraphBuilder: 构建器实例
        """
        from .models import ThreadContentElem, ThreadContentImage

        image_elem = ThreadContentImage(
            third_url=third_url, width_percent=width_percent
        )
        elem = ThreadContentElem(type=ThreadContentElem.TYPE_IMAGE, image=image_elem)
        self._elems.append(elem)
        return self

    def add_video(
        self,
        third_url: str,
    ) -> "ParagraphBuilder":
        """
        添加视频元素

        Args:
            third_url: 第三方视频链接

        Returns:
            ParagraphBuilder: 构建器实例
        """
        from .models import ThreadContentElem, ThreadContentVideo

        video_elem = ThreadContentVideo(third_url=third_url)
        elem = ThreadContentElem(type=ThreadContentElem.TYPE_VIDEO, video=video_elem)
        self._elems.append(elem)
        return self

    def add_url(
        self,
        url: str,
        desc: str = "",
    ) -> "ParagraphBuilder":
        """
        添加链接元素

        Args:
            url: 链接地址
            desc: 链接描述

        Returns:
            ParagraphBuilder: 构建器实例
        """
        from .models import ThreadContentElem, ThreadContentUrl

        url_elem = ThreadContentUrl(url=url, desc=desc)
        elem = ThreadContentElem(type=ThreadContentElem.TYPE_URL, url=url_elem)
        self._elems.append(elem)
        return self

    def set_alignment(self, alignment: int) -> "ParagraphBuilder":
        """
        设置段落对齐方式

        Args:
            alignment: 对齐方式，使用 Alignment 枚举值

        Returns:
            ParagraphBuilder: 构建器实例
        """
        self._alignment = alignment
        return self

    def build(self) -> "ThreadContentParagraph":
        """
        构建段落对象

        Returns:
            ThreadContentParagraph: 段落对象
        """
        from .models import ParagraphProps, ThreadContentParagraph

        props = ParagraphProps(alignment=self._alignment)
        return ThreadContentParagraph(elems=self._elems, props=props)


class ThreadContentBuilder:
    """
    帖子内容构建器

    用于构建 ThreadContent 对象，简化 JSON 格式发帖。

    使用示例:
        content = (ThreadContentBuilder()
            .add_text_paragraph("这是标题")
            .add_paragraph(
                ParagraphBuilder()
                .add_text("正文内容", bold=True)
                .add_image("https://example.com/image.png")
            )
            .build())

        await api.create_thread(channel_id, "帖子标题", content)
    """

    def __init__(self):
        self._paragraphs: list = []

    def add_paragraph(
        self,
        paragraph: "ThreadContentParagraph | ParagraphBuilder",
    ) -> "ThreadContentBuilder":
        """
        添加段落

        Args:
            paragraph: 段落对象或段落构建器

        Returns:
            ThreadContentBuilder: 构建器实例
        """
        if isinstance(paragraph, ParagraphBuilder):
            paragraph = paragraph.build()
        self._paragraphs.append(paragraph)
        return self

    def add_text_paragraph(
        self,
        text: str,
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
        alignment: int = 0,
    ) -> "ThreadContentBuilder":
        """
        添加纯文本段落（快捷方法）

        Args:
            text: 文本内容
            bold: 是否加粗
            italic: 是否斜体
            underline: 是否下划线
            alignment: 对齐方式

        Returns:
            ThreadContentBuilder: 构建器实例
        """
        paragraph = (
            ParagraphBuilder()
            .add_text(text, bold=bold, italic=italic, underline=underline)
            .set_alignment(alignment)
            .build()
        )
        self._paragraphs.append(paragraph)
        return self

    def add_image_paragraph(
        self,
        third_url: str,
        width_percent: float = 1.0,
        alignment: int = 0,
    ) -> "ThreadContentBuilder":
        """
        添加图片段落（快捷方法）

        Args:
            third_url: 第三方图片链接
            width_percent: 宽度比例
            alignment: 对齐方式

        Returns:
            ThreadContentBuilder: 构建器实例
        """
        paragraph = (
            ParagraphBuilder()
            .add_image(third_url, width_percent)
            .set_alignment(alignment)
            .build()
        )
        self._paragraphs.append(paragraph)
        return self

    def build(self) -> "ThreadContent":
        """
        构建帖子内容对象

        Returns:
            ThreadContent: 帖子内容对象
        """
        from .models import ThreadContent

        return ThreadContent(paragraphs=self._paragraphs)


class Builders:
    """
    论坛内容构建器入口类

    论坛内容构建类通过 Builders.xxx 访问。

    使用示例：
        content = Builders.ThreadContentBuilder().add_text_paragraph("文本").build()
    """

    ParagraphBuilder = ParagraphBuilder
    ThreadContentBuilder = ThreadContentBuilder
