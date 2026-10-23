"""Echte PDF-Schwaerzung mit PyMuPDF (Text wird entfernt, nicht nur ueberdeckt). Optional OCR und manuelle Bereiche."""
from __future__ import annotations
import json
import os
from collections import Counter
from pathlib import Path
from typing import Iterable

import pymupdf

from .detectors import detect

MAX_PASSES = 3
OCR_PASSES = 2
OCR_LANG = "deu+eng"
OCR_DPI = 300
MIN_TEXT_CHARS = 20
LARGE_IMAGE_SHARE = 0.6
DEFAULT_TESSDATA = r"C:\Program Files\Tesseract-OCR\tessdata"


def _get_ner(use_ner: bool):
    if not use_ner:
        return None
    from .ner import make_ner
    return make_ner()


def _tessdata():
    p = os.environ.get("TESSDATA_PREFIX")
    if p and os.path.isdir(p):
        return p
    if os.path.isdir(DEFAULT_TESSDATA):
        return DEFAULT_TESSDATA
    return None


def _build_map(words):
    parts, spans, pos = [], [], 0
    for i, w in enumerate(words):
        sep = " " if i else ""
        pos += len(sep)
        parts.append(sep + w[4])
        spans.append((pos, pos + len(w[4]), i))
        pos += len(w[4])
    return "".join(parts), spans


def _extract(page, ocr: bool):
    """Liefert (text, spans, words, ocr_benutzt). OCR nur bei Seiten ohne (genug) Textlayer, aber mit Bild."""
    words = page.get_text("words", sort=True)
    used = False
    if ocr and sum(len(w[4]) for w in words) < MIN_TEXT_CHARS and page.get_image_info():
        tp = page.get_textpage_ocr(language=OCR_LANG, dpi=OCR_DPI, full=True, tessdata=_tessdata())
        words = page.get_text("words", textpage=tp, sort=True)
        used = True
    text, spans = _build_map(words)
    return text, spans, words, used


def _image_rects(page, keep_large: bool):
    """Bild-Rechtecke. Bei keep_large bleiben seitenfuellende Bilder (Scans) unberuehrt."""
    page_area = page.rect.get_area()
    out = []
    for info in page.get_image_info():
        r = pymupdf.Rect(info["bbox"])
        if keep_large and r.get_area() >= LARGE_IMAGE_SHARE * page_area:
            continue
        out.append(r)
    return out


def ocr_pages(stats) -> list[int]:
    return sorted(int(k.rsplit("_", 1)[1]) for k in stats if k.startswith("_ocr_page_"))


def _apply_regions(page, regions, fill, stats):
    """Manuelle Bereiche (Anteile der sichtbaren Seite). derotation_matrix beachtet gedrehte Seiten."""
    rs = [r for r in regions if r.page in (None, page.number + 1)]
    if not rs:
        return
    pr = page.rect
    for r in rs:
        rect = pymupdf.Rect(pr.x0 + r.x0 * pr.width, pr.y0 + r.y0 * pr.height,
                            pr.x0 + r.x1 * pr.width, pr.y0 + r.y1 * pr.height)
        page.add_redact_annot((rect * page.derotation_matrix).normalize(), fill=fill)
        stats["MANUAL"] += 1
    page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_PIXELS)


def redact_pdf(src: str, dst: str, terms: Iterable[str] = (), types=None,
               fill=(0, 0, 0), report: str | None = None, use_ner: bool = False,
               remove_images: bool = False, ocr: bool = False, regions=None) -> Counter:
    """Mehrere Durchgaenge pro Seite, bis nichts Neues gefunden wird.
    ocr=True: Scanseiten werden per Tesseract gelesen und nur die sensiblen Bildbereiche geschwaerzt.
    remove_images + ocr: nur kleine Bilder (Foto, Unterschrift, Logo) werden entfernt, Scans bleiben.
    regions: manuelle Bereiche (Region-Objekte aus regions.parse_regions)."""
    stats: Counter = Counter()
    ner = _get_ner(use_ner)
    with pymupdf.open(src) as doc:
        if doc.needs_pass:
            raise ValueError("PDF ist passwortgeschuetzt")
        for page in doc:
            if regions:
                _apply_regions(page, regions, fill, stats)
            limit, rnd = MAX_PASSES, 0
            while rnd < limit:
                first = rnd == 0
                rnd += 1
                text, spans, words, used_ocr = _extract(page, ocr)
                if first:
                    if used_ocr:
                        stats[f"_ocr_page_{page.number + 1}"] = 1
                        limit = OCR_PASSES
                    elif not text.strip():
                        stats["_pages_without_text_layer"] += 1
                findings = detect(text, terms=terms, types=types, ner=ner)
                rects = _image_rects(page, keep_large=ocr) if (remove_images and first) else []
                if not findings and not rects:
                    break
                if rects:
                    for r in rects:
                        page.add_redact_annot(r, fill=fill)
                        stats["IMAGE"] += 1
                    page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_REMOVE)
                if findings:
                    for f in findings:
                        for s, e, idx in spans:
                            if s < f.end and f.start < e:
                                page.add_redact_annot(pymupdf.Rect(words[idx][:4]), fill=fill)
                        stats[f.type] += 1
                    page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_PIXELS)
        doc.set_metadata({})
        doc.del_xml_metadata()
        for i in range(doc.embfile_count() - 1, -1, -1):
            doc.embfile_del(i)
        doc.save(dst, garbage=4, deflate=True, clean=True)
    if report:
        Path(report).write_text(json.dumps({k: v for k, v in stats.items() if not k.startswith("_")}, indent=2),
                                encoding="utf-8")
    return stats


def verify_clean(path: str, terms: Iterable[str] = (), use_ner: bool = False,
                 check_images: bool = False, ocr: bool = False) -> list:
    """Liste (Seite, Typ, Text) der Resttreffer. Mit ocr=True werden auch Scanseiten per OCR geprueft."""
    ner = _get_ner(use_ner)
    with pymupdf.open(path) as doc:
        leftovers = []
        for n, page in enumerate(doc, 1):
            text, _, _, _ = _extract(page, ocr)
            for f in detect(text, terms=terms, ner=ner):
                leftovers.append((n, f.type, f.text))
            if check_images and _image_rects(page, keep_large=ocr):
                leftovers.append((n, "IMAGE", "<Bild>"))
    return leftovers


def pages_without_text(path: str) -> list[int]:
    """Seitennummern ohne Textlayer (Scans/Bilder)."""
    with pymupdf.open(path) as doc:
        return [n for n, page in enumerate(doc, 1) if not page.get_text().strip()]
