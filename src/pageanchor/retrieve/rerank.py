from __future__ import annotations

import re

from pageanchor.models import PageHit

POOL_K = 20

_TABLE_RE = re.compile(r"table\s+(\d+)", re.IGNORECASE)
_ALGO_RE = re.compile(r"algorithm\s+(\d+)", re.IGNORECASE)
_FIRST_SLIDE_PHRASES = ("first slide", "title on the first")


def expand_same_doc(hits: list[PageHit], *, window: int = 2) -> list[PageHit]:
    by_key: dict[tuple[str, int], PageHit] = {}
    original_keys: set[tuple[str, int]] = set()
    for hit in hits:
        key = (hit.doc_id, hit.page)
        original_keys.add(key)
        existing = by_key.get(key)
        if existing is None or hit.score > existing.score:
            by_key[key] = hit

    for hit in hits:
        for page in range(hit.page - window, hit.page + window + 1):
            if page < 1:
                continue
            key = (hit.doc_id, page)
            if key in by_key:
                continue
            by_key[key] = PageHit(
                doc_id=hit.doc_id,
                page=page,
                score=hit.score * 0.01,
                source=hit.source,
            )

    for hit in hits:
        if hit.page != 1:
            continue
        page1_score = by_key[(hit.doc_id, 1)].score
        for page in (2, 3):
            key = (hit.doc_id, page)
            if key not in original_keys:
                continue
            existing = by_key[key]
            lifted = page1_score - 1e-6 * page
            if lifted > existing.score:
                by_key[key] = PageHit(
                    doc_id=existing.doc_id,
                    page=existing.page,
                    score=lifted,
                    source=existing.source,
                )

    return list(by_key.values())


def cue_boost(
    question: str,
    hit: PageHit,
    region_texts: list[str],
) -> float:
    q = question.lower()
    boost = 0.0

    for pattern, label in ((_TABLE_RE, "table"), (_ALGO_RE, "algorithm")):
        match = pattern.search(q)
        if match is not None:
            phrase = f"{label} {match.group(1)}"
            if any(phrase in text.lower() for text in region_texts):
                boost += 1.0
                break

    if any(phrase in q for phrase in _FIRST_SLIDE_PHRASES) and hit.page == 1:
        boost += 1.0

    return boost


def _region_texts_for_hit(
    hit: PageHit,
    page_text: dict[tuple[str, int], str] | None,
) -> list[str]:
    if page_text is None:
        return []
    text = page_text.get((hit.doc_id, hit.page))
    return [text] if text is not None else []


def _inject_first_slide_pages(question: str, hits: list[PageHit]) -> list[PageHit]:
    q = question.lower()
    if not any(phrase in q for phrase in _FIRST_SLIDE_PHRASES):
        return hits

    pages_by_doc: dict[str, set[int]] = {}
    best_by_doc: dict[str, PageHit] = {}
    for hit in hits:
        pages_by_doc.setdefault(hit.doc_id, set()).add(hit.page)
        best = best_by_doc.get(hit.doc_id)
        if best is None or hit.score > best.score:
            best_by_doc[hit.doc_id] = hit

    injected: list[PageHit] = []
    for doc_id, best in best_by_doc.items():
        if 1 in pages_by_doc.get(doc_id, set()):
            continue
        injected.append(
            PageHit(
                doc_id=doc_id,
                page=1,
                score=best.score,
                source=best.source,
            )
        )
    return hits + injected


def rerank_pages(
    question: str,
    hits: list[PageHit],
    *,
    page_text: dict[tuple[str, int], str] | None = None,
) -> list[PageHit]:
    hits = _inject_first_slide_pages(question, hits)
    cues = {
        (hit.doc_id, hit.page): cue_boost(
            question, hit, _region_texts_for_hit(hit, page_text)
        )
        for hit in hits
    }

    ranked = sorted(
        hits,
        key=lambda hit: (
            -(hit.score + cues[(hit.doc_id, hit.page)]),
            hit.doc_id,
            hit.page,
        ),
    )
    return ranked[:POOL_K]
