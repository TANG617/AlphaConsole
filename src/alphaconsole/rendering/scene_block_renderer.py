from __future__ import annotations

from alphaconsole.domain import SceneBlock

from .layout import wrap_paragraphs
from .profile import RenderProfile
from .width import display_width


def render_scene_block(block: SceneBlock, profile: RenderProfile) -> str:
    note = block.scene_note if block.scene_note not in (None, "") else None
    if note is None and not block.checklist_items:
        return ""

    lines: list[str] = []
    lines.extend(wrap_paragraphs(f"[{block.title}]", profile.line_width))

    if note is not None:
        lines.extend(wrap_paragraphs(note, profile.line_width))
    if block.checklist_items:
        for item in block.checklist_items:
            lines.extend(_render_checklist_item(item, profile))

    _validate_line_widths(lines, profile.line_width)

    return "\n".join(lines)


def _render_checklist_item(item: str, profile: RenderProfile) -> list[str]:
    prefix = f"{profile.checkbox_token} "
    continuation_prefix = " " * display_width(prefix)
    content_width = profile.line_width - display_width(prefix)
    wrapped = wrap_paragraphs(item, content_width)

    lines: list[str] = []
    for index, line in enumerate(wrapped):
        if index == 0:
            lines.append(prefix.rstrip() if line == "" else f"{prefix}{line}")
            continue
        lines.append("" if line == "" else f"{continuation_prefix}{line}")
    return lines


def _validate_line_widths(lines: list[str], max_width: int) -> None:
    for line in lines:
        if display_width(line) > max_width:
            raise ValueError("Scene block rendering exceeded the profile width.")
