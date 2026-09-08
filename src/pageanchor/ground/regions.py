from __future__ import annotations

import json
import re
from pathlib import Path

from pageanchor.config import DOC_ID_RE, load_settings, under_root
from pageanchor.models import Region, ScoredRegion

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


def select_regions(
    query: str,
    doc_id: str,
    page: int,
    max_regions: int = 5,
    *,
    corpus_root: Path | None = None,
) -> list[ScoredRegion]:
    if not DOC_ID_RE.match(doc_id):
        raise ValueError(f"invalid doc_id {doc_id!r}")
    root = Path(corpus_root or load_settings().corpus_root)
    path = under_root(root, "regions", f"{doc_id}.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    query_tokens = _tokens(query)
    scored: list[ScoredRegion] = []
    for item in payload:
        region = Region.model_validate(item)
        if region.page != page:
            continue
        scored.append(
            ScoredRegion(**region.model_dump(), score=_jaccard(query_tokens, _tokens(region.text)))
        )
    scored.sort(key=lambda region: (-region.score, region.region_id))
    return scored[:max_regions]


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)
