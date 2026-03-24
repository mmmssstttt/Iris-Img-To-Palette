from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from sklearn.cluster import KMeans

from core.colors.color_oklch import _linear_rgb_to_oklab, _srgb_channel_to_linear


def _rgb255_to_oklab(rgb_pixels: np.ndarray) -> np.ndarray:
    rgb_unit = np.clip(rgb_pixels.astype(np.float64) / 255.0, 0.0, 1.0)
    out = np.empty_like(rgb_unit, dtype=np.float64)
    for i, (r, g, b) in enumerate(rgb_unit):
        lr = _srgb_channel_to_linear(float(r))
        lg = _srgb_channel_to_linear(float(g))
        lb = _srgb_channel_to_linear(float(b))
        out[i] = _linear_rgb_to_oklab(lr, lg, lb)
    return out


def _center_to_record(rank: int, center: np.ndarray, ratio: float) -> dict:
    L, a, b = float(center[0]), float(center[1]), float(center[2])
    return {
        "rank": int(rank),
        "area_ratio": round(float(ratio), 3),
        "score": round(float(ratio), 3),
        "oklab": {"L": round(L, 3), "a": round(a, 3), "b": round(b, 3)},
    }


def extract_top10_similar_area_oklab(
    image_path: str | Path,
    k: int = 10,
    sample_ratio: float = 0.35,
    max_samples: int = 40000,
    random_state: int = 42,
) -> dict:
    img_bgr = cv2.imread(str(image_path))
    if img_bgr is None:
        raise ValueError(f"Unable to read image: {image_path}")

    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    pixels_rgb = img_rgb.reshape(-1, 3)
    n = len(pixels_rgb)

    sample_n = max(k, min(int(n * sample_ratio), max_samples))
    rng = np.random.default_rng(random_state)
    sample_idx = rng.choice(n, sample_n, replace=False)
    sampled_rgb = pixels_rgb[sample_idx]

    sampled_oklab = _rgb255_to_oklab(sampled_rgb)

    # Clustering in Oklab approximates perceptual grouping via color distance.
    kmeans = KMeans(n_clusters=k, n_init=10, random_state=random_state)
    labels = kmeans.fit_predict(sampled_oklab)
    centers = kmeans.cluster_centers_

    counts = np.bincount(labels, minlength=k).astype(np.float64)
    ratios = counts / counts.sum()
    sort_idx = np.argsort(-ratios)

    top_colors = [
        _center_to_record(rank=i + 1, center=centers[idx], ratio=float(ratios[idx]))
        for i, idx in enumerate(sort_idx[:k])
    ]

    return {
        "dimension": "similar_color_area_sum",
        "description": "Aggregate visually similar colors using Oklab distance clustering.",
        "top_colors": top_colors,
    }
