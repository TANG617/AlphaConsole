from __future__ import annotations

import socket
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from escpos.printer import Network

from .config import Settings
from .layout import ReceiptScene, build_receipt_scene
from .models import EntryRecord
from .render import render_ascii, render_calibration_image, render_to_image


@dataclass(slots=True)
class PrinterPreview:
    scene: ReceiptScene
    ascii_preview: str
    preview_path: Path


class PrinterService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def check_connectivity(self) -> bool:
        try:
            with socket.create_connection(
                (self.settings.printer_host, self.settings.printer_port),
                timeout=self.settings.printer_timeout,
            ):
                return True
        except OSError:
            return False

    def build_preview(self, entry: EntryRecord) -> PrinterPreview:
        scene = build_receipt_scene(entry)
        ascii_preview = render_ascii(scene, width=self.settings.theme.preview_width_chars)
        timestamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
        output_path = (
            self.settings.preview_dir / f"entry-{entry.id}-{timestamp}.png"
        ).resolve()
        render_to_image(scene, self.settings, output_path)
        return PrinterPreview(
            scene=scene,
            ascii_preview=ascii_preview,
            preview_path=output_path,
        )

    def print_entry(self, entry: EntryRecord, dry_run: bool = False) -> Path:
        preview = self.build_preview(entry)
        preview_path = preview.preview_path
        if dry_run:
            return preview_path

        self._send_image(preview_path)
        return preview_path

    def print_calibration(self, dry_run: bool = False) -> Path:
        timestamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
        output_path = (
            self.settings.preview_dir / f"calibration-{timestamp}.png"
        ).resolve()
        render_calibration_image(self.settings, output_path)
        if dry_run:
            return output_path

        self._send_image(output_path)
        return output_path

    def _send_image(self, image_path: Path) -> None:
        printer = Network(
            host=self.settings.printer_host,
            port=self.settings.printer_port,
            timeout=self.settings.printer_timeout,
        )
        try:
            printer.image(str(image_path), center=False)
            printer.cut()
        finally:
            with suppress(Exception):
                printer.close()
