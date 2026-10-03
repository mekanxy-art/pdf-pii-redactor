"""Lokale Web-Oberflaeche: streamlit run app.py"""
import tempfile
from pathlib import Path

import streamlit as st

from pii_redactor.pdf_redact import redact_pdf, verify_clean, pages_without_text, ocr_pages
from pii_redactor.preview import page_count, render_preview
from pii_redactor.regions import parse_regions

st.set_page_config(page_title="PII Redactor")
st.title("PDF-Schwaerzung")
st.caption("Laeuft komplett lokal auf deinem Rechner - nichts wird hochgeladen.")

file = st.file_uploader("PDF auswaehlen", type="pdf")
terms_raw = st.text_area("Eigene Begriffe (einer pro Zeile, z. B. Namen)")
use_ner = st.checkbox("Namen und Orte automatisch erkennen (spaCy)", value=False)
use_ocr = st.checkbox("Gescannte Seiten per OCR lesen und schwaerzen (langsamer)", value=False)
remove_images = st.checkbox(
    "Bilder entfernen (Foto, Unterschrift, Logos)", value=False,
    help="Mit OCR werden nur kleine Bilder entfernt, ganze Scanseiten bleiben lesbar. "
         "Ohne OCR werden ALLE Bilder entfernt, Scanseiten werden dann komplett schwarz.")

regions = []
if file:
    data = file.getvalue()
    try:
        n_pages = page_count(data)
    except Exception as e:
        st.error(f"PDF konnte nicht gelesen werden: {e}")
        st.stop()
    with st.expander("Manuelle Bereiche schwaerzen (optional)"):
        st.caption("Eine Zeile pro Bereich: Seite;links;oben;rechts;unten (Prozent der Seite, "
                   "Seite = Zahl oder * fuer alle). Beispiel: 1;20;30;80;40")
        regions_text = st.text_area("Bereiche", placeholder="1;20;30;80;40", key="regions_text")
        c1, c2 = st.columns(2)
        page_no = c1.number_input("Vorschau-Seite", min_value=1, max_value=n_pages, value=1, step=1)
        grid = c2.checkbox("Raster (alle 10 %)", value=True)
        try:
            regions = parse_regions(regions_text)
        except ValueError as e:
            st.error(str(e))
            regions = None
        if regions is not None:
            st.image(render_preview(data, int(page_no), regions, grid))

if file and st.button("Schwaerzen", type="primary"):
    if regions is None:
        st.error("Bitte zuerst die manuellen Bereiche korrigieren.")
        st.stop()
    terms = [t for t in terms_raw.splitlines() if t.strip()]
    with tempfile.TemporaryDirectory() as tmp:
        src, dst = Path(tmp, "in.pdf"), Path(tmp, "out.pdf")
        src.write_bytes(file.getvalue())
        try:
            with st.spinner("Wird verarbeitet ... (OCR kann pro Seite einige Sekunden dauern)"):
                stats = redact_pdf(str(src), str(dst), terms=terms, use_ner=use_ner,
                                   remove_images=remove_images, ocr=use_ocr, regions=regions)
                left = verify_clean(str(dst), terms=terms, use_ner=use_ner,
                                    check_images=remove_images, ocr=use_ocr)
            no_text = pages_without_text(str(src))
        except Exception as e:
            st.error(f"Fehler: {e}")
            st.stop()
        data_out = dst.read_bytes()
    st.success("Fertig")
    st.json({k: v for k, v in stats.items() if not k.startswith("_")})
    done = ocr_pages(stats)
    if done:
        st.info(f"OCR angewendet auf Seiten: {done}. Bitte diese Seiten besonders pruefen.")
    uncovered = [n for n in no_text if n not in done]
    if uncovered:
        st.warning(f"Seiten ohne Text, nicht verarbeitet: {uncovered}. OCR-Haken oder manuellen Bereich nutzen.")
    if left:
        st.error("Moegliche Resttreffer - bitte pruefen (wird nur hier lokal angezeigt):")
        st.table([{"Seite": n, "Typ": t, "Text": x} for n, t, x in left])
    st.download_button("Geschwaerzte PDF laden", data_out, file_name=f"geschwaerzt_{file.name}",
                       mime="application/pdf")
    st.info("Bitte stichprobenartig manuell pruefen.")
