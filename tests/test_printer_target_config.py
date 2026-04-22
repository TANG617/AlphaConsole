from __future__ import annotations

from pathlib import Path

import pytest

from alphaconsole.config import RuntimeConfigError, compile_runtime_config, load_runtime_config


BASE_CONFIG = """
[rendering]
default_profile = "receipt42"

[printing]
default_target = "receipt_printer"

[[printer_targets]]
target_id = "receipt_printer"
kind = "escpos_socket"
host = "127.0.0.1"
port = 9100
mode = "raster"
profile = "receipt42"
font_path = ""
font_size = 18
line_spacing = 4
cut = true

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
""".strip()


def test_compile_runtime_config_loads_printer_target() -> None:
    config = load_runtime_config(Path("examples/printer-network.toml"))
    compiled = compile_runtime_config(config)

    target = compiled.printer_targets_by_id["receipt_printer"]

    assert compiled.default_printer_target_id == "receipt_printer"
    assert target.kind == "escpos_socket"
    assert target.host == "127.0.0.1"
    assert target.port == 19100
    assert target.profile_name == "receipt_42"
    assert target.hardware_options.mode == "raster"


@pytest.mark.parametrize(
    ("field_name", "field_value", "error_pattern"),
    [
        ("target_id", '""', r"printer_targets\[1\]\.target_id must be a non-empty string"),
        ("kind", '""', r"printer_targets\[1\]\.kind must be a non-empty string"),
        ("mode", '""', r"printer_targets\[1\]\.mode must be a non-empty string"),
    ],
)
def test_load_runtime_config_rejects_blank_printer_target_strings(
    tmp_path: Path,
    field_name: str,
    field_value: str,
    error_pattern: str,
) -> None:
    current_values = {
        "target_id": 'target_id = "receipt_printer"',
        "kind": 'kind = "escpos_socket"',
        "mode": 'mode = "raster"',
    }
    config_path = tmp_path / "runtime.toml"
    config_path.write_text(
        BASE_CONFIG.replace(current_values[field_name], f"{field_name} = {field_value}"),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeConfigError, match=error_pattern):
        load_runtime_config(config_path)


def test_compile_runtime_config_rejects_missing_socket_host_or_port(
    tmp_path: Path,
) -> None:
    missing_host = tmp_path / "missing-host.toml"
    missing_host.write_text(BASE_CONFIG.replace('host = "127.0.0.1"\n', ""), encoding="utf-8")

    with pytest.raises(RuntimeConfigError, match="requires host for escpos_socket"):
        compile_runtime_config(load_runtime_config(missing_host))

    missing_port = tmp_path / "missing-port.toml"
    missing_port.write_text(BASE_CONFIG.replace("port = 9100\n", ""), encoding="utf-8")

    with pytest.raises(RuntimeConfigError, match="requires port for escpos_socket"):
        compile_runtime_config(load_runtime_config(missing_port))


def test_compile_runtime_config_rejects_missing_bytes_file_output_dir(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "runtime.toml"
    config_path.write_text(
        BASE_CONFIG.replace('kind = "escpos_socket"', 'kind = "escpos_bytes_file"')
        .replace('host = "127.0.0.1"\n', "")
        .replace("port = 9100\n", ""),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeConfigError, match="requires output_dir for escpos_bytes_file"):
        compile_runtime_config(load_runtime_config(config_path))


def test_compile_runtime_config_rejects_non_raster_mode(tmp_path: Path) -> None:
    config_path = tmp_path / "runtime.toml"
    config_path.write_text(BASE_CONFIG.replace('mode = "raster"', 'mode = "text"'), encoding="utf-8")

    with pytest.raises(RuntimeConfigError, match="Unsupported hardware print mode"):
        compile_runtime_config(load_runtime_config(config_path))


def test_compile_runtime_config_normalizes_blank_font_path_to_none(tmp_path: Path) -> None:
    config_path = tmp_path / "runtime.toml"
    config_path.write_text(
        BASE_CONFIG.replace('port = 9100', 'port = 9100\noutput_dir = "var/escpos"')
        .replace('kind = "escpos_socket"', 'kind = "escpos_bytes_file"')
        .replace('host = "127.0.0.1"\n', ""),
        encoding="utf-8",
    )

    compiled = compile_runtime_config(load_runtime_config(config_path))

    assert compiled.printer_targets_by_id["receipt_printer"].hardware_options.font_path is None
