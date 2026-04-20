from enum import StrEnum


class TriggerMode(StrEnum):
    SCHEDULED = "scheduled"
    IMMEDIATE = "immediate"


class MergePolicy(StrEnum):
    MERGEABLE = "mergeable"
    STANDALONE = "standalone"
