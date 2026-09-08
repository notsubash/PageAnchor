from pageanchor.ingest.render import render_pdf


def test_render_hello_pdf_produces_one_png(hello_pdf, tmp_path):
    paths = render_pdf(hello_pdf, tmp_path, dpi=72)
    assert len(paths) == 1
    assert paths[0].name == "p1.png"
    assert paths[0].is_file()
    assert paths[0].stat().st_size > 0
