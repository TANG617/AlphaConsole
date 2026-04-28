from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path
import sys

from alphaconsole.application import AutomationRuntimeService
from alphaconsole.config import RuntimeConfigError, resolve_render_profile
from alphaconsole.rendering import render_issue
from alphaconsole.runtime import RuntimeBundle, build_runtime_from_config
from alphaconsole.state import SQLiteStateStore


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
        return args.handler(args)
    except SystemExit as exc:
        return int(exc.code)
    except RuntimeConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="alphaconsole.cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list")
    _add_config_argument(list_parser)
    list_parser.set_defaults(handler=_handle_list)

    preview_parser = subparsers.add_parser("preview")
    preview_subparsers = preview_parser.add_subparsers(
        dest="preview_command", required=True
    )
    preview_scheduled = preview_subparsers.add_parser("scheduled")
    _add_config_argument(preview_scheduled)
    _add_runtime_arguments(preview_scheduled, include_adapter=False)
    preview_scheduled.add_argument("--slot-id", required=True)
    preview_scheduled.set_defaults(handler=_handle_preview_scheduled)

    publish_parser = subparsers.add_parser("publish")
    publish_subparsers = publish_parser.add_subparsers(
        dest="publish_command", required=True
    )

    publish_scheduled = publish_subparsers.add_parser("scheduled")
    _add_config_argument(publish_scheduled)
    _add_runtime_arguments(publish_scheduled, include_adapter=True)
    publish_scheduled.add_argument("--slot-id", required=True)
    publish_scheduled.set_defaults(handler=_handle_publish_scheduled)

    publish_immediate = publish_subparsers.add_parser("immediate")
    _add_config_argument(publish_immediate)
    _add_runtime_arguments(publish_immediate, include_adapter=True)
    publish_immediate.add_argument("--app-id", required=True)
    publish_immediate.set_defaults(handler=_handle_publish_immediate)

    runtime_parser = subparsers.add_parser("runtime")
    runtime_subparsers = runtime_parser.add_subparsers(
        dest="runtime_command", required=True
    )

    runtime_once = runtime_subparsers.add_parser("once")
    _add_config_argument(runtime_once)
    _add_state_argument(runtime_once)
    _add_runtime_override_arguments(runtime_once)
    runtime_once.add_argument("--catchup-seconds", type=int)
    runtime_once.add_argument("--now", type=_parse_datetime)
    runtime_once.set_defaults(handler=_handle_runtime_once)

    runtime_loop = runtime_subparsers.add_parser("loop")
    _add_config_argument(runtime_loop)
    _add_state_argument(runtime_loop)
    _add_runtime_override_arguments(runtime_loop)
    runtime_loop.add_argument("--catchup-seconds", type=int)
    runtime_loop.add_argument("--poll-interval", type=float)
    runtime_loop.add_argument("--iterations", type=int)
    runtime_loop.add_argument("--now", type=_parse_datetime)
    runtime_loop.set_defaults(handler=_handle_runtime_loop)

    runs_parser = subparsers.add_parser("runs")
    runs_subparsers = runs_parser.add_subparsers(dest="runs_command", required=True)

    runs_list = runs_subparsers.add_parser("list")
    _add_state_argument(runs_list)
    runs_list.add_argument("--limit", type=int, default=20)
    runs_list.set_defaults(handler=_handle_runs_list)

    runs_latest = runs_subparsers.add_parser("latest")
    _add_state_argument(runs_latest)
    runs_latest.set_defaults(handler=_handle_runs_latest)

    return parser


def _add_config_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", type=Path, required=True)


def _add_state_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--state", type=Path, required=True)


def _add_runtime_arguments(
    parser: argparse.ArgumentParser,
    *,
    include_adapter: bool,
) -> None:
    parser.add_argument("--profile")
    if include_adapter:
        parser.add_argument("--adapter")
        parser.add_argument("--output-dir", type=Path)
        _add_printer_arguments(parser)
    parser.add_argument("--now", type=_parse_datetime)
    parser.add_argument("--sequence-of-day", type=int, default=1)


def _add_runtime_override_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--profile")
    parser.add_argument("--adapter")
    parser.add_argument("--output-dir", type=Path)
    _add_printer_arguments(parser)


