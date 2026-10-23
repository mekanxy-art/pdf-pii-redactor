"""Exercise the real installed German model, not only a mocked recognizer."""
import pytest
pytest.importorskip('de_core_news_md')
import pymupdf
from pii_redactor.pdf_redact import redact_pdf, verify_clean


def test_installed_german_model_redacts_name_and_location(tmp_path):
    source, target = tmp_path/'source.pdf', tmp_path/'redacted.pdf'
    with pymupdf.open() as document:
        page = document.new_page()
        page.insert_text((72, 72), 'Angela Merkel lebt in Berlin.')
        page.insert_text((72, 110), 'Die Rechnung wurde bezahlt.')
        document.save(source)
    stats = redact_pdf(str(source), str(target), use_ner=True)
    with pymupdf.open(target) as document:
        text = ''.join(page.get_text() for page in document)
    assert 'Merkel' not in text and 'Berlin' not in text
    assert 'bezahlt' in text
    assert stats['PERSON'] >= 1 and stats['LOCATION'] >= 1
    assert verify_clean(str(target), use_ner=True) == []
