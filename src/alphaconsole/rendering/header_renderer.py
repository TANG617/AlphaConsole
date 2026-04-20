from __future__ import annotations

from alphaconsole.domain import IssueHeader

from .profile import RenderProfile
from .width import display_width


def render_issue_header(header: IssueHeader, profile: RenderProfile) -> str:
    lines = [
        profile.header_rule_char * profile.line_width,
        f"DATE: {header.issue_date.isoformat()}",
        f"PRINTED: {header.printed_at.strftime('%H:%M')}",
        f"ISSUE NO: {header.sequence_of_day}",
        f"TRIGGER: {header.trigger_mode.value}",
        profile.block_rule_char * profile.line_width,
    ]
    _validate_line_widths(lines, profile.line_width)
    return "\n".join(lines)


def _validate_line_widths(lines: list[str], max_width: int) -> None:
    for line in lines:
        if display_width(line) > max_width:
            raise ValueError("Header rendering exceeded the profile width.")
