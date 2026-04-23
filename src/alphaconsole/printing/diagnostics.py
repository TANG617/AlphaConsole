from __future__ import annotations

from dataclasses import dataclass

from .artifact import RenderedReceipt


@dataclass(slots=True, frozen=True)
class DeliveryDiagnostics:
    adapter_name: str
    target_id: str | None
    printer_profile_name: str | None
    render_profile_name: str | None
    transport: str
    bytes_length: int | None
    duration_ms: int | None
    succeeded: bool
    error_text: str | None


@dataclass(slots=True, frozen=True)
class TargetHealthResult:
    target_id: str
    ok: bool
    latency_ms: int | None
    error_text: str | None


@dataclass(slots=True, frozen=True)
class PrintResult:
    receipt: RenderedReceipt
    diagnostics: DeliveryDiagnostics


def build_delivery_diagnostics(
    *,
    adapter_name: str,
    target_id: str | None,
    printer_profile_name: str | None,
    render_profile_name: str | None,
    transport: str,
    bytes_length: int | None,
    duration_ms: int | None,
    succeeded: bool,
    error_text: str | None,
) -> DeliveryDiagnostics:
    return DeliveryDiagnostics(
        adapter_name=adapter_name,
        target_id=target_id,
        printer_profile_name=printer_profile_name,
        render_profile_name=render_profile_name,
        transport=transport,
        bytes_length=bytes_length,
        duration_ms=duration_ms,
        succeeded=succeeded,
        error_text=error_text,
    )


def build_failed_delivery_diagnostics(
    adapter,
    receipt: RenderedReceipt,
    *,
    error_text: str,
    duration_ms: int | None = None,
    bytes_length: int | None = None,
) -> DeliveryDiagnostics:
    return build_delivery_diagnostics(
        adapter_name=getattr(adapter, "name", adapter.__class__.__name__),
        target_id=getattr(adapter, "target_id", None),
        printer_profile_name=getattr(adapter, "printer_profile_name", None),
        render_profile_name=(
            getattr(adapter, "render_profile_name", None) or receipt.profile_name
        ),
        transport=getattr(adapter, "transport", getattr(adapter, "name", "unknown")),
        bytes_length=bytes_length,
        duration_ms=duration_ms,
        succeeded=False,
        error_text=error_text,
    )
