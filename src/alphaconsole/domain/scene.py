from __future__ import annotations

from dataclasses import dataclass

from .app import ContentApp
from .block import Block
from .context import IssueBuildContext


@dataclass(slots=True)
class SceneBlock(Block):
    scene_note: str | None
    checklist_items: tuple[str, ...]


@dataclass(slots=True)
class SceneApp(ContentApp):
    scene_note: str | None
    checklist_items: tuple[str, ...]
    scene_description: str | None
    recurrence_rule: str | None

    def publish(self, ctx: IssueBuildContext) -> SceneBlock | None:
        if self.scene_note is None and not self.checklist_items:
            return None

        return SceneBlock(
            block_id=f"{ctx.issue_id}:{self.app_id}",
            block_type="scene",
            title=self.name,
            body=self._build_body(),
            source_app_id=self.app_id,
            source_app_type=self.app_type,
            publication_slot_id=self.target_publication_slot_id
            if ctx.publication_slot_id is not None
            else None,
            trigger_mode=self.resolve_trigger_mode(ctx),
            merge_policy=self.default_merge_policy,
            expires_at=self.resolve_expires_at(ctx),
            template_type=self.default_template_type,
            created_at=ctx.issued_at,
            scene_note=self.scene_note,
            checklist_items=self.checklist_items,
        )

    def _build_body(self) -> str:
        lines: list[str] = []
        if self.scene_note is not None:
            lines.append(self.scene_note)
        if self.checklist_items:
            lines.extend(f"[ ] {item}" for item in self.checklist_items)

        return "\n".join(lines)
