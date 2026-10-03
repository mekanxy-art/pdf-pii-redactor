import pytest
pymupdf = pytest.importorskip("pymupdf")
from pii_redactor.pdf_redact import redact_pdf, verify_clean


def make_pdf(path, image=False):
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 100), "Name: Max Mustermann")
    page.insert_text((72, 130), "IBAN: DE89 3704 0044 0532 0130 00")
    page.insert_text((72, 160), "Mail: max@example.de, Rechnung 2024")
    if image:
        pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 50, 20), False)
        pix.set_rect(pix.irect, (0, 0, 255))
        page.insert_image(pymupdf.Rect(72, 200, 172, 240), pixmap=pix)
    doc.save(path)


def test_text_really_removed(tmp_path):
    src, dst = str(tmp_path / "a.pdf"), str(tmp_path / "b.pdf")
    make_pdf(src)
    stats = redact_pdf(src, dst, terms=["Mustermann"])
    out = pymupdf.open(dst)[0].get_text()
    assert "Mustermann" not in out and "DE89" not in out and "max@example.de" not in out
    assert "Rechnung" in out
    assert stats["IBAN"] == 1 and stats["EMAIL"] == 1
    assert verify_clean(dst, terms=["Mustermann"]) == []


def test_images_removed(tmp_path):
    src, dst = str(tmp_path / "i.pdf"), str(tmp_path / "j.pdf")
    make_pdf(src, image=True)
    assert len(pymupdf.open(src)[0].get_image_info()) == 1
    stats = redact_pdf(src, dst, remove_images=True)
    assert stats["IMAGE"] == 1
    assert pymupdf.open(dst)[0].get_image_info() == []
    assert "Rechnung" in pymupdf.open(dst)[0].get_text()
    assert verify_clean(dst, check_images=True) == []


def test_manual_region_removes_text_under_it(tmp_path):
    from pii_redactor.regions import parse_regions
    src, dst = str(tmp_path / "m.pdf"), str(tmp_path / "n.pdf")
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 100), "GEHEIMNAME")
    page.insert_text((72, 400), "Sichtbarer Text")
    doc.save(src)
    top = 100 / page.rect.height * 100
    regions = parse_regions(f"1;0;{top - 5:.1f};100;{top + 3:.1f}")
    stats = redact_pdf(src, dst, regions=regions)
    out = pymupdf.open(dst)[0].get_text()
    assert stats["MANUAL"] == 1
    assert "GEHEIMNAME" not in out and "Sichtbarer" in out
