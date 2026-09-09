from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import lancedb
import numpy as np
from lancedb.db import DBConnection

from pageanchor.config import VISUAL_TABLE, load_settings
from pageanchor.ingest.index_text import table_names
from pageanchor.ingest.index_visual import unpack_multivec
from pageanchor.models import PageHit

EmbedQueryFn = Callable[[str], list[list[float]]]

_model = None
_processor = None


def maxsim(query: np.ndarray, doc: np.ndarray) -> float:
    # ponytail: O(pages) MaxSim, fine until corpus >> 1k pages. Upgrade: token-level ANN.
    if query.size == 0 or doc.size == 0:
        return 0.0
    sims = query @ doc.T
    return float(np.max(sims, axis=1).sum())


def search_visual(
    query: str,
    k: int,
    *,
    lancedb_uri: str | None = None,
    embed_query: EmbedQueryFn | None = None,
) -> list[PageHit]:
    uri = lancedb_uri or str(load_settings().lancedb_uri)
    if not Path(uri).exists():
        raise FileNotFoundError(f"LanceDB not found at {uri}; run pageanchor ingest")
    db: DBConnection = lancedb.connect(uri)
    if VISUAL_TABLE not in table_names(db):
        raise FileNotFoundError(
            f"visual table {VISUAL_TABLE} missing at {uri}; run pageanchor ingest --visual"
        )
    table = db.open_table(VISUAL_TABLE)
    embed_fn = embed_query or encode_query
    query_vec = np.asarray(embed_fn(query), dtype=np.float32)
    if query_vec.ndim != 2:
        raise ValueError("visual query embedding must be (n_tokens, dim)")
    norms = np.linalg.norm(query_vec, axis=1, keepdims=True)
    query_vec = query_vec / np.clip(norms, 1e-12, None)
    hits: list[PageHit] = []
    for record in table.to_arrow().to_pylist():
        doc = unpack_multivec(record["n_tokens"], record["dim"], record["multivec"])
        hits.append(
            PageHit(
                doc_id=str(record["doc_id"]),
                page=int(record["page"]),
                score=maxsim(query_vec, doc),
                source="visual",
            )
        )
    return sorted(hits, key=lambda hit: (-hit.score, hit.doc_id, hit.page))[:k]


def encode_pages(paths: list[Path]) -> list[list[list[float]]]:
    model, processor = _load()
    rows: list[list[list[float]]] = []
    for index, path in enumerate(paths, start=1):
        print(f"visual encode {index}/{len(paths)} {path.name}", flush=True)
        image = _open_rgb(path)
        rows.append(_embed_batch(model, processor, processor.process_images([image]))[0])
    return rows


def encode_query(query: str) -> list[list[float]]:
    model, processor = _load()
    return _embed_batch(model, processor, processor.process_queries([query]))[0]


def _open_rgb(path: Path):
    from PIL import Image

    with Image.open(path) as image:
        return image.convert("RGB")


def _embed_batch(model, _processor, batch) -> list[list[list[float]]]:
    import torch

    batch = batch.to(model.device)
    with torch.inference_mode():
        output = model(**batch)
    if isinstance(output, list | tuple):
        vectors = output
    else:
        vectors = [output[i] for i in range(output.shape[0])]
    rows: list[list[list[float]]] = []
    for item in vectors:
        arr = item.float().cpu().numpy()
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        arr = arr / np.clip(norms, 1e-12, None)
        rows.append(arr.tolist())
    return rows


def _load():
    global _model, _processor
    if _model is None:
        try:
            import torch
            from colpali_engine.models import ColQwen2, ColQwen2Processor
        except ImportError as exc:
            raise ImportError(
                "visual retrieve needs the visual extra: uv sync --extra visual"
            ) from exc

        from pageanchor.config import load_settings

        name = load_settings().visual_retrieve_model
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        dtype = torch.bfloat16 if device.type == "cuda" else torch.float32
        _model = ColQwen2.from_pretrained(
            name,
            torch_dtype=dtype,
            device_map=None,
            attn_implementation="sdpa",
        ).to(device).eval()
        _processor = ColQwen2Processor.from_pretrained(name)
    return _model, _processor
