from pageanchor.ground.verify import verify_quote


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
