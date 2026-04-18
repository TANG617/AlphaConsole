from __future__ import annotations

from datetime import datetime
from pathlib import Path
from textwrap import shorten
from unicodedata import east_asian_width

from PIL import Image, ImageDraw, ImageFont
from rich import box
from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from .config import Settings
from .layout import ReceiptScene, SceneSection, SceneText, TextAlign, TextRole


def render_ascii(scene: ReceiptScene, width: int) -> str:
    content_width = width - 4
    output: list[str] = []
    output.append(_box_top(content_width))
    output.append(_boxed_line(scene.header_bar, content_width, center=True))
    output.append(_box_rule(content_width))
    for section in scene.sections:
        output.append(_boxed_line(f"[ {section.label} ]", content_width))
        for line in section.lines:
            if not line.text:
                output.append(_boxed_line("", content_width))
                continue
            for segment in _wrap_display_text(line.text, content_width):
                output.append(
                    _boxed_line(
                        segment,
                        content_width,
                        center=line.align is TextAlign.CENTER,
                    )
                )
        output.append(_box_rule(content_width))
    output[-1] = _box_bottom(content_width)
    return "\n".join(output)


def render_rich(
    scene: ReceiptScene,
    settings: Settings,
    preview_path: str | None = None,
) -> RenderableType:
    theme = settings.theme
    blocks: list[RenderableType] = [
        Panel(
            Text(scene.header_bar, style="bold white on black", justify="center"),
            box=box.SQUARE,
            style="black on white",
            border_style="white",
            padding=(0, 1),
        )
    ]

    for section in scene.sections:
        blocks.append(
            Panel(
                _rich_section_group(section, theme.preview_width_chars),
                title=f" {section.label} ",
                box=box.SQUARE,
                style="black on white",
                border_style="black",
                padding=(0, 1),
            )
        )
    if preview_path:
        blocks.append(
            Text(
                f"PNG :: {preview_path}",
                style="bold black on white",
                justify="left",
            )
        )
    return Group(*blocks)


def render_to_image(scene: ReceiptScene, settings: Settings, output_path: Path) -> Path:
    theme = settings.theme
    width = settings.printer_width
    left = theme.page_margin_px
    right = width - theme.page_margin_px
    temp_image = Image.new("L", (width, 3200), 255)
    draw = ImageDraw.Draw(temp_image)
    fonts = _build_font_map(settings)
    theme = settings.theme

    y = theme.page_margin_px
    y = _draw_header_bar(draw, left, right, y, scene.header_bar, fonts["header"])
    y += theme.section_gap_px
    for section in scene.sections:
        y = _draw_panel(
            draw=draw,
            left=left,
            right=right,
            top=y,
            section=section,
            fonts=fonts,
            settings=settings,
            padding=theme.panel_padding_px,
        )
        y += theme.section_gap_px

    output_path.parent.mkdir(parents=True, exist_ok=True)
    final_image = temp_image.crop((0, 0, width, y + theme.page_margin_px)).convert("1")
    final_image.save(output_path)
    return output_path


