"""FastAPI tile server for the digital pathology viewer.

Serves DeepZoom (.dzi) descriptors and tiles generated on the fly from slides
via OpenSlide, plus slide listing, metadata, thumbnails, and uploads. Also
serves the static frontend.
"""
from __future__ import annotations

import re
from contextlib import asynccontextmanager
from io import BytesIO

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from . import config, slides

cache = slides.SlideCache()

# Tile path pattern: {level}/{col}_{row}.{format}
_TILE_RE = re.compile(r"^(?P<level>\d+)/(?P<col>\d+)_(?P<row>\d+)\.(?P<fmt>jpeg|jpg|png)$")


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    cache.close_all()


app = FastAPI(title="PathViewer Tile Server", lifespan=lifespan)


def _get_handle(slide_id: str) -> slides.SlideHandle:
    try:
        return cache.get(slide_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Slide not found: {slide_id}")
    except Exception as exc:  # noqa: BLE001 - surface open errors to client
        raise HTTPException(status_code=500, detail=f"Failed to open slide: {exc}")


@app.get("/api/slides")
def api_list_slides():
    return slides.list_slides()


@app.get("/api/slides/{slide_id}/metadata")
def api_metadata(slide_id: str):
    handle = _get_handle(slide_id)
    return slides.slide_metadata(handle)


@app.get("/api/slides/{slide_id}/thumbnail")
def api_thumbnail(slide_id: str):
    handle = _get_handle(slide_id)
    img = slides.thumbnail(handle)
    buf = BytesIO()
    img.convert("RGB").save(buf, "jpeg", quality=80)
    return Response(buf.getvalue(), media_type="image/jpeg")


@app.get("/api/slides/{slide_id}.dzi")
def api_dzi(slide_id: str):
    handle = _get_handle(slide_id)
    xml = handle.dz.get_dzi(config.TILE_FORMAT)
    return Response(xml, media_type="application/xml")


@app.get("/api/slides/{slide_id}_files/{tile_path:path}")
def api_tile(slide_id: str, tile_path: str):
    match = _TILE_RE.match(tile_path)
    if not match:
        raise HTTPException(status_code=400, detail="Malformed tile path")
    handle = _get_handle(slide_id)
    level = int(match.group("level"))
    col = int(match.group("col"))
    row = int(match.group("row"))
    try:
        tile = handle.dz.get_tile(level, (col, row))
    except (ValueError, IndexError):
        raise HTTPException(status_code=404, detail="Tile out of range")
    buf = BytesIO()
    tile.save(buf, config.TILE_FORMAT, quality=config.TILE_QUALITY)
    media_type = "image/png" if config.TILE_FORMAT == "png" else "image/jpeg"
    return Response(buf.getvalue(), media_type=media_type)


@app.post("/api/slides/upload")
async def api_upload(file: UploadFile):
    name = (file.filename or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="No filename provided")
    suffix = "." + name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if suffix not in config.SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format {suffix!r}. Allowed: {sorted(config.SUPPORTED_EXTENSIONS)}",
        )
    # Strip any path components from the client-provided name.
    safe_name = name.replace("\\", "/").split("/")[-1]
    dest = config.SLIDES_DIR / safe_name
    with dest.open("wb") as out:
        while chunk := await file.read(1024 * 1024):
            out.write(chunk)
    return {"id": safe_name, "name": dest.stem, "format": suffix.lstrip(".")}


# --- Static frontend --------------------------------------------------------
# Mounted last so API routes take precedence.
if config.FRONTEND_DIR.is_dir():
    @app.get("/", response_class=HTMLResponse)
    def index():
        return FileResponse(config.FRONTEND_DIR / "index.html")

    app.mount("/", StaticFiles(directory=str(config.FRONTEND_DIR), html=True), name="frontend")
