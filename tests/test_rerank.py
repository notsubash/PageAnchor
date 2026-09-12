"""Page-rerank fixtures and retrieve-only diagnostics. No live LanceDB."""

from pageanchor.eval.retrieve import (
    gold_rank,
    recall_at,
    render_retrieve_report,
    rrf_fuse_lists,
    run_retrieve_eval,
)
from pageanchor.models import PageHit, RetrievalMode
from pageanchor.retrieve.hybrid import rrf_fuse
from pageanchor.retrieve.rerank import (
    POOL_K,
    cue_boost,
    expand_same_doc,
    rerank_pages,
)

# --- fixtures reused by later rerank tests ---

COLPALI = "arxiv-2407-colpali"
SLIDES = "nasa-roman-slides"


def hit(doc_id: str, page: int, score: float, source: RetrievalMode = "text") -> PageHit:
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


def test_expand_same_doc_injects_middle_page():
    expanded = expand_same_doc(SAME_DOC_HITS, window=2)
    pages = {(h.doc_id, h.page) for h in expanded}
    assert (COLPALI, 3) in pages
    assert (COLPALI, 1) in pages
    assert (COLPALI, 5) in pages


def test_expand_does_not_flood_existing_page_scores():
    hits = [
        hit(COLPALI, 21, 0.9, "hybrid"),
        hit(COLPALI, 3, 0.5, "bm25"),
    ]
    expanded = expand_same_doc(hits, window=2)
    by_page = {(h.doc_id, h.page): h for h in expanded}
    assert by_page[(COLPALI, 3)].score == 0.5
    ranked = rerank_pages("unrelated question", expanded)
    top5 = {(h.doc_id, h.page) for h in ranked[:5]}
    assert (COLPALI, 3) in top5


def test_expand_lifts_neighbors_when_page_one_hit():
    hits = [
        hit(COLPALI, 1, 0.8, "hybrid"),
        hit(COLPALI, 3, 0.3, "bm25"),
        hit("other-a", 1, 0.7, "text"),
        hit("other-b", 1, 0.6, "text"),
    ]
    expanded = expand_same_doc(hits, window=2)
    by_page = {(h.doc_id, h.page): h for h in expanded}
    assert by_page[(COLPALI, 3)].score == 0.8 - 3e-6
    ranked = rerank_pages("unrelated question", expanded)
    top5 = {(h.doc_id, h.page) for h in ranked[:5]}
    assert (COLPALI, 3) in top5


def test_expand_does_not_lower_existing_page_score():
    hits = [
        hit(COLPALI, 1, 0.4, "hybrid"),
        hit(COLPALI, 3, 0.9, "bm25"),
    ]
    expanded = expand_same_doc(hits, window=2)
    by_page = {(h.doc_id, h.page): h for h in expanded}
    assert by_page[(COLPALI, 3)].score == 0.9


def test_cue_boost_table_phrase_when_text_matches():
    question = "What does Table 2 show?"
    assert (
        cue_boost(question, hit(COLPALI, 7, 0.5), ["Results for Table 2 are here"])
        == 1.0
    )
    assert cue_boost(question, hit(COLPALI, 7, 0.5), ["No tables here"]) == 0.0


def test_rerank_pages_table_cue_beats_small_rrf_gap():
    question = "What does Table 2 show?"
    hits = [
        hit(COLPALI, 6, 0.51, "hybrid"),
        hit(COLPALI, 7, 0.50, "hybrid"),
    ]
    page_text = {(COLPALI, 7): "Table 2 results"}
    ranked = rerank_pages(question, hits, page_text=page_text)
    assert ranked[0].page == 7


def test_rerank_pages_first_slide_beats_higher_raw_score():
    question = "What is the title on the first slide?"
    hits = [
        hit(SLIDES, 4, 0.9, "hybrid"),
        hit(SLIDES, 1, 0.5, "hybrid"),
    ]
    ranked = rerank_pages(question, hits)
    assert ranked[0].page == 1


def test_cue_boost_first_slide_question():
    question = "What is the title on the first slide?"
    assert cue_boost(question, hit(SLIDES, 1, 0.5), []) == 1.0
    assert cue_boost(question, hit(SLIDES, 4, 0.5), []) == 0.0


def test_rerank_pages_prefers_earlier_page_on_score_tie():
    ranked = rerank_pages("unrelated question", FIRST_SLIDE_TIE)
    assert ranked[0].page == 1
    assert ranked[1].page == 4


def test_rerank_pages_first_slide_cue_ranks_page_one():
    question = "What is the title on the first slide?"
    ranked = rerank_pages(question, FIRST_SLIDE_TIE)
    assert ranked[0].page == 1


def test_pool_k_is_twenty():
    assert POOL_K == 20


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
