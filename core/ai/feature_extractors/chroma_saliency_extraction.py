from __future__ import annotations
from pathlib import Path
import cv2
import numpy as np
from sklearn.cluster import KMeans

from core.colors.color_oklch import _rgb_to_oklab_vectorized

def _center_to_record(rank: int, center: np.ndarray, ratio: float, mean_chroma: float) -> dict:
    return {
        "rank": int(rank),
        "weighted_ratio": round(float(ratio), 3),
        "score": round(float(ratio), 3),
        "mean_chroma": round(float(mean_chroma), 3),
        "oklab": {"L": round(float(center[0]), 3), "a": round(float(center[1]), 3), "b": round(float(center[2]), 3)},
    }

def extract_top10_chroma_saliency_oklab(
    image_path: str | Path,
    k: int = 10,
    sample_ratio: float = 0.35,
    max_samples: int = 40000,
    random_state: int = 42,
    saliency_gain: float = 2.5,
) -> dict:
    img_bgr = cv2.imread(str(image_path))
    if img_bgr is None:
        raise ValueError(f"Unable to read image: {image_path}")

    # If the image is very large, pre-scaling can save memory
    h, w = img_bgr.shape[:2]
    if h * w > 4000000:
        scale = 2000 / max(h, w)
        img_bgr = cv2.resize(img_bgr, None, fx=scale, fy=scale)

    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    pixels_rgb = img_rgb.reshape(-1, 3)
    n = len(pixels_rgb)

    # sampling
    sample_n = min(n, max(k, min(int(n * sample_ratio), max_samples)))
    effective_k = min(k, sample_n)
    rng = np.random.default_rng(random_state)
    sample_idx = rng.choice(n, sample_n, replace=False)
    sampled_rgb = pixels_rgb[sample_idx]

    rgb_unit = np.clip(sampled_rgb.astype(np.float64) / 255.0, 0.0, 1.0)
    sampled_oklab = _rgb_to_oklab_vectorized(rgb_unit)

    # Calculate chroma and weight
    chroma = np.sqrt(sampled_oklab[:, 1] ** 2 + sampled_oklab[:, 2] ** 2)
    chroma_p95 = float(np.quantile(chroma, 0.95))
    denom = max(chroma_p95, 1e-6)
    chroma_norm = np.clip(chroma / denom, 0.0, 1.0)
    weights = 1.0 + saliency_gain * chroma_norm

    # K-Means
    kmeans = KMeans(n_clusters=effective_k, n_init=10, random_state=random_state)
    kmeans.fit(sampled_oklab, sample_weight=weights)
    
    labels = kmeans.labels_
    centers = kmeans.cluster_centers_

    # Statistical results
    cluster_weight = np.bincount(labels, weights=weights, minlength=effective_k)
    weighted_ratio = cluster_weight / cluster_weight.sum()
    
    counts = np.bincount(labels, minlength=effective_k)
    mean_chroma = np.bincount(labels, weights=chroma, minlength=effective_k) / np.maximum(counts, 1.0)
    
    sort_idx = np.argsort(-weighted_ratio)

    top_colors = [
        _center_to_record(
            rank=i + 1,
            center=centers[idx],
            ratio=weighted_ratio[idx],
            mean_chroma=mean_chroma[idx],
        )
        for i, idx in enumerate(sort_idx[:effective_k])
    ]

    return {
        "dimension": "chroma_saliency",
        "top_colors": top_colors,
    }
