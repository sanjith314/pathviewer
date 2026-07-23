# PathViewer

A web-based digital pathology slide viewer built on
[OpenSeadragon](https://openseadragon.github.io/) with a Python
[OpenSlide](https://openslide.org/) DeepZoom tile server.

Supports **jpg**, **svs** (Aperio), pyramidal **tiff**, and **ndpi** (Hamamatsu).
Tiles are generated on demand, so multi-gigabyte slides open instantly and the
browser only downloads the tiles currently in view.

## Features

- Smooth deep-zoom pan/zoom to full magnification
- Thumbnail navigator (mini-map)
- Real-world scale bar computed from the slide's microns-per-pixel
- Slide list with thumbnails + metadata panel (dimensions, MPP, objective, vendor)
- Drag-and-drop upload

## Requirements

- Python 3.10+
- No system OpenSlide install needed - `openslide-bin` ships the native binaries.
- Internet access in the browser (OpenSeadragon + scale bar plugin load via CDN).

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

## Run

```bash
source .venv/bin/activate
cd backend
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000, then upload a slide or drop slide files into the
`slides/` directory.

## Trying it with sample data

Public OpenSlide test slides (e.g. `CMU-1.svs`, `CMU-1.ndpi`) are available at
<https://openslide.org/> under test data. Place any `.jpg/.svs/.tif/.tiff/.ndpi`
file into `slides/` and it will appear in the sidebar.

## Project layout

```
backend/app/config.py   paths, formats, DeepZoom + cache settings
backend/app/slides.py   slide cache, tiling, metadata, thumbnails
backend/app/main.py     FastAPI routes + static frontend
frontend/               OpenSeadragon UI (HTML/CSS/JS)
slides/                 slide files (gitignored)
```

See [PLAN.md](PLAN.md) for the full design and [AGENTS.md](AGENTS.md) for
implementation context.
