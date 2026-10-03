import pytest
spacy = pytest.importorskip("spacy")
from pii_redactor.detectors import detect, Finding
from pii_redactor.ner import make_ner


def fake_nlp():
    nlp = spacy.blank("de")
    ruler = nlp.add_pipe("entity_ruler")
    ruler.add_patterns([
        {"label": "PER", "pattern": [{"LOWER": "max"}, {"LOWER": "mustermann"}]},
        {"label": "LOC", "pattern": "Muenster"},
        {"label": "ORG", "pattern": "Unhyde"},
    ])
    return nlp


def test_ner_finds_person_and_location_not_org():
    res = detect("Max Mustermann aus Muenster arbeitet bei Unhyde", ner=make_ner(nlp=fake_nlp()))
    got = {(f.type, f.text) for f in res}
    assert ("PERSON", "Max Mustermann") in got and ("LOCATION", "Muenster") in got
    assert not any(f.text == "Unhyde" for f in res)


def test_ner_and_regex_combine():
    res = detect("Max Mustermann, DE89 3704 0044 0532 0130 00", ner=make_ner(nlp=fake_nlp()))
    assert {f.type for f in res} == {"PERSON", "IBAN"}


def test_names_propagate_to_uppercase_heading_and_lastname():
    text = "MAX MUSTERMANN Lebenslauf. Max Mustermann wohnt hier. Herr MUSTERMANN unterschreibt."
    i = text.index("Max Mustermann")
    first_only = lambda t: [Finding(i, i + 14, "PERSON", 0.6, "Max Mustermann")]
    res = [f for f in detect(text, ner=first_only) if f.type == "PERSON"]
    assert {f.text for f in res} == {"MAX MUSTERMANN", "Max Mustermann", "MUSTERMANN"}


def test_propagation_not_on_substrings_and_email_wins():
    text = "Mustermanns Auto, mail max.mustermann@example.de, Max Mustermann"
    i = text.rindex("Max")
    res = detect(text, ner=lambda t: [Finding(i, len(t), "PERSON", 0.6, "Max Mustermann")])
    assert not any(f.text == "Mustermanns" for f in res)
    assert any(f.type == "EMAIL" for f in res)


def test_propagation_from_multiword_custom_term():
    res = detect("MAX MUSTERMANN\nSpaeter Mustermann", terms=["Max Mustermann"])
    assert [f.text for f in res] == ["MAX MUSTERMANN", "Mustermann"]
