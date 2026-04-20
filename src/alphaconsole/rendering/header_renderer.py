from __future__ import annotations

from alphaconsole.domain import IssueHeader


def render_issue_header(header: IssueHeader) -> str:
    lines = [
        "================================",
        f"DATE: {header.issue_date.isoformat()}",
        f"PRINTED: {header.printed_at.strftime('%H:%M')}",
        f"ISSUE NO: {header.sequence_of_day}",
        f"TRIGGER: {header.trigger_mode.value}",
        "--------------------------------",
    ]
    return "\n".join(lines)
