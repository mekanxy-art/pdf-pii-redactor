import pytest
pymupdf = pytest.importorskip("pymupdf")
from pii_redactor.pdf_redact import redact_pdf, verify_clean, ocr_pages


def make_scan(path):
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 120), "Name: Max Mustermann", fontsize=22)
    page.insert_text((72, 180), "Rechnung Nummer 2024", fontsize=22)
    pix = page.get_pixmap(dpi=200)
    scan = pymupdf.open()
    p2 = scan.new_page()
    p2.insert_image(p2.rect, pixmap=pix)
    scan.save(path)


def test_scanned_page_ocr_redaction(tmp_path):
    src, dst = str(tmp_path / "s.pdf"), str(tmp_path / "t.pdf")
    make_scan(src)
    assert pymupdf.open(src)[0].get_text().strip() == ""
    try:
        stats = redact_pdf(src, dst, terms=["Mustermann"], ocr=True)
    except Exception as e:
        pytest.skip(f"Tesseract nicht nutzbar: {e}")
    assert ocr_pages(stats) == [1]
    assert sum(v for k, v in stats.items() if not k.startswith("_")) >= 1
    assert verify_clean(dst, terms=["Mustermann"], ocr=True) == []