def _add_printer_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--printer-host")
    parser.add_argument("--printer-port", type=int)
    parser.add_argument("--printer-timeout", type=float)
    parser.add_argument("--printer-encoding")
    parser.add_argument("--printer-feed-lines", type=int)
    parser.add_argument(
        "--no-cut",
        dest="printer_cut",
        action="store_false",
        default=None,
    )


def _handle_list(args: argparse.Namespace) -> int:
    bundle = build_runtime_from_config(args.config)

    print("slots:")
    for slot in bundle.slots_by_id.values():
        status = "enabled" if slot.is_enabled else "disabled"
        print(
            f"- {slot.slot_id}: {slot.name} @ {slot.publish_time.strftime('%H:%M')} ({status})"
        )

    print("apps:")
    for app in bundle.apps_by_id.values():
        status = "enabled" if app.is_enabled else "disabled"
        print(f"- {app.app_id}: {app.name} -> {app.target_publication_slot_id} ({status})")

    return 0


def _handle_preview_scheduled(args: argparse.Namespace) -> int:
    bundle = build_runtime_from_config(args.config)
    slot = _require_slot(bundle, args.slot_id)
    profile = _resolve_profile(bundle, args.profile)
    issue = bundle.issue_assembler.assemble_scheduled_issue(
        slot=slot,
        apps=tuple(bundle.apps_by_id.values()),
        now=_resolve_now(args.now),
        sequence_of_day=args.sequence_of_day,
    )
    print(render_issue(issue, profile))
    return 0


def _handle_publish_scheduled(args: argparse.Namespace) -> int:
    bundle = build_runtime_from_config(args.config)
    slot = _require_slot(bundle, args.slot_id)
    profile = _resolve_profile(bundle, args.profile)
    adapter = _resolve_adapter_from_args(bundle, args)
    bundle.publication_service.publish_scheduled(
        slot=slot,
        apps=tuple(bundle.apps_by_id.values()),
        adapter=adapter,
        now=_resolve_now(args.now),
        sequence_of_day=args.sequence_of_day,
        profile=profile,
    )
    return 0


def _handle_publish_immediate(args: argparse.Namespace) -> int:
    bundle = build_runtime_from_config(args.config)
    app = _require_app(bundle, args.app_id)
    profile = _resolve_profile(bundle, args.profile)
    adapter = _resolve_adapter_from_args(bundle, args)
    bundle.publication_service.publish_immediate(
        app=app,
        adapter=adapter,
        now=_resolve_now(args.now),
        sequence_of_day=args.sequence_of_day,
        profile=profile,
    )
    return 0


def _handle_runtime_once(args: argparse.Namespace) -> int:
    bundle = build_runtime_from_config(args.config)
    service = _build_automation_runtime_service(bundle)
    adapter = _resolve_adapter_from_args(bundle, args)
    store = _open_state_store(args.state)
    result = service.run_once(
        slots=tuple(bundle.slots_by_id.values()),
        apps=tuple(bundle.apps_by_id.values()),
        adapter=adapter,
        store=store,
        now=_resolve_now(args.now),
        profile=_resolve_profile(bundle, args.profile),
        catchup_seconds=_resolve_catchup_seconds(bundle, args.catchup_seconds),
    )
    _print_runtime_tick_summary(result)
    return 0


def _handle_runtime_loop(args: argparse.Namespace) -> int:
    bundle = build_runtime_from_config(args.config)
    service = _build_automation_runtime_service(bundle)
    adapter = _resolve_adapter_from_args(bundle, args)
    store = _open_state_store(args.state)
    poll_interval = _resolve_poll_interval_seconds(bundle, args.poll_interval)
    service.run_loop(
        slots=tuple(bundle.slots_by_id.values()),
        apps=tuple(bundle.apps_by_id.values()),
        adapter=adapter,
        store=store,
        profile=_resolve_profile(bundle, args.profile),
        poll_interval_seconds=poll_interval,
        catchup_seconds=_resolve_catchup_seconds(bundle, args.catchup_seconds),
        iterations=args.iterations,
        now_fn=_build_now_fn(args.now, poll_interval),
    )
    if args.iterations is not None:
        print(f"runtime loop completed: {args.iterations} iterations")
    return 0


