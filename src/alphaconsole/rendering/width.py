from __future__ import annotations

import unicodedata


def char_display_width(char: str) -> int:
    if len(char) != 1:
        raise ValueError("char_display_width expects a single character.")
    if char in {"\n", "\r"}:
        return 0
    if char == "\t":
        return 4
    if unicodedata.combining(char):
        return 0
    if unicodedata.category(char).startswith("C"):
        return 0
    if unicodedata.east_asian_width(char) in {"F", "W"}:
        return 2
    return 1


def display_width(text: str) -> int:
    max_width = 0
    current_width = 0

    for char in text:
        if char == "\n":
            max_width = max(max_width, current_width)
            current_width = 0
            continue
        if char == "\r":
            continue

        current_width += char_display_width(char)

    return max(max_width, current_width)
