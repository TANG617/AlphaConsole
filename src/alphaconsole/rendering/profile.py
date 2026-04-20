from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class RenderProfile:
    name: str
    line_width: int
    header_rule_char: str = "="
    block_rule_char: str = "-"
    checkbox_token: str = "[ ]"
    blank_line_between_blocks: bool = True

    def __post_init__(self) -> None:
        if self.line_width <= 0:
            raise ValueError("line_width must be positive.")
        if len(self.header_rule_char) != 1:
            raise ValueError("header_rule_char must be a single character.")
        if len(self.block_rule_char) != 1:
            raise ValueError("block_rule_char must be a single character.")
        if not self.checkbox_token:
            raise ValueError("checkbox_token must not be empty.")


RECEIPT_32 = RenderProfile(name="receipt_32", line_width=32)
RECEIPT_42 = RenderProfile(name="receipt_42", line_width=42)
