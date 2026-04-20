from __future__ import annotations

from datetime import datetime

from alphaconsole.domain import Issue
from alphaconsole.rendering import RECEIPT_42, RenderProfile, render_issue

from .adapter import PrinterAdapter
from .artifact import RenderedReceipt


class PrintService:
    def render_issue_to_receipt(
        self,
        issue: Issue,
        profile: RenderProfile = RECEIPT_42,
    ) -> RenderedReceipt:
        return RenderedReceipt(
            issue_id=issue.issue_id,
            publication_slot_id=issue.publication_slot_id,
            trigger_mode=issue.trigger_mode,
            profile_name=profile.name,
            text=render_issue(issue, profile),
            rendered_at=datetime.now(),
        )

    def print_issue(
        self,
        issue: Issue,
        adapter: PrinterAdapter,
        profile: RenderProfile = RECEIPT_42,
    ) -> RenderedReceipt:
        receipt = self.render_issue_to_receipt(issue, profile)
        adapter.deliver(receipt)
        return receipt
