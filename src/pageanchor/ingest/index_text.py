from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import lancedb
from lancedb.db import DBConnection

from pageanchor.config import DOC_ID_RE, TEXT_TABLE
from pageanchor.embed import embed_passages
from pageanchor.models import Region

CHUNK_CHARS = 1500
CHUNK_OVERLAP = 200
EmbedFn = Callable[[list[str]], list[list[float]]]


def chunk_text(text: str) -> list[str]:
    if len(text) <= CHUNK_CHARS:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        chunks.append(text[start : start + CHUNK_CHARS])
        if start + CHUNK_CHARS >= len(text):
            break
        start += CHUNK_CHARS - CHUNK_OVERLAP
    return chunks


def table_names(db: DBConnection) -> set[str]:
    return set(db.list_tables().tables)


def index_text(
    regions: list[Region],
    lancedb_uri: str,
    *,
    embed: EmbedFn | None = None,
) -> None:
    embed_fn = embed or embed_passages
    texts: list[str] = []
    meta: list[tuple[Region, int, str]] = []
    for region in regions:
        for index, chunk in enumerate(chunk_text(region.text)):
            texts.append(chunk)
            meta.append((region, index, chunk))
    vectors = embed_fn(texts) if texts else []
    rows = [
        {
            "vector": vector,
            "doc_id": region.doc_id,
            "page": region.page,
            "region_id": region.region_id,
            "chunk": chunk_index,
            "bbox": list(region.bbox),
            "text": chunk,
        }
        for (region, chunk_index, chunk), vector in zip(meta, vectors, strict=True)
    ]
    db = lancedb.connect(lancedb_uri)
    names = table_names(db)
    if TEXT_TABLE not in names:
        if rows:
            db.create_table(TEXT_TABLE, rows)
        return
    table = db.open_table(TEXT_TABLE)
    for doc_id in {region.doc_id for region in regions}:
        if not DOC_ID_RE.match(doc_id):
            raise ValueError(f"invalid doc_id {doc_id!r}")
        table.delete(f"doc_id = '{doc_id}'")
    if rows:
        table.add(rows)


def has_indexed_doc(lancedb_uri: str, doc_id: str) -> bool:
    if not Path(lancedb_uri).exists():
        return False
    db = lancedb.connect(lancedb_uri)
    if TEXT_TABLE not in table_names(db):
        return False
    if not DOC_ID_RE.match(doc_id):
        raise ValueError(f"invalid doc_id {doc_id!r}")
    table = db.open_table(TEXT_TABLE)
    # ponytail: full scan is fine for an 8-PDF corpus; switch to count_rows if this grows.
    column = table.to_arrow().column("doc_id").to_pylist()
    return doc_id in column
