"""Configuration for the pathology viewer tile server."""
from __future__ import annotations

from pathlib import Path

# Project root is two levels up from this file (backend/app/config.py -> repo root).
REPO_ROOT = Path(__file__).resolve().parents[2]

# Directory that holds slide files (sample + uploaded).
SLIDES_DIR = Path(__file__).resolve().parents[1].parent / "slides"

# Directory with the static frontend assets.
FRONTEND_DIR = REPO_ROOT / "frontend"

# Supported slide extensions. jpg/jpeg are opened via PIL (ImageSlide); the
# rest are pyramidal whole-slide formats decoded by OpenSlide.
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".svs", ".tif", ".tiff", ".ndpi"}

# DeepZoom tiling parameters. tile_size + 2 * overlap should be a power of two
# (254 + 2 = 256) for best OpenSeadragon performance.
DEEPZOOM_TILE_SIZE = 254
DEEPZOOM_OVERLAP = 1
DEEPZOOM_LIMIT_BOUNDS = True

# Tile delivery format and JPEG quality.
TILE_FORMAT = "jpeg"
TILE_QUALITY = 75

# Max number of open slide handles to keep cached.
SLIDE_CACHE_SIZE = 8

# Thumbnail size (longest edge) for the slide list.
THUMBNAIL_SIZE = 256

SLIDES_DIR.mkdir(parents=True, exist_ok=True)
