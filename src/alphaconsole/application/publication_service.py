from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from alphaconsole.domain import ContentApp, PublicationSlot
from alphaconsole.printing import PrintService, PrinterAdapter
from alphaconsole.rendering import RECEIPT_42, RenderProfile
from alphaconsole.services import IssueAssembler

from .publication_result import PublicationResult


class PublicationService:
    def __init__(
        self,
        assembler: IssueAssembler | None = None,
        print_service: PrintService | None = None,
    ) -> None:
        self._assembler = assembler or IssueAssembler()
        self._print_service = print_service or PrintService()

    def publish_scheduled(
        self,
        slot: PublicationSlot,
        apps: Sequence[ContentApp],
        adapter: PrinterAdapter,
        now: datetime,
        sequence_of_day: int,
        profile: RenderProfile = RECEIPT_42,
    ) -> PublicationResult:
        issue = self._assembler.assemble_scheduled_issue(
            slot=slot,
            apps=apps,
            now=now,
            sequence_of_day=sequence_of_day,
        )
        receipt = self._print_service.print_issue(
            issue=issue,
            adapter=adapter,
            profile=profile,
        )
        return PublicationResult(
            issue=issue,
            receipt=receipt,
            adapter_name=adapter.name,
        )

    def publish_immediate(
        self,
        app: ContentApp,
        adapter: PrinterAdapter,
        now: datetime,
        sequence_of_day: int,
        profile: RenderProfile = RECEIPT_42,
    ) -> PublicationResult:
        issue = self._assembler.assemble_immediate_issue(
            app=app,
            now=now,
            sequence_of_day=sequence_of_day,
        )
        receipt = self._print_service.print_issue(
            issue=issue,
            adapter=adapter,
            profile=profile,
        )
        return PublicationResult(
            issue=issue,
            receipt=receipt,
            adapter_name=adapter.name,
        )
