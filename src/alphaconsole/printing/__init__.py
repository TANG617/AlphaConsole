from .adapter import PrinterAdapter
from .artifact import RenderedReceipt
from .bytes_file_adapter import EscPosBytesFileAdapter
from .calibration import build_calibration_receipt_text
from .diagnostics import (
    DeliveryDiagnostics,
    PrintResult,
    TargetHealthResult,
    build_delivery_diagnostics,
    build_failed_delivery_diagnostics,
)
from .escpos import EscPosPayload, build_escpos_payload, encode_raster_receipt_to_escpos
from .file_adapter import FilePrinterAdapter
from .memory_adapter import MemoryPrinterAdapter
from .profiles import (
    GENERIC_58MM,
    GENERIC_80MM,
    PrinterCapability,
    PrinterProfile,
    list_printer_profiles,
    resolve_printer_profile,
)
from .raster import RasterizedReceipt, rasterize_receipt
from .service import PrintService
from .socket_adapter import EscPosSocketPrinterAdapter
from .stdout_adapter import StdoutPrinterAdapter
from .test_page import build_test_receipt, build_test_receipt_text
from .targets import (
    HardwarePrintOptions,
    PrinterTargetInspection,
    PrinterTargetConfig,
    ResolvedPrinterTarget,
    inspect_printer_target,
    normalize_hardware_print_mode,
    normalize_printer_target_kind,
)

__all__ = [
    "RenderedReceipt",
    "PrinterAdapter",
    "PrinterProfile",
    "PrinterCapability",
    "GENERIC_58MM",
    "GENERIC_80MM",
    "DeliveryDiagnostics",
    "TargetHealthResult",
    "PrintResult",
    "PrinterTargetConfig",
    "PrinterTargetInspection",
    "ResolvedPrinterTarget",
    "HardwarePrintOptions",
    "RasterizedReceipt",
    "EscPosPayload",
    "MemoryPrinterAdapter",
    "FilePrinterAdapter",
    "StdoutPrinterAdapter",
    "EscPosSocketPrinterAdapter",
    "EscPosBytesFileAdapter",
    "PrintService",
    "build_test_receipt",
    "build_test_receipt_text",
    "build_calibration_receipt_text",
    "build_delivery_diagnostics",
    "build_failed_delivery_diagnostics",
    "rasterize_receipt",
    "encode_raster_receipt_to_escpos",
    "build_escpos_payload",
    "resolve_printer_profile",
    "list_printer_profiles",
    "inspect_printer_target",
    "normalize_printer_target_kind",
    "normalize_hardware_print_mode",
]
