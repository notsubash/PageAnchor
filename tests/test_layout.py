from pageanchor.ingest.layout import extract_regions


def test_extract_regions_keeps_hello_token(hello_pdf):
    regions = extract_regions(hello_pdf, "hello")
    pages = {region.page for region in regions}
    assert pages == {1}
    blob = " ".join(region.text for region in regions)
    assert "THE_TOKEN_42" in blob
    for region in regions:
        x0, y0, x1, y1 = region.bbox
        assert 0.0 <= x0 < x1 <= 1.0
        assert 0.0 <= y0 < y1 <= 1.0
