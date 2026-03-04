import argparse
import json
from pathlib import Path

import cv2
import numpy as np
from sklearn.cluster import KMeans

from .color_oklch import hex_to_oklch


def _resize_for_speed(image_bgr: np.ndarray) -> np.ndarray:
    height, width = image_bgr.shape[:2]
    target_width = max(1, min(100, int(width * 0.1)))

    if target_width >= width:
        return image_bgr

    target_height = max(1, int(height * (target_width / width)))
    return cv2.resize(image_bgr, (target_width, target_height), interpolation=cv2.INTER_AREA)


def extract_dominant_colors(image_path: str, n_colors: int = 3) -> list[dict[str, object]]:
    image_bytes = np.fromfile(Path(image_path), dtype=np.uint8)
    image_bgr = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)
    if image_bgr is None:
        raise ValueError(f"Invalid or corrupted image format: {image_path}")

    small_bgr = _resize_for_speed(image_bgr)
    image_rgb = cv2.cvtColor(small_bgr, cv2.COLOR_BGR2RGB)

    pixels = image_rgb.reshape(-1, 3)
    kmeans = KMeans(n_clusters=n_colors, n_init="auto", random_state=42)
    labels = kmeans.fit_predict(pixels)

    counts = np.bincount(labels, minlength=n_colors)
    centers = np.rint(kmeans.cluster_centers_).astype(np.uint8)
    sorted_indices = np.argsort(counts)[::-1]

    results: list[dict[str, object]] = []
    for idx in sorted_indices:
        hex_color = "#{:02x}{:02x}{:02x}".format(*centers[idx])
        L, c, h = hex_to_oklch(hex_color)
        if c < 1e-9:
            h = 0.0
        results.append(
            {
                "hex": hex_color,
                "oklch": {
                    "L": round(float(L), 6),
                    "c": round(float(c), 6),
                    "h": round(float(h), 6),
                },
            }
        )
    return results


def cli_main() -> int:
    parser = argparse.ArgumentParser(description="Extract dominant colors from an image.")
    parser.add_argument("image", help="Input image path")
    parser.add_argument("-n", "--n-colors", type=int, default=3, help="Number of colors to extract")
    args = parser.parse_args()

    colors = extract_dominant_colors(args.image, args.n_colors)
    print(json.dumps(colors, ensure_ascii=False, indent=2))
    return 0
