from __future__ import annotations

from typing import Any

_model: Any = None


def _load():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        from pageanchor.config import load_settings, torch_device

        device = torch_device()
        _model = SentenceTransformer(load_settings().text_embedding_model, device=device)
        print(f"text encoder on {device}", flush=True)
        # Regions are chunked to 1500 chars; 32k-token default makes CPU ingest unusable.
        _model.max_seq_length = 1024
        tokenizer = getattr(_model, "tokenizer", None)
        if tokenizer is not None:
            tokenizer.model_max_length = 1024
    return _model


def _as_rows(encoded: Any) -> list[list[float]]:
    if encoded is None:
        return []
    if getattr(encoded, "ndim", 1) == 1:
        encoded = [encoded]
    rows: list[list[float]] = []
    for item in encoded:
        rows.append(item.tolist() if hasattr(item, "tolist") else list(item))
    return rows


def embed_passages(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    return _as_rows(
        _load().encode(
            texts, normalize_embeddings=True, batch_size=16, show_progress_bar=True
        )
    )


def embed_queries(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    return _as_rows(
        _load().encode(
            texts, prompt_name="query", normalize_embeddings=True, batch_size=16
        )
    )
