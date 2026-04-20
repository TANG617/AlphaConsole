from __future__ import annotations

from alphaconsole.domain import Block, Issue, SceneBlock

from .layout import wrap_paragraphs
from .header_renderer import render_issue_header
from .profile import RECEIPT_42, RenderProfile
from .scene_block_renderer import render_scene_block


def render_issue(issue: Issue, profile: RenderProfile = RECEIPT_42) -> str:
    parts = [render_issue_header(issue.header, profile)]
    rendered_blocks = [
        rendered for block in issue.blocks if (rendered := _render_block(block, profile))
    ]

    if rendered_blocks:
        separator = profile.block_rule_char * profile.line_width
        joiner = (
            f"\n\n{separator}\n\n"
            if profile.blank_line_between_blocks
            else f"\n{separator}\n"
        )
        parts.append(joiner.join(rendered_blocks))

    return "\n\n".join(parts)


def render_issue_text(issue: Issue, profile: RenderProfile = RECEIPT_42) -> str:
    # Backward-compatible alias for the earlier Phase 3 function name.
    return render_issue(issue, profile)


def _render_block(block: Block, profile: RenderProfile) -> str:
    if isinstance(block, SceneBlock):
        return render_scene_block(block, profile)

    lines = wrap_paragraphs(f"[{block.title}]", profile.line_width)
    if block.body:
        lines.extend(wrap_paragraphs(block.body, profile.line_width))
    return "\n".join(lines)
