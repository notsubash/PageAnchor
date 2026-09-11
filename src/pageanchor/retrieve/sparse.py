from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Callable
from pathlib import Path

import lancedb
from lancedb.db import DBConnection

from pageanchor.config import TEXT_TABLE, load_settings
from pageanchor.ingest.index_text import table_names
from pageanchor.models import PageHit

TokenizeFn = Callable[[str], list[str]]

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")
_K1 = 1.2
_B = 0.75


def bm25_score(
    query: str,
    doc: str,
    docs: list[str],
    *,
    tokenize: TokenizeFn | None = None,
) -> float:
    tok = tokenize or _tokenize
    corpus = [tok(item) for item in docs]
    return _score_tokens(tok(query), tok(doc), _corpus_stats(corpus))


def search_bm25(
    query: str,
    k: int,
    *,
    lancedb_uri: str | None = None,
    tokenize: TokenizeFn | None = None,
) -> list[PageHit]:
    uri = lancedb_uri or str(load_settings().lancedb_uri)
    tok = tokenize or _tokenize
    rows = _load_text_rows(uri)
    corpus = [tok(str(row.get("text") or "")) for row in rows]
    stats = _corpus_stats(corpus)
    query_tokens = tok(query)
    best: dict[tuple[str, int], PageHit] = {}
    for row, doc_tokens in zip(rows, corpus, strict=True):
        key = (str(row["doc_id"]), int(row["page"]))
        hit = PageHit(
            doc_id=key[0],
            page=key[1],
            score=_score_tokens(query_tokens, doc_tokens, stats),
            source="bm25",
        )
        current = best.get(key)
        if current is None or hit.score > current.score:
            best[key] = hit
    return sorted(best.values(), key=lambda hit: (-hit.score, hit.doc_id, hit.page))[:k]


def _load_text_rows(uri: str) -> list[dict]:
    if not Path(uri).exists():
        raise FileNotFoundError(f"LanceDB not found at {uri}; run pageanchor ingest")
    db: DBConnection = lancedb.connect(uri)
    if TEXT_TABLE not in table_names(db):
        raise FileNotFoundError(f"LanceDB not found at {uri}; run pageanchor ingest")
    # ponytail: full-table BM25 is fine for ~3k chunks. Upgrade: LanceDB FTS index.
    return db.open_table(TEXT_TABLE).to_arrow().to_pylist()


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _corpus_stats(corpus: list[list[str]]) -> tuple[int, float, Counter]:
    n_docs = len(corpus)
    avgdl = sum(len(item) for item in corpus) / n_docs if n_docs else 0.0
    df: Counter[str] = Counter()
    for item in corpus:
        df.update(set(item))
    return n_docs, avgdl, df


def _score_tokens(
    query_tokens: list[str],
    doc_tokens: list[str],
    stats: tuple[int, float, Counter],
) -> float:
    n_docs, avgdl, df = stats
    if n_docs == 0 or avgdl == 0.0:
        return 0.0
    tf = Counter(doc_tokens)
    length = len(doc_tokens)
    score = 0.0
    for term in query_tokens:
        n_qi = df[term]
        idf = math.log((n_docs - n_qi + 0.5) / (n_qi + 0.5) + 1.0)
        freq = tf[term]
        denom = freq + _K1 * (1.0 - _B + _B * length / avgdl)
        score += idf * (freq * (_K1 + 1.0)) / denom
    return score
