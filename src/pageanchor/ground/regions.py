from __future__ import annotations

import re
from pathlib import Path

from pageanchor.config import load_settings
from pageanchor.corpus import load_regions, require_doc_id
from pageanchor.models import ScoredRegion

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


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
    query_tokens = _tokens(query)
    scored: list[ScoredRegion] = [
        ScoredRegion(
            **region.model_dump(), score=_jaccard(query_tokens, _tokens(region.text))
        )
        for region in load_regions(root, doc_id, page)
    ]
    scored.sort(key=lambda region: (-region.score, region.region_id))
    return scored[:max_regions]


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)
