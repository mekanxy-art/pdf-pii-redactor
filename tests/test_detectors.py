from pii_redactor.detectors import detect, iban_valid, luhn_valid, steuer_id_valid


def types(text, **kw):
    return {(f.type, f.text) for f in detect(text, **kw)}


def test_iban_valid_and_invalid():
    assert iban_valid("DE89 3704 0044 0532 0130 00")
    assert not iban_valid("DE89 3704 0044 0532 0130 01")
    assert ("IBAN", "DE89 3704 0044 0532 0130 00") in types("Konto: DE89 3704 0044 0532 0130 00 bitte")
    assert not [f for f in detect("Konto: DE89 3704 0044 0532 0130 01") if f.type == "IBAN"]


def test_credit_card_luhn():
    assert luhn_valid("4111 1111 1111 1111")
    assert not luhn_valid("4111 1111 1111 1112")
    assert any(t == "CREDIT_CARD" for t, _ in types("Karte 4111 1111 1111 1111"))


def test_steuer_id():
    assert steuer_id_valid("65929970489")
    assert not steuer_id_valid("65929970480")
    assert not steuer_id_valid("01234567890")


def test_email_and_phone():
    t = types("Mail max.mustermann@example.de oder Tel +49 251 123456")
    assert ("EMAIL", "max.mustermann@example.de") in t
    assert any(x == "PHONE" for x, _ in t)


def test_no_false_positive_on_plain_numbers():
    assert detect("Rechnung 2024, Menge 12, Preis 19,99 EUR") == []


def test_custom_terms_case_insensitive():
    assert any(f.type == "CUSTOM_TERM" for f in detect("hallo MAX Mustermann", terms=["max mustermann"]))


def test_overlap_resolution_iban_not_also_phone():
    assert [f.type for f in detect("DE89 3704 0044 0532 0130 00")] == ["IBAN"]


def test_email_beats_custom_term_in_report():
    assert [f.type for f in detect("max.mustermann@example.de", terms=["mustermann"])] == ["EMAIL"]
