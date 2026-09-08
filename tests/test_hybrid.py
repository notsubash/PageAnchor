from pageanchor.models import PageHit
from pageanchor.retrieve.hybrid import rrf_fuse


def test_rrf_prefers_pages_in_both_lists():
    text = [
        PageHit(doc_id="a", page=1, score=0.9, source="text"),
        PageHit(doc_id="a", page=2, score=0.8, source="text"),
    ]
    visual = [
        PageHit(doc_id="a", page=2, score=0.7, source="visual"),
        PageHit(doc_id="a", page=3, score=0.6, source="visual"),
    ]
    fused = rrf_fuse(text, visual, k=5)
    assert fused[0].doc_id == "a" and fused[0].page == 2
    assert fused[0].source == "hybrid"


def test_rrf_collapses_duplicate_pages_to_best_rank():
    text = [
        PageHit(doc_id="a", page=1, score=0.99, source="text"),
        PageHit(doc_id="a", page=1, score=0.50, source="text"),
        PageHit(doc_id="a", page=2, score=0.40, source="text"),
    ]
    fused = rrf_fuse(text, [], k=5)
    pages = [(hit.doc_id, hit.page) for hit in fused]
    assert pages == [("a", 1), ("a", 2)]
    assert all(hit.source == "hybrid" for hit in fused)


def test_rrf_respects_k():
    text = [
        PageHit(doc_id="a", page=1, score=0.9, source="text"),
        PageHit(doc_id="a", page=2, score=0.8, source="text"),
        PageHit(doc_id="a", page=3, score=0.7, source="text"),
    ]
    fused = rrf_fuse(text, [], k=2)
    assert len(fused) == 2
