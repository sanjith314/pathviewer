"""Slide access layer: opening slides, DeepZoom tiling, metadata, thumbnails."""
from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path

from cachetools import LRUCache
from openslide import ImageSlide, OpenSlide, open_slide
from openslide.deepzoom import DeepZoomGenerator
from PIL import Image

from . import config


@dataclass
class SlideHandle:
    """A cached open slide plus its DeepZoom generator."""

    slide: OpenSlide | ImageSlide
    dz: DeepZoomGenerator
    path: Path


class SlideCache:
    """Thread-safe LRU cache of open slide handles keyed by slide id."""

    def __init__(self) -> None:
        self._cache: LRUCache[str, SlideHandle] = LRUCache(maxsize=config.SLIDE_CACHE_SIZE)
        self._lock = threading.Lock()

    def _resolve_path(self, slide_id: str) -> Path:
        # slide_id is the file name (with extension) relative to SLIDES_DIR.
        # Reject anything that tries to escape the slides directory.
        candidate = (config.SLIDES_DIR / slide_id).resolve()
        slides_root = config.SLIDES_DIR.resolve()
        if slides_root not in candidate.parents and candidate != slides_root:
            raise KeyError(slide_id)
        if not candidate.is_file():
            raise KeyError(slide_id)
        if candidate.suffix.lower() not in config.SUPPORTED_EXTENSIONS:
            raise KeyError(slide_id)
        return candidate

    def get(self, slide_id: str) -> SlideHandle:
        with self._lock:
            handle = self._cache.get(slide_id)
            if handle is not None:
                return handle
            path = self._resolve_path(slide_id)
            slide = open_slide(str(path))
            dz = DeepZoomGenerator(
                slide,
                tile_size=config.DEEPZOOM_TILE_SIZE,
                overlap=config.DEEPZOOM_OVERLAP,
                limit_bounds=config.DEEPZOOM_LIMIT_BOUNDS,
            )
            handle = SlideHandle(slide=slide, dz=dz, path=path)
            self._cache[slide_id] = handle
            return handle

    def close_all(self) -> None:
        with self._lock:
            for handle in self._cache.values():
                try:
                    handle.slide.close()
                except Exception:
                    pass
            self._cache.clear()


def list_slides() -> list[dict]:
    """Return lightweight info for every slide file in SLIDES_DIR."""
    slides: list[dict] = []
    for path in sorted(config.SLIDES_DIR.iterdir()):
        if path.is_file() and path.suffix.lower() in config.SUPPORTED_EXTENSIONS:
            slides.append(
                {
                    "id": path.name,
                    "name": path.stem,
                    "format": path.suffix.lower().lstrip("."),
                }
            )
    return slides


def _mpp(slide: OpenSlide | ImageSlide) -> float | None:
    """Microns per pixel (average of x/y) if available."""
    try:
        mpp_x = slide.properties.get("openslide.mpp-x")
        mpp_y = slide.properties.get("openslide.mpp-y")
        if mpp_x and mpp_y:
            return (float(mpp_x) + float(mpp_y)) / 2.0
        if mpp_x:
            return float(mpp_x)
    except (ValueError, TypeError):
        pass
    return None


def slide_metadata(handle: SlideHandle) -> dict:
    slide = handle.slide
    width, height = slide.dimensions
    props = slide.properties

    def prop(key: str):
        value = props.get(key)
        return value if value else None

    return {
        "id": handle.path.name,
        "name": handle.path.stem,
        "format": handle.path.suffix.lower().lstrip("."),
        "width": width,
        "height": height,
        "mpp": _mpp(slide),
        "vendor": prop("openslide.vendor"),
        "objective_power": prop("openslide.objective-power"),
        "level_count": slide.level_count,
        "associated_images": list(slide.associated_images.keys()),
        "dzi_levels": handle.dz.level_count,
    }


def thumbnail(handle: SlideHandle, size: int = config.THUMBNAIL_SIZE) -> Image.Image:
    return handle.slide.get_thumbnail((size, size))
