from pathlib import Path
import tempfile
import os
import shutil
import traceback
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from fastapi import FastAPI, File, UploadFile, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.concurrency import run_in_threadpool
from fastapi.staticfiles import StaticFiles

import sys
import json
import asyncio

# Add project root to sys path so we can import core modules.
sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.ai.gwo_extraction import extract_top10_gwo
from core.ai.saliency_extraction import extract_top10_saliency
from core.ai.k_means_extractor import extract_top10_kmeans

from core.ai.area_ratio_extraction import extract_top10_area_ratio_oklab
from core.ai.chroma_saliency_extraction import extract_top10_chroma_saliency_oklab
from core.ai.lightness_ratio_extraction import extract_top10_lightness_ratio_oklab
from core.ai.similar_area_extraction import extract_top10_similar_area_oklab
from core.colors.color_oklch import _linear_rgb_to_oklab, _srgb_channel_to_linear
from core.colors.color_hex import hex_to_rgb


app = FastAPI(title="Palette Extraction App")
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))

app.mount("/static", StaticFiles(directory=str(Path(__file__).resolve().parent / "static")), name="static")

@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "selected_method": "gwo",
        },
    )


def _build_visual_rankings(area_data: dict) -> dict:
    base = area_data.get("top_colors", [])

    def _chroma(item: dict) -> float:
        o = item.get("oklab", {})
        a = float(o.get("a", 0.0))
        b = float(o.get("b", 0.0))
        return (a * a + b * b) ** 0.5

    vivid = sorted(base, key=_chroma, reverse=True)
    bright = sorted(base, key=lambda x: float(x.get("oklab", {}).get("L", 0.0)), reverse=True)

    return {
        "dominant_main_color_ranking": [
            {
                "rank": idx + 1,
                "area_ratio": round(float(item.get("area_ratio", 0.0)), 3),
                "oklab": item.get("oklab", {}),
            }
            for idx, item in enumerate(base)
        ],
        "vividness_ranking": [
            {
                "rank": idx + 1,
                "chroma": round(_chroma(item), 3),
                "oklab": item.get("oklab", {}),
            }
            for idx, item in enumerate(vivid)
        ],
        "brightness_ranking": [
            {
                "rank": idx + 1,
                "lightness": round(float(item.get("oklab", {}).get("L", 0.0)), 3),
                "oklab": item.get("oklab", {}),
            }
            for idx, item in enumerate(bright)
        ],
    }


def _to_oklab_palette(colors) -> list[dict]:
    rows = []
    for i, c in enumerate(colors, 1):
        r = int(c[0])
        g = int(c[1])
        b = int(c[2])
        lr = _srgb_channel_to_linear(r / 255.0)
        lg = _srgb_channel_to_linear(g / 255.0)
        lb = _srgb_channel_to_linear(b / 255.0)
        L, a, b_lab = _linear_rgb_to_oklab(lr, lg, lb)
        rows.append(
            {
                "rank": i,
                "oklab": {"L": round(float(L), 3), "a": round(float(a), 3), "b": round(float(b_lab), 3)},
            }
        )
    return rows


def _to_oklab_user_selected(colors_list) -> list[dict]:
    if not isinstance(colors_list, list):
        raise ValueError("selected_colors must be a JSON array")

    rows = []
    for i, color in enumerate(colors_list, 1):
        if isinstance(color, str):
            r, g, b = hex_to_rgb(color)
        elif isinstance(color, dict) and {"r", "g", "b"}.issubset(color.keys()):
            r = int(color["r"])
            g = int(color["g"])
            b = int(color["b"])
        else:
            raise ValueError(f"Invalid selected color payload at index {i - 1}: {color}")

        lr = _srgb_channel_to_linear(r / 255.0)
        lg = _srgb_channel_to_linear(g / 255.0)
        lb = _srgb_channel_to_linear(b / 255.0)
        L, a, b_lab = _linear_rgb_to_oklab(lr, lg, lb)
        rows.append(
            {
                "rank": i,
                "oklab": {"L": round(float(L), 3), "a": round(float(a), 3), "b": round(float(b_lab), 3)},
            }
        )
    return rows


def _write_pretty_json_with_inline_oklab(path: Path, data) -> None:
    def _format_json(obj, level: int = 0, indent: int = 2) -> str:
        if isinstance(obj, dict):
            # Keep compact one-line JSON for rank payloads and oklab triplets.
            if "rank" in obj or (set(obj.keys()) == {"L", "a", "b"}):
                return json.dumps(obj, ensure_ascii=False, separators=(", ", ": "))

            if not obj:
                return "{}"

            pad = " " * (indent * level)
            child_pad = " " * (indent * (level + 1))
            parts = []
            for key, value in obj.items():
                key_str = json.dumps(key, ensure_ascii=False)
                value_str = _format_json(value, level + 1, indent)
                parts.append(f"{child_pad}{key_str}: {value_str}")
            return "{\n" + ",\n".join(parts) + "\n" + pad + "}"

        if isinstance(obj, list):
            if not obj:
                return "[]"

            pad = " " * (indent * level)
            child_pad = " " * (indent * (level + 1))
            parts = [f"{child_pad}{_format_json(item, level + 1, indent)}" for item in obj]
            return "[\n" + ",\n".join(parts) + "\n" + pad + "]"

        return json.dumps(obj, ensure_ascii=False)

    text = _format_json(data, level=0, indent=2)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text + "\n")


