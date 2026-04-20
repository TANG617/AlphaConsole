from __future__ import annotations

from alphaconsole.domain import Block, Issue, SceneBlock

from .header_renderer import render_issue_header
from .scene_block_renderer import render_scene_block


def render_issue_text(issue: Issue) -> str:
    parts = [render_issue_header(issue.header)]

    if issue.blocks:
        block_text = "\n\n--------------------------------\n\n".join(
            _render_block(block) for block in issue.blocks
        )
        parts.append(block_text)

    return "\n\n".join(parts)


def _render_block(block: Block) -> str:
    if isinstance(block, SceneBlock):
        return render_scene_block(block)

    lines = [f"[{block.title}]"]
    if block.body:
        lines.append(block.body)
    return "\n".join(lines)
