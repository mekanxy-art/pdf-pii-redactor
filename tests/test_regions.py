import pytest
from PIL import Image
from pii_redactor.regions import parse_regions, Region
from pii_redactor.preview import draw_overlay


def test_parse_basic_and_all_pages():
    r = parse_regions("1;20;30;80;40\n*;0;0;100;10,5\n# Kommentar\n\n")
    assert r[0] == Region(1, 0.2, 0.3, 0.8, 0.4)
    assert r[1].page is None and r[1].y1 == pytest.approx(0.105)


@pytest.mark.parametrize("bad", ["1;20;30;80", "x;1;1;2;2", "0;1;1;2;2", "1;a;1;2;2",
                                 "1;-5;1;2;2", "1;1;1;101;2", "1;50;10;40;20", "1;10;50;20;40"])
def test_parse_rejects_bad_input(bad):
    with pytest.raises(ValueError):
        parse_regions(bad)


def test_draw_overlay_marks_region_red_and_keeps_size():
    img = Image.new("RGB", (200, 100), (255, 255, 255))
    out = draw_overlay(img, parse_regions("1;25;25;75;75"), grid=False)
    assert out.size == (200, 100)
    r, g, b = out.getpixel((100, 50))
    assert r > 200 and g < 200 and b < 200
    assert out.getpixel((5, 5)) == (255, 255, 255)
