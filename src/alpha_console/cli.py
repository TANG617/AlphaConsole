from __future__ import annotations

import time
from datetime import timedelta

import typer

from .config import load_settings
from .service import ConsoleService
from .timeutil import format_local, now_local, parse_user_datetime

app = typer.Typer(
    help="Local-first planner and checklist printer MVP.",
    no_args_is_help=True,
    add_completion=False,
)


def _service() -> ConsoleService:
    return ConsoleService(load_settings())


@app.command()
def init() -> None:
    """Initialize local storage."""
    service = _service()
    try:
        typer.echo(f"Database ready at {service.settings.db_path}")
        typer.echo(f"Preview directory: {service.settings.preview_dir}")
    finally:
        service.close()


@app.command()
def doctor() -> None:
    """Check local runtime directories and printer reachability."""
    service = _service()
    try:
        printer_status = (
            "reachable" if service.printer.check_connectivity() else "unreachable"
        )
        typer.echo(f"Config: {service.settings.config_path}")
        typer.echo(f"DB: {service.settings.db_path}")
        typer.echo(f"Preview dir: {service.settings.preview_dir}")
        typer.echo(
            f"Printer: {service.settings.printer_host}:{service.settings.printer_port} ({printer_status})"
        )
        typer.echo(f"Effective width: {service.settings.printer_width}px")
        typer.echo(f"Font: {service.settings.font_path}")
        typer.echo(f"Mono font: {service.settings.mono_font_path}")
        typer.echo(f"Theme: {service.settings.theme.name}")
    finally:
        service.close()


@app.command("add-event")
def add_event(
    title: str = typer.Option(..., "--title", "-t", help="Reminder title."),
    due_at: str = typer.Option(
        ...,
        "--due-at",
        "-d",
        help="When to trigger. Example: '2026-04-18 18:20' or ISO 8601.",
    ),
    notes: str = typer.Option("", "--notes", "-n", help="Optional notes."),
) -> None:
    """Create a single reminder entry."""
    service = _service()
    try:
        entry = service.create_event(
            title=title,
            due_at=parse_user_datetime(due_at),
            notes=notes,
        )
        typer.echo(f"Created event #{entry.id} at {format_local(entry.due_at)}")
    finally:
        service.close()


@app.command("add-checklist")
def add_checklist(
    title: str = typer.Option(..., "--title", "-t", help="Checklist title."),
    due_at: str = typer.Option(..., "--due-at", "-d", help="When to print the checklist."),
    item: list[str] = typer.Option(
        ...,
        "--item",
        "-i",
        help="Checklist item. Repeat the flag for multiple items.",
    ),
    notes: str = typer.Option("", "--notes", "-n", help="Optional notes."),
) -> None:
    """Create a checklist reminder."""
    service = _service()
    try:
        entry = service.create_checklist(
            title=title,
            due_at=parse_user_datetime(due_at),
            items=item,
            notes=notes,
        )
        typer.echo(
            f"Created checklist #{entry.id} with {len(entry.items)} items at {format_local(entry.due_at)}"
        )
    finally:
        service.close()


@app.command()
def demo(
    delay_seconds: int = typer.Option(
        30,
        "--delay-seconds",
        "-s",
        min=5,
        help="How long from now to enqueue the sample checklist.",
    )
) -> None:
    """Create a sample checklist for end-to-end testing."""
    service = _service()
    try:
        due_at = now_local() + timedelta(seconds=delay_seconds)
        entry = service.create_checklist(
            title="出门前检查",
            due_at=due_at,
            items=["钥匙", "耳机", "水杯", "雨伞"],
            notes="本地 MVP 演示任务",
        )
        typer.echo(f"Created demo checklist #{entry.id} for {format_local(entry.due_at)}")
    finally:
        service.close()


@app.command("list")
def list_entries(
    limit: int = typer.Option(20, "--limit", "-l", min=1, max=200, help="Number of rows."),
) -> None:
    """List upcoming and historical entries."""
    service = _service()
    try:
        entries = service.list_entries(limit=limit)
        if not entries:
            typer.echo("No entries yet.")
            return
        typer.echo("ID  KIND       STATUS      DUE                      TITLE")
        typer.echo("--  ---------  ----------  -----------------------  ------------------------------")
        for entry in entries:
            kind = entry.kind.value.ljust(9)
            status = entry.status.value.ljust(10)
            due = entry.due_at.astimezone().strftime("%Y-%m-%d %H:%M:%S")
            typer.echo(f"{str(entry.id).ljust(2)}  {kind}  {status}  {due}  {entry.title}")
    finally:
        service.close()


@app.command()
def preview(
    entry_id: int = typer.Argument(..., help="Entry ID."),
) -> None:
    """Render a text preview and save the printer image locally."""
    service = _service()
    try:
        preview = service.preview_entry(entry_id)
        typer.echo(preview.ascii_preview)
        typer.echo("")
        typer.echo(f"Image preview: {preview.preview_path}")
    finally:
        service.close()


@app.command("print-now")
def print_now(
    entry_id: int = typer.Argument(..., help="Entry ID."),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Render and save the preview, but do not send it to the printer.",
    ),
) -> None:
    """Print a specific entry immediately."""
    service = _service()
    try:
        preview_path = service.print_entry_now(entry_id, dry_run=dry_run)
        mode = "Rendered" if dry_run else "Printed"
        typer.echo(f"{mode} entry #{entry_id}: {preview_path}")
    finally:
        service.close()


@app.command("calibrate-print")
def calibrate_print(
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Render and save the calibration image, but do not send it to the printer.",
    ),
) -> None:
    """Print a dedicated calibration ticket for paper width tuning."""
    service = _service()
    try:
        preview_path = service.printer.print_calibration(dry_run=dry_run)
        mode = "Rendered" if dry_run else "Printed"
        typer.echo(f"{mode} calibration ticket: {preview_path}")
    finally:
        service.close()


@app.command()
def worker(
    poll_interval: float = typer.Option(
        1.0,
        "--poll-interval",
        "-p",
        min=0.2,
        help="How often to poll the database for due jobs.",
    ),
    once: bool = typer.Option(
        False,
        "--once",
        help="Process due jobs once and exit.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Mark jobs done after rendering, but do not send to the printer.",
    ),
) -> None:
    """Run the local reminder worker."""
    service = _service()
    try:
        typer.echo(
            f"Worker watching {service.settings.db_path} and printer {service.settings.printer_host}:{service.settings.printer_port}"
        )
        while True:
            processed = service.process_due_entries(dry_run=dry_run)
            for result in processed:
                typer.echo(
                    f"[{result.status}] #{result.entry_id} {result.title} -> {result.detail}"
                )
            if once:
                break
            time.sleep(poll_interval)
    finally:
        service.close()


@app.command()
def tui() -> None:
    """Open the Textual dashboard."""
    from .tui import ConsoleTUI

    service = _service()
    app_instance = ConsoleTUI(service)
    try:
        app_instance.run()
    finally:
        service.close()
