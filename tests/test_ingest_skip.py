from pathlib import Path

from pageanchor.ingest import ingest_document, pdf_sha256


def test_ingest_skips_when_pdf_hash_and_artifacts_exist(hello_pdf, tmp_path, monkeypatch):
    monkeypatch.setenv("PAGEANCHOR_CORPUS_ROOT", str(tmp_path))
    monkeypatch.setenv("LANCEDB_URI", str(tmp_path / "lancedb"))
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()
    dest = pdf_dir / "hello.pdf"
    dest.write_bytes(hello_pdf.read_bytes())
    digest = pdf_sha256(dest)
    doc = {
        "id": "hello",
        "path": "pdfs/hello.pdf",
        "pages": 1,
        "sha256": digest,
    }

    def boom(*args, **kwargs):
        raise AssertionError("embed should not run on skip")

    first = ingest_document(doc, tmp_path, embed=lambda texts: [[1.0, 0.0]] * len(texts))
    assert first["skipped"] is False
    second = ingest_document(doc, tmp_path, embed=boom)
    assert second["skipped"] is True
    assert (tmp_path / "pages" / "hello" / "p1.png").is_file()
    assert Path(tmp_path / "regions" / "hello.json").is_file()

    def visual_embed(paths):
        return [[[1.0, 0.0]] for _ in paths]

    with_visual = ingest_document(
        doc, tmp_path, embed=boom, visual=True, visual_embed=visual_embed
    )
    assert with_visual["skipped"] is False
    skipped_visual = ingest_document(
        doc, tmp_path, embed=boom, visual=True, visual_embed=boom
    )
    assert skipped_visual["skipped"] is True
