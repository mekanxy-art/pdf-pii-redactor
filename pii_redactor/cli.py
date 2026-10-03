import argparse, sys
from .pdf_redact import redact_pdf, verify_clean, pages_without_text, ocr_pages
from .regions import parse_regions


def main(argv=None):
    p = argparse.ArgumentParser(description="Sensible Daten in PDFs dauerhaft schwaerzen")
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--term", action="append", default=[], help="Eigener Begriff (mehrfach moeglich)")
    p.add_argument("--ner", action="store_true", help="Namen/Orte per spaCy erkennen")
    p.add_argument("--ocr", action="store_true", help="Scanseiten per Tesseract-OCR lesen und schwaerzen")
    p.add_argument("--remove-images", action="store_true", help="Bilder entfernen (mit --ocr nur kleine: Foto, Unterschrift)")
    p.add_argument("--region", action="append", default=[],
                   help="Manueller Bereich 'Seite;links;oben;rechts;unten' in Prozent (Seite oder *), mehrfach moeglich")
    p.add_argument("--report", help="JSON-Report (nur Typ + Anzahl)")
    a = p.parse_args(argv)
    regions = parse_regions("\n".join(a.region))
    stats = redact_pdf(a.input, a.output, terms=a.term, report=a.report, use_ner=a.ner,
                       remove_images=a.remove_images, ocr=a.ocr, regions=regions)
    left = verify_clean(a.output, terms=a.term, use_ner=a.ner, check_images=a.remove_images, ocr=a.ocr)
    print("Geschwaerzt:", {k: v for k, v in stats.items() if not k.startswith("_")})
    done = ocr_pages(stats)
    if done:
        print(f"OCR angewendet auf Seiten: {done}")
    uncovered = [n for n in pages_without_text(a.input) if n not in done]
    if uncovered:
        print(f"WARNUNG: Seiten ohne Text, nicht verarbeitet: {uncovered} (--ocr oder --region verwenden)")
    if left:
        print("PRUEFEN: Moegliche Resttreffer (Seite, Typ, Text):")
        for item in left:
            print("  ", item)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
