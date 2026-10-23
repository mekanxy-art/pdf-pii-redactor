"""PDF handles must be released on success and on failed name detection."""
import pytest
import pymupdf
import pii_redactor.pdf_redact as module
from pii_redactor import ner


@pytest.mark.parametrize('operation', ['redact', 'verify'])
def test_missing_model_releases_input_pdf(tmp_path, monkeypatch, operation):
    source = tmp_path / 'input.pdf'
    with pymupdf.open() as document:
        document.new_page().insert_text((72, 72), 'Max Mustermann wohnt in Berlin.')
        document.save(source)
    opened = []
    original = pymupdf.open
    def tracking_open(*args, **kwargs):
        document = original(*args, **kwargs)
        opened.append(document)
        return document
    def missing_model():
        raise RuntimeError('Kein deutsches spaCy-Modell gefunden')
    monkeypatch.setattr(module.pymupdf, 'open', tracking_open)
    monkeypatch.setattr(ner, 'load_model', missing_model)
    with pytest.raises(RuntimeError, match='spaCy-Modell'):
        if operation == 'redact':
            module.redact_pdf(str(source), str(tmp_path/'out.pdf'), use_ner=True)
        else:
            module.verify_clean(str(source), use_ner=True)
    assert opened and all(document.is_closed for document in opened)
    source.unlink()  # Windows rejects this if a handle leaked.


@pytest.mark.parametrize('operation', ['redact', 'verify', 'pages'])
def test_success_releases_input_pdf(tmp_path, monkeypatch, operation):
    source = tmp_path / 'input.pdf'
    with pymupdf.open() as document:
        document.new_page().insert_text((72, 72), 'Unkritischer Text bleibt erhalten.')
        document.save(source)
    opened = []
    original = pymupdf.open
    def tracking_open(*args, **kwargs):
        document = original(*args, **kwargs)
        opened.append(document)
        return document
    monkeypatch.setattr(module.pymupdf, 'open', tracking_open)
    if operation == 'redact':
        module.redact_pdf(str(source), str(tmp_path/'out.pdf'))
    elif operation == 'verify':
        module.verify_clean(str(source))
    else:
        assert module.pages_without_text(str(source)) == []
    assert opened and all(document.is_closed for document in opened)
    source.unlink()
