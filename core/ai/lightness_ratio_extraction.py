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


def _center_to_record(rank: int, center: np.ndarray, ratio: float, mean_lightness: float) -> dict:
    L, a, b = float(center[0]), float(center[1]), float(center[2])
    return {
        "rank": int(rank),
        "weighted_ratio": round(float(ratio), 3),
        "score": round(float(ratio), 3),
        "mean_lightness": round(float(mean_lightness), 3),
        "oklab": {"L": round(L, 3), "a": round(a, 3), "b": round(b, 3)},
    }


def extract_top10_lightness_ratio_oklab(
    image_path: str | Path,
    k: int = 10,
    sample_ratio: float = 0.35,
    max_samples: int = 40000,
    random_state: int = 42,
    contrast_gain: float = 2.0,
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
    lightness = sampled_oklab[:, 0]

    # Give more weight to very bright / very dark regions.
    edge_strength = np.abs(lightness - 0.5) * 2.0
    weights = 1.0 + contrast_gain * np.clip(edge_strength, 0.0, 1.0)

    kmeans = KMeans(n_clusters=k, n_init=10, random_state=random_state)
    kmeans.fit(sampled_oklab, sample_weight=weights)
    labels = kmeans.labels_
    centers = kmeans.cluster_centers_

    cluster_weight = np.bincount(labels, weights=weights, minlength=k).astype(np.float64)
    weighted_ratio = cluster_weight / cluster_weight.sum()
    mean_lightness = np.bincount(labels, weights=lightness, minlength=k) / np.maximum(
        np.bincount(labels, minlength=k),
        1.0,
    )
    sort_idx = np.argsort(-weighted_ratio)

    top_colors = [
        _center_to_record(
            rank=i + 1,
            center=centers[idx],
            ratio=float(weighted_ratio[idx]),
            mean_lightness=float(mean_lightness[idx]),
        )
        for i, idx in enumerate(sort_idx[:k])
    ]

    return {
        "dimension": "lightness_ratio",
        "description": "Use Oklab L with extreme-lightness weighting for tonal dominance.",
        "top_colors": top_colors,
    }
