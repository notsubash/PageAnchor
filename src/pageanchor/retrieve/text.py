from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import lancedb
from lancedb.db import DBConnection

from pageanchor.config import TEXT_TABLE, load_settings
from pageanchor.embed import embed_queries
from pageanchor.ingest.index_text import table_names
from pageanchor.models import PageHit

EmbedFn = Callable[[list[str]], list[list[float]]]


def search_text(
    query: str,
    k: int,
    *,
    lancedb_uri: str | None = None,
    embed_query: EmbedFn | None = None,
) -> list[PageHit]:
    uri = lancedb_uri or str(load_settings().lancedb_uri)
    if not Path(uri).exists():
        raise FileNotFoundError(f"LanceDB not found at {uri}; run pageanchor ingest")
    db: DBConnection = lancedb.connect(uri)
    if TEXT_TABLE not in table_names(db):
        raise FileNotFoundError(f"LanceDB not found at {uri}; run pageanchor ingest")
    table = db.open_table(TEXT_TABLE)
    embed_fn = embed_query or embed_queries
    query_vector = embed_fn([query])[0]
    records = table.search(query_vector).limit(max(k * 8, 32)).to_list()
    best: dict[tuple[str, int], PageHit] = {}
    for record in records:
        key = (str(record["doc_id"]), int(record["page"]))
        distance = float(record.get("_distance", 0.0))
        hit = PageHit(
            doc_id=key[0],
            page=key[1],
            score=1.0 / (1.0 + distance),
            source="text",
        )
        current = best.get(key)
        if current is None or hit.score > current.score:
            best[key] = hit
    return sorted(best.values(), key=lambda hit: (-hit.score, hit.doc_id, hit.page))[:k]
