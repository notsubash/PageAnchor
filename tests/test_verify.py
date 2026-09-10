from pageanchor.ground.verify import answer_in_quote, verify_quote


def test_verify_collapses_whitespace():
    assert verify_quote("ViDoRe  benchmark", "Visual  ViDoRe benchmark here") is True


def test_verify_is_case_sensitive():
    assert verify_quote("ViDoRe", "vidore") is False


def test_verify_rejects_paraphrase():
    assert verify_quote("18.2%", "about eighteen percent") is False


def test_verify_nfkc_and_preserves_case():
    # U+FB01 LATIN SMALL LIGATURE FI → "fi" under NFKC; case still matters.
    assert verify_quote("file", "A ﬁle") is True
    assert verify_quote("File", "A ﬁle") is False


def test_verify_rejects_empty_quote():
    assert verify_quote("   ", "some region text") is False


def test_answer_in_quote_requires_substring():
    assert answer_in_quote("8.5k", "CoLA 8.5k train") is True
    assert answer_in_quote("8.5k", "Single-Task Training") is False


def test_answer_in_quote_rejects_empty_or_none():
    assert answer_in_quote(None, "CoLA 8.5k") is False
    assert answer_in_quote("   ", "CoLA 8.5k") is False


def test_answer_in_quote_uses_same_normalize_as_quote_verify():
    assert answer_in_quote("ViDoRe  benchmark", "Visual ViDoRe benchmark here") is True
    assert answer_in_quote("ViDoRe", "vidore") is False
