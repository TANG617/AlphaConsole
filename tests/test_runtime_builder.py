from __future__ import annotations

from pathlib import Path

from alphaconsole.application import PublicationService
from alphaconsole.printing import FilePrinterAdapter
from alphaconsole.runtime import RuntimeBundle, build_runtime_from_config


def test_build_runtime_from_config_returns_runtime_bundle() -> None:
    config_path = Path("examples/basic.toml")

    bundle = build_runtime_from_config(config_path)

    assert isinstance(bundle, RuntimeBundle)
    assert isinstance(bundle.publication_service, PublicationService)
    assert "noon" in bundle.slots_by_id
    assert "lunch" in bundle.apps_by_id
    assert bundle.default_profile.name == "receipt_42"
    assert bundle.default_adapter_kind == "stdout"


def test_build_runtime_from_config_resolves_default_file_output_dir(
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
app_id = "lunch"
name = "Lunch"
target_publication_slot_id = "noon"
scene_note = "Eat vegetables"
is_enabled = true
""".strip(),
        encoding="utf-8",
    )

    bundle = build_runtime_from_config(config_path)
    adapter = bundle.adapter_factory.create(bundle.default_adapter_kind)

    assert isinstance(adapter, FilePrinterAdapter)
    assert adapter.output_dir == tmp_path / "receipts"
