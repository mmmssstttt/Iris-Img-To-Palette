from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from core.colors.color_oklch import _linear_rgb_to_oklab, _srgb_channel_to_linear


def _rgb255_to_oklab(rgb: np.ndarray) -> np.ndarray:
    rgb_unit = np.clip(rgb.astype(np.float64) / 255.0, 0.0, 1.0)
    out = np.empty_like(rgb_unit, dtype=np.float64)
    for i, (r, g, b) in enumerate(rgb_unit):
        lr = _srgb_channel_to_linear(float(r))
        lg = _srgb_channel_to_linear(float(g))
        lb = _srgb_channel_to_linear(float(b))
        out[i] = _linear_rgb_to_oklab(lr, lg, lb)
    return out


def _pack_color_record(rank: int, rgb: np.ndarray, area_ratio: float) -> dict:
    oklab = _rgb255_to_oklab(rgb.reshape(1, 3))[0]
    L, a, b = float(oklab[0]), float(oklab[1]), float(oklab[2])
    return {
        "rank": int(rank),
        "area_ratio": round(float(area_ratio), 3),
        "score": round(float(area_ratio), 3),
        "oklab": {"L": round(L, 3), "a": round(a, 3), "b": round(b, 3)},
    }


def extract_top10_area_ratio_oklab(
    image_path: str | Path,
    k: int = 10,
    bins_per_channel: int = 32,
) -> dict:
    img_bgr = cv2.imread(str(image_path))
    if img_bgr is None:
        raise ValueError(f"Unable to read image: {image_path}")

    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    pixels = img_rgb.reshape(-1, 3).astype(np.int32)
    total = pixels.shape[0]

    step = max(1, int(np.ceil(256 / bins_per_channel)))
    q = np.clip(pixels // step, 0, bins_per_channel - 1)
    keys = q[:, 0] * bins_per_channel * bins_per_channel + q[:, 1] * bins_per_channel + q[:, 2]

    uniq, inv, counts = np.unique(keys, return_inverse=True, return_counts=True)
    sum_r = np.bincount(inv, weights=pixels[:, 0], minlength=len(uniq))
    sum_g = np.bincount(inv, weights=pixels[:, 1], minlength=len(uniq))
    sum_b = np.bincount(inv, weights=pixels[:, 2], minlength=len(uniq))

    means = np.stack([sum_r / counts, sum_g / counts, sum_b / counts], axis=1)
    means = np.clip(np.rint(means), 0, 255).astype(np.int32)

    sort_idx = np.argsort(-counts)[:k]
    top_counts = counts[sort_idx].astype(np.float64)
    top_ratio = top_counts / float(total)
    top_rgb = means[sort_idx]

    top_colors = [
        _pack_color_record(rank=i + 1, rgb=top_rgb[i], area_ratio=float(top_ratio[i]))
        for i in range(len(sort_idx))
    ]

    return {
        "dimension": "physical_area_ratio",
        "description": "Single-color pixel area ratio in the image.",
        "top_colors": top_colors,
    }
