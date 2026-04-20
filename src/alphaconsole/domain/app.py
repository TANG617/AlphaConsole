from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, time

from .block import Block
from .context import IssueBuildContext
from .enums import MergePolicy, TriggerMode


@dataclass(slots=True)
class ContentApp(ABC):
    app_id: str
    app_type: str
    name: str
    description: str | None
    target_publication_slot_id: str | None
    prepare_at: time | None
    default_trigger_mode: TriggerMode
    default_merge_policy: MergePolicy
    default_template_type: str
    expiration_policy: str | None
    is_enabled: bool
    created_at: datetime
    updated_at: datetime

    def prepare(self, now: datetime) -> None:
        """Current phase keeps prepare as a no-op placeholder."""
        return None

    def resolve_expires_at(self, ctx: IssueBuildContext) -> datetime | None:
        if self.expiration_policy is None:
            return None
        raise NotImplementedError(
            "TODO: expiration_policy parsing is not defined in the current phase."
        )

    def resolve_trigger_mode(self, ctx: IssueBuildContext) -> TriggerMode:
        if self.default_trigger_mode == ctx.trigger_mode:
            return self.default_trigger_mode

        # TODO: product semantics for app default vs runtime actual trigger mode
        # are not fully frozen. Current phase favors the actual issue trigger.
        return ctx.trigger_mode

    @abstractmethod
    def publish(self, ctx: IssueBuildContext) -> Block | None:
        raise NotImplementedError
