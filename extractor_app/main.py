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
import asyncio# Add project root to sys path so we can import core modules.
sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.ai.gwo_extraction import extract_top10_oklab
from core.ai.k_means_extractor import extract_top10_kmeans
from core.ai.saliency_extraction import extract_top10_saliency


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
            colors = await run_in_threadpool(extract_top10_oklab, temp_path, 10)

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

    if not image:
        return JSONResponse({"detail": "No image uploaded"}, status_code=400)

    fd, temp_path = tempfile.mkstemp(suffix=".png")
    os.close(fd)

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        # Run all algorithms
        gwo_task = run_in_threadpool(extract_top10_oklab, temp_path, 10)
        kmeans_task = run_in_threadpool(extract_top10_kmeans, temp_path, 10)
        saliency_task = run_in_threadpool(extract_top10_saliency, temp_path, 10)

        gwo_colors, kmeans_colors, saliency_colors = await asyncio.gather(
            gwo_task, kmeans_task, saliency_task
        )

        def format_colors(colors):
            return [f"#{int(c[0]):02x}{int(c[1]):02x}{int(c[2]):02x}" for c in colors]

        record = {
            "image_name": image.filename,
            "user_selected_colors": colors_list,
            "gwo_colors": format_colors(gwo_colors),
            "kmeans_colors": format_colors(kmeans_colors),
            "saliency_colors": format_colors(saliency_colors)
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

        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(all_data, f, indent=4, ensure_ascii=False)

        return JSONResponse({"status": "success", "message": "Record saved"})

    except Exception:
        tb = traceback.format_exc()
        logger.error("[RECORD ERROR]\n%s", tb)
        return JSONResponse({"detail": str(tb)}, status_code=500)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
