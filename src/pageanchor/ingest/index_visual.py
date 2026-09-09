from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import lancedb
import numpy as np
import pyarrow as pa
from lancedb.db import DBConnection

from pageanchor.config import DOC_ID_RE, VISUAL_TABLE
from pageanchor.ingest.index_text import table_names

EmbedPagesFn = Callable[[list[Path]], list[list[list[float]]]]

# Binary blob, not a vector column: ColQwen2 token counts differ by page size.
VISUAL_SCHEMA = pa.schema(
    [
        pa.field("doc_id", pa.utf8()),
        pa.field("page", pa.int32()),
        pa.field("n_tokens", pa.int32()),
        pa.field("dim", pa.int32()),
        pa.field("multivec", pa.binary()),
    ]
)


def pack_multivec(tokens: list[list[float]]) -> tuple[int, int, bytes]:
    arr = np.asarray(tokens, dtype=np.float32)
    if arr.ndim != 2 or arr.size == 0:
        raise ValueError("visual embedding must be (n_tokens, dim)")
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    arr = arr / np.clip(norms, 1e-12, None)
    return int(arr.shape[0]), int(arr.shape[1]), arr.reshape(-1).tobytes()


def unpack_multivec(n_tokens: int, dim: int, blob: bytes) -> np.ndarray:
    data = np.frombuffer(bytes(blob), dtype=np.float32)
    return data.reshape(int(n_tokens), int(dim))


def index_visual(
    page_pngs: list[tuple[str, int, Path]],
    lancedb_uri: str,
    *,
    embed: EmbedPagesFn | None = None,
) -> None:
    if embed is None:
        from pageanchor.retrieve.visual import encode_pages

        embed = encode_pages
    paths = [path for _, _, path in page_pngs]
    vectors = embed(paths) if paths else []
    rows = []
    for (doc_id, page, _), tokens in zip(page_pngs, vectors, strict=True):
        try:
            n_tokens, dim, blob = pack_multivec(tokens)
        except ValueError as exc:
            raise ValueError(
                f"visual embedding for {doc_id} p{page} must be (n_tokens, dim)"
            ) from exc
        rows.append(
            {
                "doc_id": doc_id,
                "page": page,
                "n_tokens": n_tokens,
                "dim": dim,
                "multivec": blob,
            }
        )
    payload = pa.Table.from_pylist(rows, schema=VISUAL_SCHEMA) if rows else None
    db = lancedb.connect(lancedb_uri)
    names = table_names(db)
    if VISUAL_TABLE not in names:
        if payload is not None:
            db.create_table(VISUAL_TABLE, payload, schema=VISUAL_SCHEMA)
        return
    table = db.open_table(VISUAL_TABLE)
    for doc_id in {doc_id for doc_id, _, _ in page_pngs}:
        if not DOC_ID_RE.match(doc_id):
            raise ValueError(f"invalid doc_id {doc_id!r}")
        table.delete(f"doc_id = '{doc_id}'")
    if payload is not None:
        table.add(payload)


def has_indexed_visual_doc(lancedb_uri: str, doc_id: str) -> bool:
    if not Path(lancedb_uri).exists():
        return False
    db: DBConnection = lancedb.connect(lancedb_uri)
    if VISUAL_TABLE not in table_names(db):
        return False
    if not DOC_ID_RE.match(doc_id):
        raise ValueError(f"invalid doc_id {doc_id!r}")
    table = db.open_table(VISUAL_TABLE)
    # ponytail: full scan is fine for an 8-PDF corpus; switch to count_rows if this grows.
    column = table.to_arrow().column("doc_id").to_pylist()
    return doc_id in column
