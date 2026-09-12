"""Page-rerank fixtures and retrieve-only diagnostics. No live LanceDB."""

from pageanchor.eval.retrieve import (
    gold_rank,
    recall_at,
    render_retrieve_report,
    rrf_fuse_lists,
    run_retrieve_eval,
)
from pageanchor.models import PageHit
from pageanchor.retrieve.hybrid import rrf_fuse

# --- fixtures reused by later rerank tests ---

COLPALI = "arxiv-2407-colpali"
SLIDES = "nasa-roman-slides"


def hit(doc_id: str, page: int, score: float, source: str = "text") -> PageHit:
    return PageHit(doc_id=doc_id, page=page, score=score, source=source)


DENSE_MISS_TEXT = [
    hit("other-a", 1, 0.9, "text"),
    hit("other-a", 2, 0.8, "text"),
    hit(COLPALI, 21, 0.7, "text"),
]
DENSE_MISS_VISUAL = [
    hit("other-b", 4, 0.9, "visual"),
    hit("other-b", 5, 0.8, "visual"),
    hit(COLPALI, 6, 0.7, "visual"),
]
BM25_GOLD_FIRST = [
    hit(COLPALI, 3, 12.0, "bm25"),
    hit("other-c", 9, 2.0, "bm25"),
    hit("other-c", 10, 1.0, "bm25"),
]
SAME_DOC_HITS = [
    hit(COLPALI, 1, 0.8, "hybrid"),
    hit(COLPALI, 5, 0.7, "hybrid"),
]
FIRST_SLIDE_TIE = [
    hit(SLIDES, 4, 0.9, "hybrid"),
    hit(SLIDES, 1, 0.9, "hybrid"),
]


def test_gold_rank_is_one_based_and_none_when_missing():
    hits = [hit(COLPALI, 21, 0.9), hit(COLPALI, 3, 0.8), hit("x", 1, 0.1)]
    assert gold_rank(hits, COLPALI, [3]) == 2
    assert gold_rank(hits, COLPALI, [9]) is None


def test_recall_at_counts_ranks_inside_k():
    ranks = [3, 8, None, 20]
    assert recall_at(ranks, 5) == 0.25
    assert recall_at(ranks, 10) == 0.5
    assert recall_at(ranks, 20) == 0.75
    assert recall_at([], 5) == 0.0


def test_rrf_fuse_lists_matches_two_list_rrf_fuse():
    fused = rrf_fuse_lists([DENSE_MISS_TEXT, DENSE_MISS_VISUAL], k=5)
    baseline = rrf_fuse(DENSE_MISS_TEXT, DENSE_MISS_VISUAL, k=5)
    assert [(h.doc_id, h.page) for h in fused] == [(h.doc_id, h.page) for h in baseline]


def test_three_way_rrf_recovers_page_only_bm25_ranks():
    two = rrf_fuse_lists([DENSE_MISS_TEXT, DENSE_MISS_VISUAL], k=5)
    three = rrf_fuse_lists([DENSE_MISS_TEXT, DENSE_MISS_VISUAL, BM25_GOLD_FIRST], k=5)
    assert gold_rank(two, COLPALI, [3]) is None
    assert gold_rank(three, COLPALI, [3]) is not None


def test_run_retrieve_eval_writes_recall_table(tmp_path):
    gold = tmp_path / "gold.jsonl"
    gold.write_text(
        "\n".join(
            [
                '{"id": "h001", "question": "q1", "answerable": true, '
                '"gold_doc_id": "arxiv-2407-colpali", "gold_pages": [3]}',
                '{"id": "h013", "question": "skip", "answerable": false, '
                '"gold_doc_id": null, "gold_pages": []}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    def fake_text(query, k, **kwargs):
        return DENSE_MISS_TEXT[:k]

    def fake_visual(query, k, **kwargs):
        return DENSE_MISS_VISUAL[:k]

    def fake_hybrid(query, k, **kwargs):
        return rrf_fuse(DENSE_MISS_TEXT, DENSE_MISS_VISUAL, k=k)

    def fake_bm25(query, k, **kwargs):
        return BM25_GOLD_FIRST[:k]

    out = tmp_path / "out"
    payload = run_retrieve_eval(
        str(gold),
        str(out),
        searches={
            "text": fake_text,
            "visual": fake_visual,
            "hybrid": fake_hybrid,
            "bm25": fake_bm25,
        },
    )
    assert payload["n_answerable"] == 1
    assert payload["rows"][0]["id"] == "h001"
    assert payload["rows"][0]["ranks"]["bm25"] == 1
    assert payload["rows"][0]["ranks"]["text"] is None
    assert payload["rows"][0]["ranks"]["rrf3"] is not None
    assert payload["recall"]["bm25"]["at_20"] == 1.0
    assert payload["recall"]["rrf3"]["at_5"] == 1.0
    report = (out / "report.md").read_text(encoding="utf-8")
    assert "Recall@5" in report
    assert "rrf3" in report
    assert "h001" in report
    assert render_retrieve_report(payload) == report
    assert (out / "ranks.json").is_file()
