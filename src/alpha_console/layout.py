from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .models import EntryKind, EntryRecord
from .timeutil import format_local, now_local


class TextRole(StrEnum):
    TITLE = "title"
    SUBTITLE = "subtitle"
    EMBLEM = "emblem"
    META = "meta"
    BODY = "body"
    FOOTER = "footer"


class TextAlign(StrEnum):
    LEFT = "left"
    CENTER = "center"


@dataclass(slots=True)
class SceneText:
    text: str
    role: TextRole
    align: TextAlign = TextAlign.LEFT


@dataclass(slots=True)
class SceneSection:
    label: str
    lines: list[SceneText]


@dataclass(slots=True)
class ReceiptScene:
    header_bar: str
    sections: list[SceneSection]


def build_receipt_scene(entry: EntryRecord) -> ReceiptScene:
    is_event = entry.kind is EntryKind.EVENT
    short_due = entry.due_at.astimezone().strftime("%Y-%m-%d %H:%M %Z")

    identity = SceneSection(
        label="IDENT",
        lines=[
            SceneText(".--[ LOCAL.CONSOLE ]--.", TextRole.EMBLEM, TextAlign.CENTER),
            SceneText("| SYS/TERM :: NODE-01 |", TextRole.EMBLEM, TextAlign.CENTER),
            SceneText("'--[ PRINT.CHANNEL ]-'", TextRole.EMBLEM, TextAlign.CENTER),
            SceneText(
                "SCHEDULE ALERT" if is_event else "OPS CHECKLIST",
                TextRole.TITLE,
                TextAlign.CENTER,
            ),
            SceneText(format_local(entry.due_at), TextRole.SUBTITLE, TextAlign.CENTER),
        ],
    )

    status = SceneSection(
        label="STATUS BLOCK",
        lines=[
            SceneText(
                f"{key:<5} :: {value}",
                TextRole.META,
            )
            for key, value in [
                ("MODE", "EVENT" if is_event else "CHECKLIST"),
                ("JOB", f"{entry.id:04d}"),
                ("STATE", entry.status.value.upper()),
                ("DUE", entry.due_at.astimezone().strftime("%m-%d %H:%M")),
                ("HOST", entry.printer_host),
            ]
        ],
    )

    payload_lines = [
        SceneText(f"TITLE :: {entry.title}", TextRole.BODY),
        SceneText(
            f"TRIGGER :: {short_due}" if is_event else "VERIFY ::",
            TextRole.BODY,
        ),
    ]
    if is_event:
        if entry.notes:
            payload_lines.extend(
                [
                    SceneText("", TextRole.BODY),
                    SceneText("NOTE ::", TextRole.BODY),
                    SceneText(entry.notes, TextRole.BODY),
                ]
            )
    else:
        payload_lines.extend(
            SceneText(f"[ ] {item.label}", TextRole.BODY) for item in entry.items
        )
        if entry.notes:
            payload_lines.extend(
                [
                    SceneText("", TextRole.BODY),
                    SceneText("NOTE ::", TextRole.BODY),
                    SceneText(entry.notes, TextRole.BODY),
                ]
            )

    payload = SceneSection(label="PAYLOAD", lines=payload_lines)

    footer = SceneSection(
        label="LOG STREAM",
        lines=[
            SceneText("LOG> ticket composed", TextRole.FOOTER),
            SceneText(
                f"LOG> generated {now_local().strftime('%m-%d %H:%M:%S')}",
                TextRole.FOOTER,
            ),
            SceneText("RC=00 :: PRINT READY", TextRole.FOOTER),
        ],
    )

    return ReceiptScene(
        header_bar="LOCAL CONSOLE // RETRO TERMINAL RECEIPT",
        sections=[identity, status, payload, footer],
    )
