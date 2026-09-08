import hashlib
import math

from pageanchor.ingest.index_text import index_text
from pageanchor.models import Region
from pageanchor.retrieve.text import search_text


def _hash_embed(texts: list[str]) -> list[list[float]]:
    dim = 16
    vectors = []
    for text in texts:
        vec = [0.0] * dim
        for token in text.lower().split():
            slot = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % dim
            vec[slot] += 1.0
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        vectors.append([x / norm for x in vec])
    return vectors


def test_search_text_collapses_chunks_to_pages(tmp_path):
    uri = str(tmp_path / "lancedb")
    regions = [
        Region(
            doc_id="hello",
            page=1,
            region_id="hello:p1:r0",
            type="text",
            bbox=(0.1, 0.1, 0.9, 0.3),
            text="THE_TOKEN_42 lives on page one",
        ),
        Region(
            doc_id="hello",
            page=2,
            region_id="hello:p2:r0",
            type="text",
            bbox=(0.1, 0.1, 0.9, 0.3),
            text="unrelated potatoes and weather",
        ),
    ]
    index_text(regions, uri, embed=_hash_embed)
    hits = search_text("THE_TOKEN_42", k=5, lancedb_uri=uri, embed_query=_hash_embed)
    assert hits[0].doc_id == "hello"
    assert hits[0].page == 1
    assert hits[0].score > hits[1].score
    assert hits[0].source == "text"
    pages = [(hit.doc_id, hit.page) for hit in hits]
    assert pages.count(("hello", 1)) == 1
