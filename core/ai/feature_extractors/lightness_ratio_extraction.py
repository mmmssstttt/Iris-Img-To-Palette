from pathlib import Path
import cv2
import numpy as np
from sklearn.cluster import KMeans
from core.colors.color_oklch import _rgb_to_oklab_vectorized

def extract_top10_lightness_ratio_oklab(
    image_path: str | Path,
    k: int = 10,
    max_samples: int = 40000,
    random_state: int = 42,
    contrast_gain: float = 2.0,
) -> dict:
    # Secure reading and basic defense
    img_bgr = cv2.imread(str(image_path))
    if img_bgr is None:
        raise ValueError(f"Unable to read image or file does not exist : {image_path}")
    
    # If the image is extremely large, downscale while preserving aspect ratio.
    h, w = img_bgr.shape[:2]
    if h * w > 1000000:
        target_max_side = 500
        scale = target_max_side / max(h, w)
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        img_bgr = cv2.resize(img_bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)

    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    pixels_rgb = img_rgb.reshape(-1, 3).astype(np.float32) / 255.0

    # Vectorized sampling
    n = len(pixels_rgb)
    sample_n = min(n, max_samples)
    effective_k = min(k, sample_n)
    rng = np.random.default_rng(random_state)
    sampled_rgb = rng.choice(pixels_rgb, sample_n, axis=0, replace=False)

    sampled_oklab = _rgb_to_oklab_vectorized(sampled_rgb)
    lightness = sampled_oklab[:, 0]

    edge_strength = np.abs(lightness - 0.5) * 2.0
    weights = 1.0 + contrast_gain * np.clip(edge_strength, 0.0, 1.0)

    kmeans = KMeans(n_clusters=effective_k, n_init=3, init='k-means++', random_state=random_state)
    labels = kmeans.fit_predict(sampled_oklab, sample_weight=weights)
    centers = kmeans.cluster_centers_

    # Result Calculation
    cluster_weight = np.bincount(labels, weights=weights, minlength=effective_k)
    weighted_ratio = cluster_weight / cluster_weight.sum()
    
    # Calculate the average brightness of each group
    counts = np.bincount(labels, minlength=effective_k)
    mean_lightness = np.bincount(labels, weights=lightness, minlength=effective_k) / np.maximum(counts, 1)

    # Sorting and Encapsulation
    sort_idx = np.argsort(-weighted_ratio)
    top_colors = []
    for i, idx in enumerate(sort_idx[:effective_k]):
        L, a, b = centers[idx]
        top_colors.append({
            "rank": i + 1,
            "weighted_ratio": round(float(weighted_ratio[idx]), 3),
            "score": round(float(weighted_ratio[idx]), 3),
            "mean_lightness": round(float(mean_lightness[idx]), 3),
            "oklab": {"L": round(float(L), 3), "a": round(float(a), 3), "b": round(float(b), 3)},
        })

    return {
        "dimension": "lightness_ratio",
        "top_colors": top_colors,
    }