def _handle_runs_list(args: argparse.Namespace) -> int:
    store = _open_state_store(args.state)
    runs = store.list_publication_runs(limit=args.limit)
    if not runs:
        print("No publication runs found.")
        return 0

    for run in runs:
        print(_format_run(run))
    return 0


def _handle_runs_latest(args: argparse.Namespace) -> int:
    store = _open_state_store(args.state)
    latest = store.get_latest_publication_run()
    if latest is None:
        print("No publication runs found.")
        return 0

    print(_format_run(latest))
    return 0


def _resolve_profile(bundle: RuntimeBundle, override: str | None):
    if override is None:
        return bundle.default_profile
    return resolve_render_profile(override)


def _resolve_adapter(
    bundle: RuntimeBundle,
    override_kind: str | None,
    output_dir: Path | None,
    *,
    printer_host: str | None = None,
    printer_port: int | None = None,
    printer_timeout_seconds: float | None = None,
    printer_encoding: str | None = None,
    printer_cut: bool | None = None,
    printer_feed_lines: int | None = None,
):
    kind = override_kind or bundle.default_adapter_kind
    return bundle.adapter_factory.create(
        kind,
        output_dir=output_dir,
        printer_host=printer_host,
        printer_port=printer_port,
        printer_timeout_seconds=printer_timeout_seconds,
        printer_encoding=printer_encoding,
        printer_cut=printer_cut,
        printer_feed_lines=printer_feed_lines,
    )


def _resolve_adapter_from_args(bundle: RuntimeBundle, args: argparse.Namespace):
    return _resolve_adapter(
        bundle,
        args.adapter,
        args.output_dir,
        printer_host=args.printer_host,
        printer_port=args.printer_port,
        printer_timeout_seconds=args.printer_timeout,
        printer_encoding=args.printer_encoding,
        printer_cut=args.printer_cut,
        printer_feed_lines=args.printer_feed_lines,
    )


def _resolve_catchup_seconds(bundle: RuntimeBundle, override: int | None) -> int:
    if override is None:
        return bundle.runtime_catchup_seconds
    return override


def _resolve_poll_interval_seconds(
    bundle: RuntimeBundle,
    override: float | None,
) -> float:
    if override is None:
        return bundle.runtime_poll_interval_seconds
    return override


def _require_slot(bundle: RuntimeBundle, slot_id: str):
    try:
        return bundle.slots_by_id[slot_id]
    except KeyError as exc:
        raise RuntimeConfigError(f"Unknown slot_id: {slot_id!r}.") from exc


def _require_app(bundle: RuntimeBundle, app_id: str):
    try:
        return bundle.apps_by_id[app_id]
    except KeyError as exc:
        raise RuntimeConfigError(f"Unknown app_id: {app_id!r}.") from exc


def _parse_datetime(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid ISO datetime value: {value!r}."
        ) from exc


def _resolve_now(value: datetime | None) -> datetime:
    return value or datetime.now()


def _build_automation_runtime_service(
    bundle: RuntimeBundle,
) -> AutomationRuntimeService:
    return AutomationRuntimeService(
        assembler=bundle.issue_assembler,
        print_service=bundle.print_service,
    )


def _open_state_store(path: Path) -> SQLiteStateStore:
    store = SQLiteStateStore(path)
    store.init_schema()
    return store


def _build_now_fn(base_now: datetime | None, poll_interval_seconds: float):
    if base_now is None:
        return datetime.now

    iteration = 0

    def _now_fn() -> datetime:
        nonlocal iteration
        current = base_now + timedelta(seconds=poll_interval_seconds * iteration)
        iteration += 1
        return current

    return _now_fn


def _print_runtime_tick_summary(result) -> None:
    print(f"due: {len(result.due_occurrences)}")
    print(f"published: {len(result.published_issue_ids)}")
    print(f"skipped_existing: {len(result.skipped_existing_occurrences)}")


def _format_run(run) -> str:
    occurrence_at = run.occurrence_at.isoformat() if run.occurrence_at else "-"
    delivered_at = run.delivered_at.isoformat() if run.delivered_at else "-"
    slot_id = run.slot_id or "-"
    return (
        f"{run.issue_id} slot={slot_id} occurrence_at={occurrence_at} "
        f"status={run.status} seq={run.sequence_of_day} "
        f"adapter={run.adapter_name} delivered_at={delivered_at}"
    )


if __name__ == "__main__":
    raise SystemExit(main())