def render_calibration_image(settings: Settings, output_path: Path) -> Path:
    theme = settings.theme
    width = settings.printer_width
    margin = theme.page_margin_px
    inner_margin = margin + 12
    height = 900
    image = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.truetype(str(settings.mono_font_path), theme.title_font_size)
    body_font = ImageFont.truetype(str(settings.font_path), max(20, theme.body_font_size - 6))
    mono_font = ImageFont.truetype(str(settings.mono_font_path), theme.meta_font_size)

    y = margin
    title = "PRINT WIDTH CALIBRATION"
    subtitle = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
    title_width = draw.textbbox((0, 0), title, font=title_font)[2]
    draw.text(((width - title_width) / 2, y), title, font=title_font, fill=0)
    y += 40
    subtitle_width = draw.textbbox((0, 0), subtitle, font=mono_font)[2]
    draw.text(((width - subtitle_width) / 2, y), subtitle, font=mono_font, fill=0)
    y += 40

    outer_left = 8
    outer_right = width - 8
    draw.rectangle((outer_left, y, outer_right, height - 60), outline=0, width=2)
    draw.text((outer_left + 2, y + 4), "L", font=body_font, fill=0)
    right_label_width = draw.textbbox((0, 0), "R", font=body_font)[2]
    draw.text((outer_right - right_label_width - 2, y + 4), "R", font=body_font, fill=0)
    y += 36

    center_x = width // 2
    draw.line((center_x, y, center_x, height - 70), fill=0, width=1)

    content_left = inner_margin
    content_right = width - inner_margin
    ruler_y = y + 16
    draw.line((content_left, ruler_y, content_right, ruler_y), fill=0, width=2)
    tick_step = 24
    for x in range(content_left, content_right + 1, tick_step):
        tick_height = 12 if (x - content_left) % (tick_step * 4) == 0 else 7
        draw.line((x, ruler_y - tick_height, x, ruler_y + tick_height), fill=0, width=1)

    y = ruler_y + 28
    info_lines = [
        f"printer_width = {width}px",
        f"content box = {content_right - content_left}px",
        "边框应完整可见，左右留白应接近对称。",
        "如果右侧被裁切，减小 ALPHA_CONSOLE_PRINTER_WIDTH。",
        "如果左右留白过大，可适当增大该值。",
        "",
        "|012345678901234567890123456789|",
        "|雨伞 水杯 耳机 钥匙 门卡 电脑|",
        "|wallet phone cable notebook |",
        "",
        "中心线应穿过本页正中。",
        "上方刻度用于观察横向压缩或裁切。",
    ]
    for line in info_lines:
        if not line:
            y += 14
            continue
        wrapped = _wrap_pixel_text(draw, line, mono_font, content_right - content_left)
        for segment in wrapped:
            draw.text((content_left, y), segment, font=mono_font, fill=0)
            y += 28

    draw.line((content_left, y + 10, content_right, y + 10), fill=0, width=2)
    y += 28
    sample_box_top = y
    sample_box_bottom = y + 170
    draw.rectangle(
        (content_left, sample_box_top, content_right, sample_box_bottom),
        outline=0,
        width=2,
    )
    draw.text((content_left + 12, sample_box_top + 14), "Sample block", font=body_font, fill=0)
    draw.text((content_left + 12, sample_box_top + 52), "[ ] Checklist item 1", font=body_font, fill=0)
    draw.text((content_left + 12, sample_box_top + 90), "[ ] Checklist item 2", font=body_font, fill=0)
    draw.text((content_left + 12, sample_box_top + 128), "Meeting 18:45  Prepare PDF", font=body_font, fill=0)

    footer = "AlphaConsole MVP / Calibration"
    footer_width = draw.textbbox((0, 0), footer, font=mono_font)[2]
    draw.text(((width - footer_width) / 2, height - 48), footer, font=mono_font, fill=0)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("1").save(output_path)
    return output_path


def _rich_section_group(section: SceneSection, width_chars: int) -> RenderableType:
    texts: list[RenderableType] = []
    for line in section.lines:
        if not line.text:
            texts.append(Text(""))
            continue
        for segment in _wrap_display_text(line.text, width_chars):
            texts.append(
                Text(
                    segment,
                    style=_rich_style(line.role),
                    justify=line.align.value,
                )
            )
    return Group(*texts)


def _rich_style(role: TextRole) -> str:
    if role is TextRole.TITLE:
        return "bold black on white"
    if role is TextRole.SUBTITLE:
        return "black on white"
    if role is TextRole.EMBLEM:
        return "bold black on white"
    if role is TextRole.META:
        return "black on white"
    if role is TextRole.FOOTER:
        return "dim black on white"
    return "bold black on white"


def _build_font_map(settings: Settings) -> dict[str, ImageFont.ImageFont]:
    theme = settings.theme
    return {
        "header": ImageFont.truetype(str(settings.mono_font_path), theme.header_font_size),
        "title": ImageFont.truetype(str(settings.mono_font_path), theme.title_font_size),
        "subtitle": ImageFont.truetype(str(settings.font_path), theme.subtitle_font_size),
        "emblem": ImageFont.truetype(str(settings.mono_font_path), theme.emblem_font_size),
        "label": ImageFont.truetype(str(settings.mono_font_path), theme.label_font_size),
        "meta": ImageFont.truetype(str(settings.mono_font_path), theme.meta_font_size),
        "body": ImageFont.truetype(str(settings.font_path), theme.body_font_size),
        "footer": ImageFont.truetype(str(settings.mono_font_path), theme.footer_font_size),
    }


