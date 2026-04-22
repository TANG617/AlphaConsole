from __future__ import annotations

from datetime import datetime
from pathlib import Path

from alphaconsole.application import AutomationRuntimeService
from alphaconsole.runtime import build_runtime_from_config
from alphaconsole.state import SQLiteStateStore


def test_end_to_end_automated_runtime_dedupes_across_restarts(
    tmp_path: Path,
) -> None:
    bundle = build_runtime_from_config(Path("examples/basic.toml"))
    service = AutomationRuntimeService(
        assembler=bundle.issue_assembler,
        print_service=bundle.print_service,
    )
    state_path = tmp_path / "state.db"
    output_dir = tmp_path / "out"
    store = SQLiteStateStore(state_path)
    adapter = bundle.adapter_factory.create("file", output_dir=output_dir)

    first_result = service.run_once(
        slots=tuple(bundle.slots_by_id.values()),
        apps=tuple(bundle.apps_by_id.values()),
        adapter=adapter,
        store=store,
        now=datetime(2026, 4, 22, 12, 0, 0),
        profile=bundle.default_profile,
        catchup_seconds=bundle.runtime_catchup_seconds,
    )

    assert len(first_result.published_issue_ids) == 1
    assert len(list(output_dir.glob("*.txt"))) == 1

    restarted_bundle = build_runtime_from_config(Path("examples/basic.toml"))
    restarted_service = AutomationRuntimeService(
        assembler=restarted_bundle.issue_assembler,
        print_service=restarted_bundle.print_service,
    )
    restarted_store = SQLiteStateStore(state_path)
    restarted_store.set_last_tick_at(datetime(2026, 4, 22, 11, 59, 0))
    second_result = restarted_service.run_once(
        slots=tuple(restarted_bundle.slots_by_id.values()),
        apps=tuple(restarted_bundle.apps_by_id.values()),
        adapter=restarted_bundle.adapter_factory.create("file", output_dir=output_dir),
        store=restarted_store,
        now=datetime(2026, 4, 22, 12, 0, 30),
        profile=restarted_bundle.default_profile,
        catchup_seconds=restarted_bundle.runtime_catchup_seconds,
    )

    assert second_result.published_issue_ids == ()
    assert len(second_result.skipped_existing_occurrences) == 1
    assert len(list(output_dir.glob("*.txt"))) == 1


def test_end_to_end_automated_runtime_uses_example_config_with_stdout(
    capsys,
    tmp_path: Path,
) -> None:
    bundle = build_runtime_from_config(Path("examples/basic.toml"))
    service = AutomationRuntimeService(
        assembler=bundle.issue_assembler,
        print_service=bundle.print_service,
    )
    store = SQLiteStateStore(tmp_path / "state.db")

    result = service.run_once(
        slots=tuple(bundle.slots_by_id.values()),
        apps=tuple(bundle.apps_by_id.values()),
        adapter=bundle.adapter_factory.create("stdout"),
        store=store,
        now=datetime(2026, 4, 22, 12, 0, 0),
        profile=bundle.default_profile,
        catchup_seconds=bundle.runtime_catchup_seconds,
    )
    captured = capsys.readouterr()

    assert len(result.published_issue_ids) == 1
    assert "[Lunch]" in captured.out
