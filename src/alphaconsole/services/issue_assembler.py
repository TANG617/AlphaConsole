from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from uuid import uuid4

from alphaconsole.domain import (
    Block,
    ContentApp,
    Issue,
    IssueBuildContext,
    IssueHeader,
    MergePolicy,
    PublicationSlot,
    TriggerMode,
)


class IssueAssembler:
    def assemble_scheduled_issue(
        self,
        slot: PublicationSlot,
        apps: Sequence[ContentApp],
        now: datetime,
        sequence_of_day: int,
    ) -> Issue:
        issue = self._create_issue_shell(
            now=now,
            publication_slot_id=slot.slot_id,
            trigger_mode=TriggerMode.SCHEDULED,
            sequence_of_day=sequence_of_day,
        )
        ctx = self._build_context(issue, now)

        blocks = self._collect_scheduled_blocks(slot=slot, apps=apps, ctx=ctx)
        issue.blocks = tuple(blocks)
        return issue

    def assemble_immediate_issue(
        self,
        app: ContentApp,
        now: datetime,
        sequence_of_day: int,
    ) -> Issue:
        issue = self._create_issue_shell(
            now=now,
            publication_slot_id=None,
            trigger_mode=TriggerMode.IMMEDIATE,
            sequence_of_day=sequence_of_day,
        )
        ctx = self._build_context(issue, now)

        block = app.publish(ctx)
        if block is None or block.is_expired(now):
            issue.blocks = ()
            return issue

        issue.blocks = (block,)
        return issue

    def _create_issue_shell(
        self,
        *,
        now: datetime,
        publication_slot_id: str | None,
        trigger_mode: TriggerMode,
        sequence_of_day: int,
    ) -> Issue:
        issue_id = uuid4().hex
        header = IssueHeader(
            issue_date=now.date(),
            printed_at=now,
            sequence_of_day=sequence_of_day,
            trigger_mode=trigger_mode,
        )
        return Issue(
            issue_id=issue_id,
            issue_date=now.date(),
            publication_slot_id=publication_slot_id,
            trigger_mode=trigger_mode,
            sequence_of_day=sequence_of_day,
            header=header,
            blocks=(),
            created_at=now,
            printed_at=None,
        )

    def _build_context(self, issue: Issue, issued_at: datetime) -> IssueBuildContext:
        return IssueBuildContext(
            issue_id=issue.issue_id,
            issue_date=issue.issue_date,
            issued_at=issued_at,
            publication_slot_id=issue.publication_slot_id,
            trigger_mode=issue.trigger_mode,
            sequence_of_day=issue.sequence_of_day,
        )

    def _collect_scheduled_blocks(
        self,
        *,
        slot: PublicationSlot,
        apps: Sequence[ContentApp],
        ctx: IssueBuildContext,
    ) -> list[Block]:
        kept_blocks: list[tuple[datetime, int, Block]] = []

        for insert_order, app in enumerate(apps):
            if not app.is_enabled:
                continue
            if app.target_publication_slot_id != slot.slot_id:
                continue

            block = app.publish(ctx)
            if block is None:
                continue
            if block.is_expired(ctx.issued_at):
                continue
            if block.merge_policy is not MergePolicy.MERGEABLE:
                continue

            kept_blocks.append((block.created_at, insert_order, block))

        kept_blocks.sort(key=lambda item: (item[0], item[1]))
        return [block for _, _, block in kept_blocks]
