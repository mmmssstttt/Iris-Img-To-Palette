from __future__ import annotations
from pathlib import Path
import cv2
import numpy as np

from core.colors.color_oklch import _rgb_to_oklab_vectorized

def extract_top10_area_ratio_oklab(
    image_path: str | Path,
    k: int = 10,
    bins_per_channel: int = 32,
) -> dict:
    img_bgr = cv2.imread(str(image_path))
    if img_bgr is None:
        raise ValueError(f"Unable to read image: {image_path}")

    max_side = 400
    h, w = img_bgr.shape[:2]
    if max(h, w) > max_side:
        scale = max_side / max(h, w)
        img_bgr = cv2.resize(img_bgr, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    pixels = img_rgb.reshape(-1, 3).astype(np.int32)
    total = pixels.shape[0]

    step = 256 // bins_per_channel
    q = np.clip(pixels // step, 0, bins_per_channel - 1)
    keys = q[:, 0] * bins_per_channel * bins_per_channel + q[:, 1] * bins_per_channel + q[:, 2]

    uniq, inv, counts = np.unique(keys, return_inverse=True, return_counts=True)
    sort_idx = np.argsort(-counts)[:k]
    
    # 1. First, collect the average RGB values ​​of all top K values
    top_avg_rgbs = []
    ratios = []
    for idx in sort_idx:
        mask = (inv == idx)
        actual_rgb = np.mean(pixels[mask], axis=0) / 255.0  # Convert to 0-1 floating-point numbers
        top_avg_rgbs.append(actual_rgb)
        ratios.append(counts[idx] / total)
    
    # 2. One-time vectorization conversion
    oklabs = _rgb_to_oklab_vectorized(np.array(top_avg_rgbs))
    
    # 3. Assemble the results
    top_colors = []
    for i, (lab, ratio) in enumerate(zip(oklabs, ratios)):
        top_colors.append({
            "rank": i + 1,
            "area_ratio": round(float(ratio), 3),
            "oklab": {"L": round(float(lab[0]), 3), "a": round(float(lab[1]), 3), "b": round(float(lab[2]), 3)},
        })

    return {
        "dimension": "physical_area_ratio",
        "top_colors": top_colors,
    }
