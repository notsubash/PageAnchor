from __future__ import annotations

from pageanchor.models import PageHit
from pageanchor.retrieve.sparse import search_bm25
from pageanchor.retrieve.text import search_text
from pageanchor.retrieve.visual import search_visual


def rrf_fuse_many(
    hit_lists: list[list[PageHit]],
    k: int = 5,
    k_rrf: int = 60,
) -> list[PageHit]:
    scores: dict[tuple[str, int], float] = {}

    def accumulate(hits: list[PageHit]) -> None:
        seen: set[tuple[str, int]] = set()
        for rank, hit in enumerate(hits, start=1):
            key = (hit.doc_id, hit.page)
            if key in seen:
                continue
            seen.add(key)
            scores[key] = scores.get(key, 0.0) + 1.0 / (k_rrf + rank)

    for hits in hit_lists:
        accumulate(hits)

    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0][0], item[0][1]))
    return [
        PageHit(doc_id=doc_id, page=page, score=score, source="hybrid")
        for (doc_id, page), score in ranked[:k]
    ]


def rrf_fuse(
    text_hits: list[PageHit],
    visual_hits: list[PageHit],
    k: int = 5,
    k_rrf: int = 60,
) -> list[PageHit]:
    return rrf_fuse_many([text_hits, visual_hits], k=k, k_rrf=k_rrf)


def search_hybrid(
    query: str,
    k: int,
    *,
    lancedb_uri: str | None = None,
    embed_query=None,
    embed_visual_query=None,
) -> list[PageHit]:
    fuse_k = max(k, 60)
    text_hits = search_text(query, fuse_k, lancedb_uri=lancedb_uri, embed_query=embed_query)
    visual_hits = search_visual(
        query, fuse_k, lancedb_uri=lancedb_uri, embed_query=embed_visual_query
    )
    bm25_hits = search_bm25(query, fuse_k, lancedb_uri=lancedb_uri)
    return rrf_fuse_many([text_hits, visual_hits, bm25_hits], k=k)
