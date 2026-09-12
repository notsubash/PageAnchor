from pageanchor.cli import main


def test_ask_missing_lancedb_prints_ingest_hint(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("LANCEDB_URI", str(tmp_path / "missing-lancedb"))
    monkeypatch.setenv("PAGEANCHOR_CORPUS_ROOT", str(tmp_path))
    code = main(["ask", "hello", "--mode", "text"])
    assert code == 1
    err = capsys.readouterr().err
    assert "LanceDB not found" in err
    assert "pageanchor ingest" in err


def test_eval_retrieve_only_skips_generator(monkeypatch, tmp_path):
    seen = {}

    def fake_retrieve(gold, out, **kwargs):
        seen["gold"] = gold
        seen["out"] = out
        return {"n_answerable": 0, "recall": {}}

    monkeypatch.setattr("pageanchor.eval.retrieve.run_retrieve_eval", fake_retrieve)
    out = tmp_path / "retrieve"
    argv = [
        "eval",
        "--gold",
        "corpus/eval/hard_questions.jsonl",
        "--retrieve-only",
        "--out",
        str(out),
    ]
    assert main(argv) == 0
    assert seen["gold"] == "corpus/eval/hard_questions.jsonl"
    assert seen["out"] == str(out)


def test_ingest_visual_flag_is_passed(monkeypatch):
    seen = {}

    def fake_ingest_all(**kwargs):
        seen.update(kwargs)
        return iter([])

    monkeypatch.setattr("pageanchor.ingest.ingest_all", fake_ingest_all)
    assert main(["ingest", "--all", "--visual"]) == 0
    assert seen["visual"] is True
    assert seen["all_docs"] is True
