from __future__ import annotations

from .width import char_display_width, display_width


def wrap_text(text: str, width: int) -> list[str]:
    if width <= 0:
        raise ValueError("width must be positive.")

    paragraphs = text.split("\n")
    lines: list[str] = []

    for paragraph in paragraphs:
        if paragraph == "":
            lines.append("")
            continue
        lines.extend(_wrap_single_paragraph(paragraph, width))

    return lines or [""]


def wrap_paragraphs(text: str, width: int) -> list[str]:
    return wrap_text(text, width)


def _wrap_single_paragraph(paragraph: str, width: int) -> list[str]:
    if paragraph == "":
        return [""]

    for char in paragraph:
        if char_display_width(char) > width:
            raise ValueError("width is too small for the input text.")

    lines: list[str] = []
    remaining = paragraph

    while remaining:
        if display_width(remaining) <= width:
            lines.append(remaining.rstrip())
            break

        cut_index = _find_wrap_index(remaining, width)
        if cut_index <= 0:
            raise ValueError("Unable to wrap paragraph within width.")

        line = remaining[:cut_index].rstrip()
        if line:
            lines.append(line)

        remaining = remaining[cut_index:].lstrip()

    return lines or [""]


def _find_wrap_index(text: str, width: int) -> int:
    current_width = 0
    last_break_index: int | None = None

    for index, char in enumerate(text):
        char_width = char_display_width(char)
        if current_width + char_width > width:
            if char.isspace():
                return index
            if last_break_index is not None:
                return last_break_index
            return index

        current_width += char_width
        if char.isspace():
            last_break_index = index + 1

    return len(text)