@app.post("/api/extract", response_class=HTMLResponse)
async def api_extract(
    request: Request,
    image: UploadFile = File(...),
    method: str = Form("gwo"),
) -> HTMLResponse:
    if not image:
        return HTMLResponse("<div class='text-red-500'>No image uploaded</div>", status_code=400)

    method = (method or "gwo").strip().lower()

    if method not in {"gwo", "saliency", "k-means"}:
        return HTMLResponse("<div class='text-red-500'>Invalid extraction method</div>", status_code=400)

    fd, temp_path = tempfile.mkstemp(suffix=".png")
    os.close(fd)

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        if method == "saliency":
            colors = await run_in_threadpool(extract_top10_saliency, temp_path, 10)
        elif method == "k-means":
            colors = await run_in_threadpool(extract_top10_kmeans, temp_path, 10)
        else:
            colors = await run_in_threadpool(extract_top10_gwo, temp_path, 10)

    except Exception:
        tb = traceback.format_exc()
        logger.error("[EXTRACTION ERROR]\n%s", tb)
        return HTMLResponse(
            f"<pre style='color:red;white-space:pre-wrap;font-size:12px'>[DEBUG] {tb}</pre>",
            status_code=500,
        )
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    palette = [
        {
            "r": int(c[0]),
            "g": int(c[1]),
            "b": int(c[2]),
            "hex": f"#{int(c[0]):02x}{int(c[1]):02x}{int(c[2]):02x}",
        }
        for c in colors
    ]

    return templates.TemplateResponse(
        "partials/result.html",
        {
            "request": request,
            "palette": palette,
            "image_filename": image.filename,
            "method": "SALIENCY" if method == "saliency" else ("K-MEANS" if method == "k-means" else method.upper()),
        },
    )

@app.post("/api/record")
async def api_record(
    image: UploadFile = File(...),
    selected_colors: str = Form(...)
):
    try:
        colors_list = json.loads(selected_colors)
    except json.JSONDecodeError:
        return JSONResponse({"detail": "Invalid selected_colors format"}, status_code=400)
    except Exception:
        return JSONResponse({"detail": "Invalid selected_colors payload"}, status_code=400)

    try:
        user_selected_oklab = _to_oklab_user_selected(colors_list)
    except Exception as e:
        return JSONResponse({"detail": str(e)}, status_code=400)

    if not image:
        return JSONResponse({"detail": "No image uploaded"}, status_code=400)

    fd, temp_path = tempfile.mkstemp(suffix=".png")
    os.close(fd)

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        # Run core extraction algorithms and serialize results in Oklab format.
        gwo_task = run_in_threadpool(extract_top10_gwo, temp_path, 10)
        kmeans_task = run_in_threadpool(extract_top10_kmeans, temp_path, 10)
        saliency_task = run_in_threadpool(extract_top10_saliency, temp_path, 10)

        # Run Oklab visual-dimension extractors.
        area_task = run_in_threadpool(extract_top10_area_ratio_oklab, temp_path, 10)
        similar_task = run_in_threadpool(extract_top10_similar_area_oklab, temp_path, 10)
        chroma_task = run_in_threadpool(extract_top10_chroma_saliency_oklab, temp_path, 10)
        lightness_task = run_in_threadpool(extract_top10_lightness_ratio_oklab, temp_path, 10)

        (
            gwo_colors,
            kmeans_colors,
            saliency_colors,
            area_data,
            similar_data,
            chroma_data,
            lightness_data,
        ) = await asyncio.gather(
            gwo_task,
            kmeans_task,
            saliency_task,
            area_task,
            similar_task,
            chroma_task,
            lightness_task,
        )

        visual_rankings = _build_visual_rankings(area_data)

        record = {
            "image_name": image.filename,
            "gwo_colors": _to_oklab_palette(gwo_colors),
            "kmeans_colors": _to_oklab_palette(kmeans_colors),
            "saliency_colors": _to_oklab_palette(saliency_colors),
            "user_selected_colors": user_selected_oklab,
            "visual_dimensions_oklab": {
                "physical_area_ratio": area_data,
                "similar_color_area_sum": similar_data,
                "chroma_saliency": chroma_data,
                "lightness_ratio": lightness_data,
            },
            "visual_rankings": visual_rankings,
        }

        data_file = Path(__file__).resolve().parent.parent / "training_data.json"
        
        all_data = []
        if data_file.exists():
            try:
                with open(data_file, "r", encoding="utf-8") as f:
                    all_data = json.load(f)
            except Exception as e:
                logger.error(f"Error reading training_data.json: {e}")
                all_data = []

        all_data.append(record)

        _write_pretty_json_with_inline_oklab(data_file, all_data)

        return JSONResponse({"status": "success", "message": "Record saved"})

    except Exception:
        tb = traceback.format_exc()
        logger.error("[RECORD ERROR]\n%s", tb)
        return JSONResponse({"detail": str(tb)}, status_code=500)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
