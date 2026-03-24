from __future__ import annotations
from pathlib import Path
import cv2
import numpy as np
from sklearn.cluster import MiniBatchKMeans

from core.colors.color_oklch import _rgb_to_oklab_vectorized

def extract_top10_similar_area_oklab(
    image_path: str | Path,
    k: int = 10,
    max_samples: int = 40000,
    random_state: int = 42,
) -> dict:
    # 1. Securely read images
    img_bgr = cv2.imread(str(image_path))
    if img_bgr is None:
        raise ValueError(f"Could not open or find the image: {image_path}")

    # 2. Scaling or sampling before transformation avoids performing calculations on the entire image
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    pixels = img_rgb.reshape(-1, 3)
    
    # Limit the number of samples to optimize performance
    n_pixels = pixels.shape[0]
    sample_n = min(n_pixels, max_samples)
    effective_k = min(k, sample_n)
    rng = np.random.default_rng(random_state)
    sampled_rgb = rng.choice(pixels, sample_n, axis=0, replace=False)

    # 3. Vectorized color conversion
    sampled_oklab = _rgb_to_oklab_vectorized(sampled_rgb.astype(np.float64) / 255.0)

    # 4. Improve clustering speed using MiniBatchKMeans
    kmeans = MiniBatchKMeans(
        n_clusters=effective_k, 
        batch_size=1024, 
        n_init="auto", 
        random_state=random_state
    ).fit(sampled_oklab)
    
    # 5. Results Calculation and Sorting
    unique_labels, counts = np.unique(kmeans.labels_, return_counts=True)
    ratios = counts / counts.sum()
    
    # Arranged in descending order of proportion
    sorted_indices = np.argsort(-ratios)
    top_colors = []
    for i, idx in enumerate(sorted_indices[:effective_k]):
        center_idx = int(unique_labels[idx])
        L, a, b = kmeans.cluster_centers_[center_idx]
        ratio = float(ratios[idx])
        top_colors.append({
            "rank": i + 1,
            "area_ratio": round(ratio, 3),
            "oklab": {"L": round(float(L), 3), "a": round(float(a), 3), "b": round(float(b), 3)},
        })

    return {
        "dimension": "similar_color_area_sum",
        "top_colors": top_colors,
    }
