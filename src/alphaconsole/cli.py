from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import sys

from alphaconsole.config import RuntimeConfigError, resolve_render_profile
from alphaconsole.rendering import render_issue
from alphaconsole.runtime import RuntimeBundle, build_runtime_from_config


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

    return parser


def _add_config_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", type=Path, required=True)


def _add_runtime_arguments(
    parser: argparse.ArgumentParser,
    *,
    include_adapter: bool,
) -> None:
    parser.add_argument("--profile")
    if include_adapter:
        parser.add_argument("--adapter")
        parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--now", type=_parse_datetime)
    parser.add_argument("--sequence-of-day", type=int, default=1)


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
    adapter = _resolve_adapter(bundle, args.adapter, args.output_dir)
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
    adapter = _resolve_adapter(bundle, args.adapter, args.output_dir)
    bundle.publication_service.publish_immediate(
        app=app,
        adapter=adapter,
        now=_resolve_now(args.now),
        sequence_of_day=args.sequence_of_day,
        profile=profile,
    )
    return 0


def _resolve_profile(bundle: RuntimeBundle, override: str | None):
    if override is None:
        return bundle.default_profile
    return resolve_render_profile(override)


def _resolve_adapter(
    bundle: RuntimeBundle,
    override_kind: str | None,
    output_dir: Path | None,
):
    kind = override_kind or bundle.default_adapter_kind
    return bundle.adapter_factory.create(kind, output_dir=output_dir)


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


if __name__ == "__main__":
    raise SystemExit(main())
