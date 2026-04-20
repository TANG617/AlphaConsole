from __future__ import annotations

from alphaconsole.domain import SceneBlock


def render_scene_block(block: SceneBlock) -> str:
    lines = [f"[{block.title}]"]

    if block.scene_note is not None:
        lines.append(block.scene_note)
    if block.checklist_items:
        lines.extend(f"[ ] {item}" for item in block.checklist_items)

    return "\n".join(lines)
