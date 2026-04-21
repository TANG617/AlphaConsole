from __future__ import annotations

from alphaconsole.rendering.layout import wrap_paragraphs, wrap_text
from alphaconsole.rendering.width import display_width


def test_display_width_for_ascii_text() -> None:
    assert display_width("AlphaConsole") == 12


def test_display_width_for_chinese_text() -> None:
    assert display_width("午餐") == 4


def test_display_width_for_mixed_text() -> None:
    assert display_width("Lunch午餐") == 9


def test_wrap_text_lines_do_not_exceed_target_width() -> None:
    lines = wrap_text("Remember vegetables and soup tonight", 16)

    assert lines == ["Remember", "vegetables and", "soup tonight"]
    assert all(display_width(line) <= 16 for line in lines)


def test_wrap_paragraphs_preserves_explicit_blank_lines() -> None:
    lines = wrap_paragraphs("Alpha beta\n\nGamma delta", 10)

    assert lines == ["Alpha beta", "", "Gamma", "delta"]
    assert all(display_width(line) <= 10 for line in lines if line)