def _draw_header_bar(
    draw: ImageDraw.ImageDraw,
    left: int,
    right: int,
    top: int,
    text: str,
    font: ImageFont.ImageFont,
) -> int:
    bottom = top + 28
    draw.rectangle((left, top, right, bottom), fill=0)
    text_width = draw.textbbox((0, 0), text, font=font)[2]
    draw.text(((left + right - text_width) / 2, top + 5), text, font=font, fill=255)
    return bottom


def _draw_panel(
    draw: ImageDraw.ImageDraw,
    left: int,
    right: int,
    top: int,
    section: SceneSection,
    fonts: dict[str, ImageFont.ImageFont],
    settings: Settings,
    padding: int,
) -> int:
    label_font = fonts["label"]
    label_width = draw.textbbox((0, 0), section.label, font=label_font)[2]
    tab_height = 24
    tab_width = min(right - left - 30, max(120, label_width + 28))
    draw.rectangle((left + 10, top, left + 10 + tab_width, top + tab_height), fill=0)
    draw.text((left + 22, top + 4), section.label, font=label_font, fill=255)

    content_top = top + tab_height - 1
    y = content_top + padding
    max_width = right - left - padding * 2
    for line in section.lines:
        font, line_height = _font_and_line_height(line.role, fonts, settings)
        if not line.text:
            y += max(12, line_height // 2)
            continue
        wrapped = _wrap_pixel_text(draw, line.text, font, max_width)
        for segment in wrapped:
            x = left + padding
            if line.align is TextAlign.CENTER:
                text_width = draw.textbbox((0, 0), segment, font=font)[2]
                x = int((left + right - text_width) / 2)
            draw.text((x, y), segment, font=font, fill=0)
            y += line_height
    bottom = y + padding - 2
    draw.rectangle((left, content_top, right, bottom), outline=0, width=2)
    return bottom


def _font_and_line_height(
    role: TextRole,
    fonts: dict[str, ImageFont.ImageFont],
    settings: Settings,
) -> tuple[ImageFont.ImageFont, int]:
    theme = settings.theme
    mapping = {
        TextRole.TITLE: (fonts["title"], theme.body_line_height),
        TextRole.SUBTITLE: (fonts["subtitle"], max(26, theme.meta_line_height + 2)),
        TextRole.EMBLEM: (fonts["emblem"], max(22, theme.meta_line_height)),
        TextRole.META: (fonts["meta"], theme.meta_line_height),
        TextRole.BODY: (fonts["body"], theme.body_line_height),
        TextRole.FOOTER: (fonts["footer"], theme.footer_line_height),
    }
    return mapping[role]


def _wrap_pixel_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    lines: list[str] = []
    current = ""
    for char in text:
        candidate = current + char
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if bbox[2] <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
            current = char
        else:
            lines.append(candidate)
            current = ""
    if current:
        lines.append(current)
    return lines or [text]


def _display_width(text: str) -> int:
    width = 0
    for char in text:
        width += 2 if east_asian_width(char) in {"W", "F"} else 1
    return width


def _wrap_display_text(text: str, width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    current_width = 0
    for char in text:
        char_width = 2 if east_asian_width(char) in {"W", "F"} else 1
        if current and current_width + char_width > width:
            lines.append(current)
            current = char
            current_width = char_width
        else:
            current += char
            current_width += char_width
    if current:
        lines.append(current)
    return lines or [text]


def _box_top(content_width: int) -> str:
    return "+" + "-" * (content_width + 2) + "+"


def _box_rule(content_width: int) -> str:
    return "|" + "-" * (content_width + 2) + "|"


def _box_bottom(content_width: int) -> str:
    return "+" + "-" * (content_width + 2) + "+"


def _boxed_line(text: str, width: int, center: bool = False) -> str:
    content = _center(text, width) if center else _pad_display(text, width)
    return f"| {content} |"


def _pad_display(text: str, width: int) -> str:
    padding = max(0, width - _display_width(text))
    return text + (" " * padding)


def _center(text: str, width: int) -> str:
    clipped = shorten(text, width=width, placeholder="…")
    padding = max(0, width - _display_width(clipped))
    left = padding // 2
    right = padding - left
    return (" " * left) + clipped + (" " * right)
