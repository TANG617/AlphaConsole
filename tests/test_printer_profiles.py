from __future__ import annotations

from pathlib import Path

import pytest

from alphaconsole.config import compile_runtime_config, load_runtime_config
from alphaconsole.printing import GENERIC_58MM, GENERIC_80MM, resolve_printer_profile


def test_builtin_printer_profiles_are_resolvable() -> None:
    assert resolve_printer_profile("generic_58mm") == GENERIC_58MM
    assert resolve_printer_profile("generic_80mm") == GENERIC_80MM
    assert GENERIC_58MM.paper_width_mm == 58
    assert GENERIC_58MM.recommended_render_profile_name == "receipt_32"
    assert GENERIC_80MM.paper_width_mm == 80
    assert GENERIC_80MM.recommended_render_profile_name == "receipt_42"


def test_unknown_printer_profile_raises_clear_error() -> None:
    with pytest.raises(ValueError, match="Unsupported printer profile"):
        resolve_printer_profile("unknown_profile")


def test_target_without_explicit_render_profile_uses_printer_profile_default(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "runtime.toml"
    config_path.write_text(
        """
[delivery]
default_adapter = "stdout"

[printing]
default_target = "bytes_debug"

[[printer_targets]]
target_id = "bytes_debug"
kind = "escpos_bytes_file"
output_dir = "escpos"
printer_profile = "generic_58mm"
mode = "raster"

[[publication_slots]]
slot_id = "noon"
name = "Noon"
publish_time = "12:00"
is_enabled = true

[[scene_apps]]
app_id = "lunch"
name = "Lunch"
target_publication_slot_id = "noon"
scene_note = "Eat vegetables"
is_enabled = true
""".strip(),
        encoding="utf-8",
    )

    compiled = compile_runtime_config(load_runtime_config(config_path))

    assert compiled.printer_targets_by_id["bytes_debug"].render_profile_name == "receipt_32"
