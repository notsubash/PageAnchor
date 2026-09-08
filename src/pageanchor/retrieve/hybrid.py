from __future__ import annotations

from pageanchor.models import PageHit


def rrf_fuse(
    text_hits: list[PageHit],
    visual_hits: list[PageHit],
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

    accumulate(text_hits)
    accumulate(visual_hits)

    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0][0], item[0][1]))
    return [
        PageHit(doc_id=doc_id, page=page, score=score, source="hybrid")
        for (doc_id, page), score in ranked[:k]
    ]
