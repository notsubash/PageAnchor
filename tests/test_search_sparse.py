from pageanchor.models import PageHit
from pageanchor.retrieve.sparse import bm25_score, search_bm25


def test_bm25_prefers_term_overlap():
    docs = ["pali gemma vision language", "consumer price index december"]
    scores = [bm25_score("pali gemma", doc, docs) for doc in docs]
    assert scores[0] > scores[1]


def test_search_bm25_collapses_to_pages(monkeypatch, tmp_path):
    rows = [
        {"doc_id": "a", "page": 1, "text": "pali gemma model"},
        {"doc_id": "a", "page": 1, "text": "unrelated"},
        {"doc_id": "a", "page": 2, "text": "consumer price"},
    ]
    monkeypatch.setattr("pageanchor.retrieve.sparse._load_text_rows", lambda uri: rows)
    hits = search_bm25("pali gemma", 5, lancedb_uri=str(tmp_path))
    assert hits[0] == PageHit(doc_id="a", page=1, score=hits[0].score, source="bm25")
    assert hits[0].page == 1
