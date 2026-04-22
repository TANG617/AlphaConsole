from __future__ import annotations

from pathlib import Path

import pytest

from alphaconsole.config import (
    RuntimeConfigError,
    compile_runtime_config,
    load_runtime_config,
)


def test_load_runtime_config_reads_minimal_toml(tmp_path: Path) -> None:
    config_path = tmp_path / "runtime.toml"
    config_path.write_text(
        """
[rendering]
default_profile = "receipt42"

[delivery]
default_adapter = "stdout"

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
checklist_items = ["Walk"]
is_enabled = true
""".strip(),
        encoding="utf-8",
    )

    config = load_runtime_config(config_path)

    assert config.rendering.default_profile == "receipt42"
    assert config.delivery.default_adapter == "stdout"
    assert config.runtime.catchup_seconds == 60
    assert config.runtime.poll_interval_seconds == 30.0
    assert config.publication_slots[0].slot_id == "noon"
    assert config.publication_slots[0].publish_time.isoformat() == "12:00:00"
    assert config.scene_apps[0].app_id == "lunch"
    assert config.scene_apps[0].checklist_items == ("Walk",)


def test_load_runtime_config_raises_clear_error_for_missing_required_field(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "runtime.toml"
    config_path.write_text(
        """
[[publication_slots]]
name = "Noon"
publish_time = "12:00"
is_enabled = true
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(
        RuntimeConfigError,
        match=r"publication_slots\[1\]\.slot_id must be a non-empty string",
    ):
        load_runtime_config(config_path)


def test_compile_runtime_config_rejects_unsupported_profile(tmp_path: Path) -> None:
    config_path = tmp_path / "runtime.toml"
    config_path.write_text(
        """
[rendering]
default_profile = "receipt99"

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

    config = load_runtime_config(config_path)

    with pytest.raises(RuntimeConfigError, match="Unsupported render profile"):
        compile_runtime_config(config)


def test_load_runtime_config_rejects_blank_default_profile(tmp_path: Path) -> None:
    config_path = tmp_path / "runtime.toml"
    config_path.write_text(
        """
[rendering]
default_profile = ""

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

    with pytest.raises(
        RuntimeConfigError,
        match=r"rendering\.default_profile must be a non-empty string",
    ):
        load_runtime_config(config_path)


def test_load_runtime_config_rejects_blank_default_adapter(tmp_path: Path) -> None:
    config_path = tmp_path / "runtime.toml"
    config_path.write_text(
        """
[delivery]
default_adapter = ""

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

    with pytest.raises(
        RuntimeConfigError,
        match=r"delivery\.default_adapter must be a non-empty string",
    ):
        load_runtime_config(config_path)


def test_compile_runtime_config_rejects_non_daily_recurrence_rule(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "runtime.toml"
    config_path.write_text(
        """
[[publication_slots]]
slot_id = "noon"
name = "Noon"
publish_time = "12:00"
is_enabled = true
recurrence_rule = "weekly"

[[scene_apps]]
app_id = "lunch"
name = "Lunch"
target_publication_slot_id = "noon"
scene_note = "Eat vegetables"
is_enabled = true
""".strip(),
        encoding="utf-8",
    )

    config = load_runtime_config(config_path)

    with pytest.raises(RuntimeConfigError, match="Unsupported recurrence_rule"):
        compile_runtime_config(config)


def test_compile_runtime_config_requires_file_output_dir_for_file_adapter(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "runtime.toml"
    config_path.write_text(
        """
[delivery]
default_adapter = "file"

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

    config = load_runtime_config(config_path)

    with pytest.raises(
        RuntimeConfigError,
        match=r"delivery\.file\.output_dir is required when default_adapter is 'file'",
    ):
        compile_runtime_config(config)


def test_load_runtime_config_normalizes_blank_scene_note_when_checklist_exists(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "runtime.toml"
    config_path.write_text(
        """
[[publication_slots]]
slot_id = "noon"
name = "Noon"
publish_time = "12:00"
is_enabled = true

[[scene_apps]]
app_id = "reset"
name = "Reset"
target_publication_slot_id = "noon"
scene_note = ""
checklist_items = ["Drink water"]
is_enabled = true
""".strip(),
        encoding="utf-8",
    )

    config = load_runtime_config(config_path)

    assert config.scene_apps[0].scene_note is None
    assert config.scene_apps[0].checklist_items == ("Drink water",)


def test_load_runtime_config_rejects_scene_app_without_note_and_checklist(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "runtime.toml"
    config_path.write_text(
        """
[[publication_slots]]
slot_id = "noon"
name = "Noon"
publish_time = "12:00"
is_enabled = true

[[scene_apps]]
app_id = "empty"
name = "Empty"
target_publication_slot_id = "noon"
scene_note = ""
checklist_items = []
is_enabled = true
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(
        RuntimeConfigError,
        match=r"scene_apps\[1\] requires scene_note or checklist_items",
    ):
        load_runtime_config(config_path)
