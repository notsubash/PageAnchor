from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path

from pageanchor.config import load_settings
from pageanchor.corpus import load_regions, require_doc_id
from pageanchor.models import PageHit, ScoredRegion

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")
# Query-side only. Region tokens stay intact so a rare word on the page can still match.
# Closed English + question list, no stemming. use/used/using stay as content words;
# dense_rerank is what beats appendix lines that share "used".
_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "of",
        "in",
        "on",
        "for",
        "to",
        "from",
        "with",
        "by",
        "as",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "what",
        "which",
        "who",
        "whom",
        "how",
        "when",
        "where",
        "why",
        "does",
        "did",
        "do",
    }
)

EmbedFn = Callable[[list[str]], list[list[float]]]


def select_regions(
    query: str,
    doc_id: str,
    page: int,
    max_regions: int = 5,
    *,
    corpus_root: Path | None = None,
) -> list[ScoredRegion]:
    require_doc_id(doc_id)
    root = Path(corpus_root or load_settings().corpus_root)
    query_tokens = _query_tokens(query)
    scored: list[ScoredRegion] = [
        ScoredRegion(
            **region.model_dump(), score=_jaccard(query_tokens, _tokens(region.text))
        )
        for region in load_regions(root, doc_id, page)
    ]
    scored.sort(key=lambda region: (-region.score, region.region_id))
    return scored[:max_regions]


def dense_rerank(
    question: str,
    regions: list[ScoredRegion],
    *,
    embed_query: EmbedFn | None = None,
    embed_passages: EmbedFn | None = None,
) -> list[ScoredRegion]:
    if not regions:
        return []
    query_fn = embed_query
    passage_fn = embed_passages
    if query_fn is None or passage_fn is None:
        from pageanchor.embed import embed_passages as default_passages
        from pageanchor.embed import embed_queries as default_queries

        query_fn = query_fn or default_queries
        passage_fn = passage_fn or default_passages
    query_vec = query_fn([question])[0]
    passage_vecs = passage_fn([region.text for region in regions])
    scored: list[ScoredRegion] = []
    for region, vector in zip(regions, passage_vecs, strict=True):
        score = sum(a * b for a, b in zip(query_vec, vector, strict=True))
        scored.append(region.model_copy(update={"score": float(score)}))
    scored.sort(key=lambda region: (-region.score, region.region_id))
    return scored


def select_evidence(
    question: str,
    hits: list[PageHit],
    *,
    max_regions: int = 5,
    per_page: int = 2,
    pool_per_page: int = 20,
    corpus_root: Path | None = None,
    embed_query: EmbedFn | None = None,
    embed_passages: EmbedFn | None = None,
) -> list[ScoredRegion]:
    pool: list[ScoredRegion] = []
    seen: set[tuple[str, int]] = set()
    for hit in hits:
        key = (hit.doc_id, hit.page)
        if key in seen:
            continue
        seen.add(key)
        pool.extend(
            select_regions(
                question,
                hit.doc_id,
                hit.page,
                max_regions=pool_per_page,
                corpus_root=corpus_root,
            )
        )
    ranked = dense_rerank(
        question, pool, embed_query=embed_query, embed_passages=embed_passages
    )
    counts: dict[tuple[str, int], int] = {}
    picked: list[ScoredRegion] = []
    for region in ranked:
        key = (region.doc_id, region.page)
        if counts.get(key, 0) >= per_page:
            continue
        counts[key] = counts.get(key, 0) + 1
        picked.append(region)
        if len(picked) >= max_regions:
            break
    return picked


def _query_tokens(query: str) -> set[str]:
    tokens = _tokens(query) - _STOPWORDS
    return tokens or _tokens(query)


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)
