# Iris-AI

[![GitHub last commit](https://img.shields.io/github/last-commit/moosh0114/Iris-img-to-palette.svg)](https://github.com/moosh0114/Iris-img-to-palette)
[![CodeQL Advanced](https://github.com/mmmssstttt/Iris-Img-To-Palette/actions/workflows/codeql.yml/badge.svg)](https://github.com/mmmssstttt/Iris-Img-To-Palette/actions/workflows/codeql.yml)
[![GitHub repo size](https://img.shields.io/github/repo-size/moosh0114/Iris-img-to-palette.svg)](https://github.com/moosh0114/Iris-img-to-palette)
[![Lyra](https://img.shields.io/badge/Designed_with-Lyra-FFC6EC?logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAwIiBoZWlnaHQ9IjEzMDAiIHZpZXdCb3g9IjAgMCA4MDAgMTMwMCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3QgeD0iNzUiIHk9Ijc1IiB3aWR0aD0iNjUwIiBoZWlnaHQ9IjExNTAiIHN0cm9rZT0idXJsKCNwYWludDBfbGluZWFyXzIxNjVfNykiIHN0cm9rZS13aWR0aD0iMTUwIi8+CjxkZWZzPgo8bGluZWFyR3JhZGllbnQgaWQ9InBhaW50MF9saW5lYXJfMjE2NV83IiB4MT0iNDAwIiB5MT0iMCIgeDI9IjQwMCIgeTI9IjEzMDAiIGdyYWRpZW50VW5pdHM9InVzZXJTcGFjZU9uVXNlIj4KPHN0b3Agc3RvcC1jb2xvcj0iI0JCRkZFRCIvPgo8c3RvcCBvZmZzZXQ9IjAuNjk3MTE1IiBzdG9wLWNvbG9yPSIjRkZFQ0Y0Ii8+CjwvbGluZWFyR3JhZGllbnQ+CjwvZGVmcz4KPC9zdmc+)](https://github.com/zzztzzzt/Lyra-AI)

<br>
<img src="https://github.com/moosh0114/Iris-img-to-palette/blob/main/logo/logo.png" alt="Iris-Color-Processor" style="height: 280px; width: auto;" />

### Iris - Refinement Network for Image Color-Extraction

IMPORTANT : This project is still in the development and testing stages, licensing terms may be updated in the future. Please don't do any commercial usage currently.

## Project Dependencies Guide

[![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://github.com/pytorch/pytorch)
[![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://github.com/opencv/opencv)
[![scikit-learn](https://img.shields.io/badge/scikit_learn-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white)](https://github.com/scikit-learn/scikit-learn)
[![SciPy](https://img.shields.io/badge/SciPy-8CAAE6?style=for-the-badge&logo=scipy&logoColor=white)](https://github.com/scipy/scipy)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://github.com/fastapi/fastapi)

**( GUI )**

[![Alpine.js](https://img.shields.io/badge/Alpine.js-8BC0D0?style=for-the-badge&logo=alpinedotjs&logoColor=white)](https://github.com/alpinejs/alpine)
[![HTMX](https://img.shields.io/badge/HTMX-3366CC?style=for-the-badge&logo=htmx&logoColor=white)](https://github.com/bigskysoftware/htmx)
[![Tailwind CSS](https://img.shields.io/badge/tailwind_css-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)](https://github.com/tailwindlabs/tailwindcss)
[![Jinja](https://img.shields.io/badge/Jinja-7E0C1B?style=for-the-badge&logo=jinja&logoColor=white)](https://github.com/pallets/jinja)

**[ for Dependencies Details please see the end of this README ]**

Iris uses PyTorch for AI Model Building. PyTorch licensed under BSD 3-Clause License.

Iris uses FastAPI for backend APIs and GUI integration, and uses scikit-learn, SciPy & OpenCV for image color extraction. FastAPI is MIT licensed, scikit-learn & SciPy licensed under the BSD 3-Clause License, OpenCV is licensed under the Apache-2.0 License.

Iris uses Alpine.js, HTMX, Jinja & Tailwind CSS for GUI showing. Alpine.js & Tailwind CSS licensed under the MIT License. HTMX licensed under Zero-Clause BSD License. Jinja licensed under BSD 3-Clause License.

![gui](https://github.com/mmmssstttt/Iris-Img-To-Palette/blob/main/training_showcase/Iris1.0_gui.png)

**( Iris 1.0 Predictions )**

![1.0predictions](https://github.com/mmmssstttt/Iris-Img-To-Palette/blob/main/training_showcase/Iris1.0_predictions.png)

## Quickstart ( GUI )

**Build Dependencies ( Install uv )**

upgrade : `python -m pip install --upgrade pip`

use uv : `python -m pip install uv` & `python -m uv sync`

```shell
python -m uv run uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`

**DB** : `data/app.db`
**Uploads** : `data/uploads/`

`POST /api/extract` batch limit : `1000` images (frontend + backend)

`n_colors` range : `1..12`

Keyboard : `ArrowUp/ArrowDown` adjust `n_colors`, `Enter` submit, `ArrowLeft/ArrowRight` switch preview image.

## How To Train

### Training via GUI ( Recommended )

```shell
python -m uv run uvicorn extractor_app.main:app --reload
```

### Training via CLI / Shell command

prepare your training data & at CDM, run below to train model : 

```shell
python -m uv run python -m scripts.train_palette_selector --data training_data.json
```

your model will be saved to `models/palette_scorer.pth`

and run below to predict : 

```shell
python -m uv run python -m scripts.predict_palette_selector --data training_data.json
```

## Project Dependencies Details

PyTorch License : [https://github.com/pytorch/pytorch/blob/main/LICENSE](https://github.com/pytorch/pytorch/blob/main/LICENSE)
<br>

FastAPI License : [https://github.com/fastapi/fastapi/blob/master/LICENSE](https://github.com/fastapi/fastapi/blob/master/LICENSE)
<br>

scikit-learn License : [https://github.com/scikit-learn/scikit-learn?tab=BSD-3-Clause-1-ov-file#readme](https://github.com/scikit-learn/scikit-learn?tab=BSD-3-Clause-1-ov-file#readme)
<br>

SciPy License : [https://github.com/scipy/scipy/blob/main/LICENSE.txt](https://github.com/scipy/scipy/blob/main/LICENSE.txt)
<br>

OpenCV License : [https://github.com/opencv/opencv/blob/4.x/LICENSE](https://github.com/opencv/opencv/blob/4.x/LICENSE)
<br>

Alpine.js License : [https://github.com/alpinejs/alpine/blob/main/LICENSE.md](https://github.com/alpinejs/alpine/blob/main/LICENSE.md)
<br>

HTMX License : [https://github.com/bigskysoftware/htmx/blob/master/LICENSE](https://github.com/bigskysoftware/htmx/blob/master/LICENSE)
<br>

Jinja License : [https://github.com/pallets/jinja/blob/main/LICENSE.txt](https://github.com/pallets/jinja/blob/main/LICENSE.txt)
<br>

Tailwind CSS License : [https://github.com/tailwindlabs/tailwindcss/blob/main/LICENSE](https://github.com/tailwindlabs/tailwindcss/blob/main/LICENSE)
