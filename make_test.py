import pymupdf

doc = pymupdf.open()
page = doc.new_page()
lines = [
    "MAX MUSTERMANN - Lebenslauf",
    "Rechnung 2024 - Max Mustermann aus Muenster",
    "IBAN: DE89 3704 0044 0532 0130 00",
    "Mail: max.mustermann@example.de",
    "Tel: +49 251 123456",
    "Karte: 4111 1111 1111 1111",
    "Betrag: 19,99 EUR",
]
for i, line in enumerate(lines):
    page.insert_text((72, 100 + i * 30), line, fontsize=12)
pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 120, 40), False)
pix.set_rect(pix.irect, (30, 30, 160))
page.insert_image(pymupdf.Rect(72, 340, 192, 380), pixmap=pix)
page.insert_text((72, 400), "(blauer Kasten = Platzhalter fuer Unterschrift/Foto)", fontsize=9)
doc.save("test.pdf")
