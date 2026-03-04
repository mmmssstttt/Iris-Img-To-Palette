"""Backward-compatible re-exports for palette services."""

from .services.format_service import build_copy_json_pretty, format_result_for_template, to_upload_url
from .services.palette_service import (
    clamp_n_colors,
    clear_history_records,
    extract_batch_palettes,
    load_history,
    load_result,
)

__all__ = [
    "build_copy_json_pretty",
    "format_result_for_template",
    "to_upload_url",
    "clamp_n_colors",
    "clear_history_records",
    "extract_batch_palettes",
    "load_history",
    "load_result",
]

