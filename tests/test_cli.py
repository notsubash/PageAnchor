from pageanchor.cli import main


def test_ask_missing_lancedb_prints_ingest_hint(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("LANCEDB_URI", str(tmp_path / "missing-lancedb"))
    monkeypatch.setenv("PAGEANCHOR_CORPUS_ROOT", str(tmp_path))
    code = main(["ask", "hello", "--mode", "text"])
    assert code == 1
    err = capsys.readouterr().err
    assert "LanceDB not found" in err
    assert "pageanchor ingest" in err
