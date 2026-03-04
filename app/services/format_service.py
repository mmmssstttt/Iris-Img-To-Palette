import json
from pathlib import Path
from typing import Any

from ..storage import PaletteResult


def to_upload_url(image_path: str) -> str:
    return f"/uploads/{Path(image_path).name}"


def _palette_json_pretty(palette: list[dict[str, Any]]) -> str:
    return json.dumps(palette, ensure_ascii=False, indent=2)


def _palette_to_oklch_triplets(palette: list[dict[str, Any]]) -> list[list[float]]:
    out: list[list[float]] = []
    for color in palette:
        oklch = color.get("oklch") or {}
        out.append(
            [
                round(float(oklch.get("L", 0.0)), 3),
                round(float(oklch.get("c", 0.0)), 3),
                round(float(oklch.get("h", 0.0)), 3),
            ]
        )
    return out


def build_copy_json_pretty(palettes: list[list[list[float]]]) -> str:
    indent1 = "  "
    indent2 = "    "
    lines: list[str] = ["{", f'{indent1}"palettes": [']
    for idx, palette in enumerate(palettes):
        encoded = json.dumps(palette, ensure_ascii=False, separators=(",", ":"))
        suffix = "," if idx < len(palettes) - 1 else ""
        lines.append(f"{indent2}{encoded}{suffix}")
    lines.extend([f"{indent1}]", "}"])
    return "\n".join(lines)


def format_result_for_template(result: PaletteResult) -> dict[str, Any]:
    return {
        "id": result.id,
        "filename": result.filename,
        "n_colors": result.n_colors,
        "created_at": result.created_at,
        "palette": result.palette,
        "palette_json_pretty": _palette_json_pretty(result.palette),
        "image_url": to_upload_url(result.image_path),
    }


def palettes_response_payload(palettes_raw: list[list[dict[str, Any]]], n_colors: int) -> dict[str, Any]:
    palettes_oklch = [_palette_to_oklch_triplets(item) for item in palettes_raw]
    return {
        "n_colors": n_colors,
        "palette": palettes_raw[0] if palettes_raw else [],
        "palettes": palettes_raw,
        "palettes_json": json.dumps(palettes_raw, ensure_ascii=False, separators=(",", ":")),
        "palette_json_pretty": build_copy_json_pretty(palettes_oklch),
        "total_images": len(palettes_raw),
    }

