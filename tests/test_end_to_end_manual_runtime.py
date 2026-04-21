from __future__ import annotations

from pathlib import Path
from datetime import datetime

from alphaconsole.runtime import build_runtime_from_config


def test_manual_runtime_builds_from_example_config() -> None:
    bundle = build_runtime_from_config(Path("examples/basic.toml"))

    assert "morning" in bundle.slots_by_id
    assert "noon" in bundle.slots_by_id
    assert "lunch" in bundle.apps_by_id
    assert "afternoon_reset" in bundle.apps_by_id


def test_manual_runtime_runs_scheduled_publish_with_file_adapter(
    tmp_path: Path,
) -> None:
    bundle = build_runtime_from_config(Path("examples/basic.toml"))
    slot = bundle.slots_by_id["noon"]
    adapter = bundle.adapter_factory.create("file", output_dir=tmp_path)

    result = bundle.publication_service.publish_scheduled(
        slot=slot,
        apps=tuple(bundle.apps_by_id.values()),
        adapter=adapter,
        now=datetime(2026, 4, 21, 12, 0, 0),
        sequence_of_day=2,
        profile=bundle.default_profile,
    )

    written_files = list(tmp_path.glob("*.txt"))

    assert result.issue.publication_slot_id == "noon"
    assert "[Lunch]" in result.receipt.text
    assert "[Afternoon Reset]" in result.receipt.text
    assert len(written_files) == 1


def test_manual_runtime_runs_immediate_publish_with_stdout_adapter(capsys) -> None:
    bundle = build_runtime_from_config(Path("examples/basic.toml"))
    app = bundle.apps_by_id["lunch"]
    adapter = bundle.adapter_factory.create("stdout")

    result = bundle.publication_service.publish_immediate(
        app=app,
        adapter=adapter,
        now=datetime(2026, 4, 21, 12, 5, 0),
        sequence_of_day=3,
        profile=bundle.default_profile,
    )

    captured = capsys.readouterr()

    assert result.issue.trigger_mode.value == "immediate"
    assert result.issue.publication_slot_id is None
    assert "[Lunch]" in captured.out


def test_manual_runtime_supports_empty_issue_path_with_disabled_app(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "runtime.toml"
    config_path.write_text(
        """
[delivery]
default_adapter = "file"
output_dir = "receipts"

[[publication_slots]]
slot_id = "noon"
name = "Noon"
publish_time = "12:00"
is_enabled = true

[[scene_apps]]
app_id = "disabled_scene"
name = "Disabled Scene"
target_publication_slot_id = "noon"
scene_note = "This should be skipped"
is_enabled = false
""".strip(),
        encoding="utf-8",
    )

    bundle = build_runtime_from_config(config_path)
    slot = bundle.slots_by_id["noon"]
    adapter = bundle.adapter_factory.create(bundle.default_adapter_kind)

    result = bundle.publication_service.publish_scheduled(
        slot=slot,
        apps=tuple(bundle.apps_by_id.values()),
        adapter=adapter,
        now=datetime(2026, 4, 21, 12, 0, 0),
        sequence_of_day=4,
        profile=bundle.default_profile,
    )

    written_files = list((tmp_path / "receipts").glob("*.txt"))

    assert result.issue.blocks == ()
    assert "DATE: 2026-04-21" in result.receipt.text
    assert len(written_files) == 1
