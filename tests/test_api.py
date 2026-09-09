import asyncio
import json
import uuid
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from pageanchor.ids import new_trace_id
from pageanchor.models import Citation, GroundedAnswer, PageHit, Trace

pytest.importorskip("fastapi")

PNG_1X1 = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
)


def _run(coro):
    return asyncio.run(coro)


def _sample_answer(question: str, mode: str = "hybrid") -> GroundedAnswer:
    return GroundedAnswer(
        question=question,
        answer="ViDoRe",
        abstain=False,
        citations=[
            Citation(
                doc_id="hello",
                page=1,
                region_id="hello:p1:r0",
                bbox=(0.1, 0.1, 0.5, 0.2),
                quote="THE_TOKEN_42",
                verified=True,
            )
        ],
        trace=Trace(
            trace_id=new_trace_id(),
            retrieval_mode=mode,  # type: ignore[arg-type]
            hits=[PageHit(doc_id="hello", page=1, score=0.9, source="text")],
        ),
    )


@pytest.fixture
def corpus(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("PAGEANCHOR_CORPUS_ROOT", str(tmp_path))
    monkeypatch.setenv("LANCEDB_URI", str(tmp_path / "lancedb"))
    (tmp_path / "manifest.json").write_text(
        json.dumps(
            {
                "version": "1.0.0",
                "documents": [
                    {
                        "id": "hello",
                        "title": "Hello",
                        "path": "pdfs/hello.pdf",
                        "pages": 1,
                        "sha256": "abc",
                        "license": "test",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    regions = tmp_path / "regions"
    regions.mkdir()
    (regions / "hello.json").write_text(
        json.dumps(
            [
                {
                    "doc_id": "hello",
                    "page": 1,
                    "region_id": "hello:p1:r0",
                    "type": "text",
                    "bbox": [0.1, 0.1, 0.5, 0.2],
                    "text": "THE_TOKEN_42 lives here",
                }
            ]
        ),
        encoding="utf-8",
    )
    page_dir = tmp_path / "pages" / "hello"
    page_dir.mkdir(parents=True)
    (page_dir / "p1.png").write_bytes(PNG_1X1)
    return tmp_path


async def _client():
    from pageanchor.api.main import app

    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def test_health_includes_trace_id(corpus: Path):
    async def run():
        async with await _client() as client:
            response = await client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert body["ok"] is True
        uuid.UUID(body["trace_id"], version=4)
        assert "tables" in body
        assert body["lancedb_open"] is False

    _run(run())


def test_corpus_and_doc_row(corpus: Path):
    async def run():
        async with await _client() as client:
            listing = await client.get("/v1/corpus")
            row = await client.get("/v1/docs/hello")
            missing = await client.get("/v1/docs/nope")
        assert listing.status_code == 200
        uuid.UUID(listing.json()["trace_id"], version=4)
        assert listing.json()["documents"][0]["id"] == "hello"
        assert row.status_code == 200
        assert row.json()["id"] == "hello"
        uuid.UUID(row.json()["trace_id"], version=4)
        assert missing.status_code == 404

    _run(run())


def test_page_png_and_regions(corpus: Path):
    async def run():
        async with await _client() as client:
            png = await client.get("/v1/docs/hello/pages/1")
            regions = await client.get("/v1/docs/hello/pages/1/regions")
            missing = await client.get("/v1/docs/hello/pages/9")
        assert png.status_code == 200
        assert png.headers["content-type"].startswith("image/png")
        assert png.content[:8] == b"\x89PNG\r\n\x1a\n"
        body = regions.json()
        uuid.UUID(body["trace_id"], version=4)
        assert body["regions"][0]["region_id"] == "hello:p1:r0"
        assert missing.status_code == 404

    _run(run())


def test_search_evidence_verify(corpus: Path, monkeypatch: pytest.MonkeyPatch):
    from pageanchor.api import routes

    monkeypatch.setattr(
        routes,
        "search_hybrid",
        lambda query, k: [PageHit(doc_id="hello", page=1, score=0.8, source="hybrid")],
    )

    async def run():
        async with await _client() as client:
            search = await client.post(
                "/v1/search", json={"query": "token", "k": 5, "mode": "hybrid"}
            )
            evidence = await client.post(
                "/v1/evidence",
                json={"query": "TOKEN", "doc_id": "hello", "page": 1, "max_regions": 5},
            )
            verify = await client.post(
                "/v1/verify",
                json={
                    "quote": "THE_TOKEN_42",
                    "doc_id": "hello",
                    "page": 1,
                    "region_id": "hello:p1:r0",
                },
            )
        assert search.status_code == 200
        body = search.json()
        uuid.UUID(body["trace_id"], version=4)
        assert body["hits"][0]["page"] == 1
        assert evidence.status_code == 200
        uuid.UUID(evidence.json()["trace_id"], version=4)
        assert evidence.json()["regions"][0]["region_id"] == "hello:p1:r0"
        assert verify.status_code == 200
        uuid.UUID(verify.json()["trace_id"], version=4)
        assert verify.json()["ok"] is True

    _run(run())


def test_answer_uses_mocked_grounded_answer(corpus: Path, monkeypatch: pytest.MonkeyPatch):
    from pageanchor.api import routes

    seen: dict = {}
    fake = _sample_answer("What is the token?", "text")

    def fake_answer(question, mode="hybrid", strict=True, **kwargs):
        seen.update(question=question, mode=mode, strict=strict)
        return fake

    monkeypatch.setattr(routes, "grounded_answer", fake_answer)

    async def run():
        async with await _client() as client:
            response = await client.post(
                "/v1/answer",
                json={"question": "What is the token?", "mode": "text", "strict": True},
            )
        assert response.status_code == 200
        body = response.json()
        assert body["trace_id"] == fake.trace.trace_id
        assert body["answer"] == "ViDoRe"
        assert body["citations"][0]["quote"] == "THE_TOKEN_42"
        assert body["trace"]["trace_id"] == fake.trace.trace_id
        assert seen == {
            "question": "What is the token?",
            "mode": "text",
            "strict": True,
        }

    _run(run())


def test_cors_allows_localhost_3000(corpus: Path):
    async def run():
        async with await _client() as client:
            response = await client.get(
                "/health", headers={"Origin": "http://localhost:3000"}
            )
            denied = await client.get(
                "/health", headers={"Origin": "http://evil.example"}
            )
        assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
        assert denied.headers.get("access-control-allow-origin") != "http://evil.example"

    _run(run())


def test_invalid_doc_id_is_400(corpus: Path):
    async def run():
        async with await _client() as client:
            row = await client.get("/v1/docs/bad!id")
            evidence = await client.post(
                "/v1/evidence",
                json={"query": "token", "doc_id": "bad!id", "page": 1, "max_regions": 5},
            )
        assert row.status_code == 400
        assert evidence.status_code == 400

    _run(run())


def test_search_and_answer_missing_lancedb_is_503(corpus: Path):
    async def run():
        async with await _client() as client:
            search = await client.post(
                "/v1/search", json={"query": "token", "k": 1, "mode": "text"}
            )
            answer = await client.post(
                "/v1/answer", json={"question": "token", "mode": "text", "strict": True}
            )
        assert search.status_code == 503
        assert "LanceDB not found" in search.json()["detail"]
        assert answer.status_code == 503
        assert "LanceDB not found" in answer.json()["detail"]

    _run(run())
