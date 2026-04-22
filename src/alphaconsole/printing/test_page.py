from __future__ import annotations

from datetime import datetime

from alphaconsole.domain import TriggerMode
from alphaconsole.rendering import RenderProfile

from .artifact import RenderedReceipt


def build_test_receipt_text(profile: RenderProfile) -> str:
    return "\n".join(
        [
            "================================",
            "ALPHACONSOLE TEST PAGE",
            f"PROFILE: {profile.name}",
            "PATH: raster-first escpos",
            "CHECK: socket / bytes / stdout",
            "--------------------------------",
        ]
    )


def build_test_receipt(
    profile: RenderProfile,
    *,
    issue_id: str = "test-page",
    rendered_at: datetime | None = None,
) -> RenderedReceipt:
    return RenderedReceipt(
        issue_id=issue_id,
        publication_slot_id=None,
        trigger_mode=TriggerMode.IMMEDIATE,
        profile_name=profile.name,
        text=build_test_receipt_text(profile),
        rendered_at=rendered_at or datetime.now(),
    )
