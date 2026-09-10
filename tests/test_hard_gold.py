import json
from pathlib import Path

import pytest

from pageanchor.ground.verify import verify_quote

HARD = Path("corpus/eval/hard_questions.jsonl")
REGIONS = Path("corpus/regions")
ALLOWED = {
    "lexical_gap",
    "table_cell",
    "figure_only",
    "layout",
    "adversarial_unanswerable",
}


def _rows() -> list[dict]:
    return [
        json.loads(line)
        for line in HARD.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_hard_gold_schema():
    rows = _rows()
    assert len(rows) >= 16
    ids = [row["id"] for row in rows]
    assert len(ids) == len(set(ids))
    for row in rows:
        assert row["type"] in ALLOWED
        assert isinstance(row["answerable"], bool)
        if row["answerable"]:
            assert row["gold_doc_id"]
            assert row["gold_pages"]
            assert row["gold_quote"]
            assert row["gold_answer"]
        else:
            assert row["gold_doc_id"] is None
            assert row["gold_pages"] == []
            assert row["gold_quote"] == ""


@pytest.mark.skipif(
    not (REGIONS / "arxiv-2407-colpali.json").is_file(),
    reason="corpus regions not on disk",
)
def test_hard_gold_quotes_are_on_gold_pages():
    for row in _rows():
        if not row["answerable"]:
            continue
        path = REGIONS / f"{row['gold_doc_id']}.json"
        regions = json.loads(path.read_text(encoding="utf-8"))
        pages = set(row["gold_pages"])
        assert any(
            region["page"] in pages and verify_quote(row["gold_quote"], region["text"])
            for region in regions
        ), row["id"]
