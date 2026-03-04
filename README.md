# Iris-AI

[![GitHub last commit](https://img.shields.io/github/last-commit/moosh0114/Iris-img-to-palette.svg)](https://github.com/moosh0114/Iris-img-to-palette)
[![GitHub repo size](https://img.shields.io/github/repo-size/moosh0114/Iris-img-to-palette.svg)](https://github.com/moosh0114/Iris-img-to-palette)

<img src="https://github.com/moosh0114/Iris-img-to-palette/blob/main/logo/logo.png" alt="Iris-Color-Processor" style="height: 280px; width: auto;" />

### Image Color Extraction to OKLCH Palette

IMPORTANT: This project is in development/testing. Do not use commercially for now.

## Dependencies

Backend:
- FastAPI
- OpenCV
- scikit-learn
- NumPy
- Jinja2

GUI:
- Alpine.js
- HTMX
- Tailwind CSS (browser build)

## Quickstart (GUI)

```shell
python -m pip install --upgrade pip
python -m pip install uv
python -m uv sync
python -m uv run uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`

- DB: `data/app.db`
- Uploads: `data/uploads/`

## API Notes

Current implementation uses REST endpoints for the web UI:
- `POST /api/extract`
- `GET /api/result/{result_id}`
- `GET /history`
- `POST /api/history/clear`

Runtime constraints and controls:
- `POST /api/extract` batch limit: up to **1000 images** per run (enforced on both frontend and backend).
- `n_colors` range: **1..12**.
- Keyboard shortcuts:
  - `ArrowUp` / `ArrowDown`: increase/decrease `n_colors`
  - `Enter`: submit (`GO`)
  - `ArrowLeft` / `ArrowRight`: switch preview image

## Run Script (CLI)

```shell
uv run python -m scripts.extract_colors
```

Note: the script entry currently reads `test.jpg` in repo root when run directly.

## Licenses

- FastAPI: https://github.com/fastapi/fastapi/blob/master/LICENSE
- scikit-learn: https://github.com/scikit-learn/scikit-learn?tab=BSD-3-Clause-1-ov-file#readme
- OpenCV: https://github.com/opencv/opencv/blob/4.x/LICENSE
- uv: https://github.com/astral-sh/uv/blob/main/LICENSE-MIT and https://github.com/astral-sh/uv/blob/main/LICENSE-APACHE
- Alpine.js: https://github.com/alpinejs/alpine/blob/main/LICENSE.md
- HTMX: https://github.com/bigskysoftware/htmx/blob/master/LICENSE
- Tailwind CSS: https://github.com/tailwindlabs/tailwindcss/blob/main/LICENSE
