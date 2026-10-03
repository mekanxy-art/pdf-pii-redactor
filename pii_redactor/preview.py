"""Seitenvorschau mit Raster und eingezeichneten Schwaerzbereichen (fuer die App)."""
from __future__ import annotations
import io

import pymupdf
from PIL import Image, ImageDraw


def draw_overlay(img: Image.Image, regions, grid: bool = True) -> Image.Image:
    """Zeichnet Raster (alle 10 %) und rote Bereiche auf ein Bild. regions: Objekte mit x0,y0,x1,y1 (Anteile)."""
    base = img.convert("RGBA")
    w, h = base.size
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    if grid:
        for i in range(1, 10):
            x, y = round(w * i / 10), round(h * i / 10)
            d.line([(x, 0), (x, h)], fill=(0, 120, 255, 90), width=1)
            d.line([(0, y), (w, y)], fill=(0, 120, 255, 90), width=1)
            d.text((x + 2, 2), str(i * 10), fill=(0, 90, 220, 255))
            d.text((2, y + 2), str(i * 10), fill=(0, 90, 220, 255))
    for r in regions:
        box = [r.x0 * w, r.y0 * h, r.x1 * w, r.y1 * h]
        d.rectangle(box, fill=(255, 0, 0, 90), outline=(255, 0, 0, 255), width=2)
    return Image.alpha_composite(base, layer).convert("RGB")


def page_count(data: bytes) -> int:
    return len(pymupdf.open(stream=data, filetype="pdf"))


def render_preview(data: bytes, page_no: int, regions, grid: bool = True, width: int = 800) -> Image.Image:
    doc = pymupdf.open(stream=data, filetype="pdf")
    page = doc[page_no - 1]
    zoom = width / page.rect.width
    pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
    img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    return draw_overlay(img, [r for r in regions if r.page in (None, page_no)], grid)
