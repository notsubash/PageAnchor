import os
from pathlib import Path

import numpy as np
import pytest

from pageanchor.ingest.index_visual import index_visual
from pageanchor.retrieve.visual import maxsim, search_visual


def _pages(tmp_path: Path) -> list[tuple[str, int, Path]]:
    p1 = tmp_path / "p1.png"
    p2 = tmp_path / "p2.png"
    p1.write_bytes(b"x")
    p2.write_bytes(b"y")
    return [("hello", 1, p1), ("hello", 2, p2)]


def _embed_pages(paths: list[Path]) -> list[list[list[float]]]:
    out = []
    for path in paths:
        if path.name.startswith("p1"):
            out.append([[1.0, 0.0]])
        else:
            out.append([[0.0, 1.0]])
    return out


def _embed_query(query: str) -> list[list[float]]:
    if "alpha" in query:
        return [[1.0, 0.0]]
    return [[0.0, 1.0]]


def test_maxsim_sums_per_query_token_max():
    query = np.array([[1.0, 0.0]], dtype=np.float32)
    doc = np.array([[0.6, 0.8], [1.0, 0.0]], dtype=np.float32)
    assert maxsim(query, doc) == pytest.approx(1.0)


def test_search_visual_roundtrips_doc_id_and_page(tmp_path):
    uri = str(tmp_path / "lancedb")
    index_visual(_pages(tmp_path), uri, embed=_embed_pages)
    hits = search_visual("alpha token", k=5, lancedb_uri=uri, embed_query=_embed_query)
    assert hits[0].doc_id == "hello"
    assert hits[0].page == 1
    assert hits[0].source == "visual"
    assert hits[0].score > hits[1].score
    pages = [(hit.doc_id, hit.page) for hit in hits]
    assert pages.count(("hello", 1)) == 1


def test_index_visual_accepts_ragged_token_counts(tmp_path):
    uri = str(tmp_path / "lancedb")
    a = tmp_path / "p1.png"
    b = tmp_path / "p2.png"
    a.write_bytes(b"x")
    b.write_bytes(b"y")

    def embed_short(paths: list[Path]) -> list[list[list[float]]]:
        return [[[1.0, 0.0]] for _ in paths]

    def embed_long(paths: list[Path]) -> list[list[list[float]]]:
        return [[[0.0, 1.0], [0.0, 1.0], [0.0, 1.0]] for _ in paths]

    index_visual([("paper", 1, a)], uri, embed=embed_short)
    index_visual([("slides", 1, b)], uri, embed=embed_long)
    hits = search_visual("beta", k=5, lancedb_uri=uri, embed_query=_embed_query)
    pages = {(hit.doc_id, hit.page) for hit in hits}
    assert pages == {("paper", 1), ("slides", 1)}
    assert hits[0].doc_id == "slides"


def test_search_visual_missing_index_hints_ingest(tmp_path):
    uri = tmp_path / "lancedb"
    uri.mkdir()
    with pytest.raises(FileNotFoundError, match="ingest --visual"):
        search_visual("alpha", k=1, lancedb_uri=str(uri), embed_query=_embed_query)


@pytest.mark.gpu
def test_colqwen2_encode_query_shape():
    if os.environ.get("PAGEANCHOR_RUN_GPU") != "1":
        pytest.skip("real ColQwen2 is not run in CI")
    pytest.importorskip("colpali_engine")
    from pageanchor.retrieve.visual import encode_query

    vec = encode_query("benchmark")
    assert len(vec) > 0 and len(vec[0]) > 0


def test_colqwen2_hint_names_torch_and_install():
    from pageanchor.retrieve.visual import _colqwen2_hint

    text = _colqwen2_hint(RuntimeError("operator torchvision::nms does not exist"))
    assert "torch=" in text
    assert "torchvision=" in text
    assert "nms" in text
    assert "cu128" in text
