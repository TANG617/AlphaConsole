from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


_FONT_CANDIDATES = (
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/PingFang.ttc",
)

_MONO_FONT_CANDIDATES = (
    "/System/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/SFNSMono.ttf",
    "/System/Library/Fonts/Monaco.ttf",
    "/System/Library/Fonts/Courier.ttc",
)


@dataclass(slots=True)
class ThemeSettings:
    name: str
    page_margin_px: int
    section_gap_px: int
    panel_padding_px: int
    preview_width_chars: int
    header_font_size: int
    title_font_size: int
    subtitle_font_size: int
    emblem_font_size: int
    label_font_size: int
    meta_font_size: int
    meta_line_height: int
    body_font_size: int
    body_line_height: int
    footer_font_size: int
    footer_line_height: int


@dataclass(slots=True)
class Settings:
    project_root: Path
    config_path: Path
    data_dir: Path
    db_path: Path
    preview_dir: Path
    printer_host: str
    printer_port: int
    printer_width: int
    printer_timeout: float
    font_path: Path
    mono_font_path: Path
    theme: ThemeSettings
    timezone_name: str

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.preview_dir.mkdir(parents=True, exist_ok=True)


def _detect_font() -> Path:
    for candidate in _FONT_CANDIDATES:
        path = Path(candidate)
        if path.exists():
            return path
    raise FileNotFoundError(
        "No usable CJK font found. Set ALPHA_CONSOLE_FONT_PATH to a .ttf/.ttc file."
    )


def _detect_mono_font() -> Path:
    for candidate in _MONO_FONT_CANDIDATES:
        path = Path(candidate)
        if path.exists():
            return path
    return _detect_font()


def _load_project_config(root: Path) -> tuple[Path, dict]:
    config_path = (root / "alpha_console.toml").resolve()
    if not config_path.exists():
        return config_path, {}
    with config_path.open("rb") as handle:
        data = tomllib.load(handle)
    return config_path, data if isinstance(data, dict) else {}


def _resolve_path(raw: str | Path, root: Path) -> Path:
    path = Path(raw)
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def _load_theme(theme_config: dict) -> ThemeSettings:
    return ThemeSettings(
        name=str(theme_config.get("name", "retro-terminal")),
        page_margin_px=int(theme_config.get("page_margin_px", 16)),
        section_gap_px=int(theme_config.get("section_gap_px", 10)),
        panel_padding_px=int(theme_config.get("panel_padding_px", 12)),
        preview_width_chars=int(theme_config.get("preview_width_chars", 40)),
        header_font_size=int(theme_config.get("header_font_size", 16)),
        title_font_size=int(theme_config.get("title_font_size", 28)),
        subtitle_font_size=int(theme_config.get("subtitle_font_size", 20)),
        emblem_font_size=int(theme_config.get("emblem_font_size", 18)),
        label_font_size=int(theme_config.get("label_font_size", 16)),
        meta_font_size=int(theme_config.get("meta_font_size", 18)),
        meta_line_height=int(theme_config.get("meta_line_height", 24)),
        body_font_size=int(theme_config.get("body_font_size", 30)),
        body_line_height=int(theme_config.get("body_line_height", 36)),
        footer_font_size=int(theme_config.get("footer_font_size", 18)),
        footer_line_height=int(theme_config.get("footer_line_height", 24)),
    )


def load_settings(project_root: Path | None = None) -> Settings:
    root = project_root.resolve() if project_root else Path.cwd().resolve()
    config_path, config_data = _load_project_config(root)
    runtime_config = config_data.get("runtime", {})
    printer_config = config_data.get("printer", {})
    theme_config = config_data.get("theme", {})

    data_dir_value = os.environ.get("ALPHA_CONSOLE_DATA_DIR") or runtime_config.get(
        "data_dir", "var"
    )
    data_dir = _resolve_path(data_dir_value, root)
    preview_dir = data_dir / "previews"
    db_path_value = os.environ.get("ALPHA_CONSOLE_DB_PATH") or runtime_config.get(
        "db_path", data_dir / "alpha_console.db"
    )
    db_path = _resolve_path(db_path_value, root)
    printer_host = os.environ.get("ALPHA_CONSOLE_PRINTER_HOST") or printer_config.get(
        "host", "10.0.4.192"
    )
    printer_port = int(
        os.environ.get("ALPHA_CONSOLE_PRINTER_PORT")
        or printer_config.get("port", 9100)
    )
    printer_width = int(
        os.environ.get("ALPHA_CONSOLE_PRINTER_WIDTH")
        or printer_config.get("effective_width_px", 576)
    )
    printer_timeout = float(
        os.environ.get("ALPHA_CONSOLE_PRINTER_TIMEOUT")
        or printer_config.get("timeout_seconds", 10)
    )
    font_override = os.environ.get("ALPHA_CONSOLE_FONT_PATH") or printer_config.get(
        "font_path"
    )
    font_path = _resolve_path(font_override, root) if font_override else _detect_font()
    mono_font_override = os.environ.get("ALPHA_CONSOLE_MONO_FONT_PATH") or printer_config.get(
        "mono_font_path"
    )
    mono_font_path = (
        _resolve_path(mono_font_override, root)
        if mono_font_override
        else _detect_mono_font()
    )
    theme = _load_theme(theme_config)
    timezone_name = datetime.now().astimezone().tzname() or "local"
    return Settings(
        project_root=root,
        config_path=config_path,
        data_dir=data_dir,
        db_path=db_path,
        preview_dir=preview_dir,
        printer_host=printer_host,
        printer_port=printer_port,
        printer_width=printer_width,
        printer_timeout=printer_timeout,
        font_path=font_path,
        mono_font_path=mono_font_path,
        theme=theme,
        timezone_name=timezone_name,
    )
