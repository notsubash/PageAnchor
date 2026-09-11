import asyncio
import json
import uuid
from pathlib import Path

import pytest

from pageanchor.ground.answer import GeneratorCitation, GeneratorOutput, grounded_answer
from pageanchor.ids import new_trace_id
from pageanchor.models import Citation, GroundedAnswer, PageHit, Trace

pytest.importorskip("mcp")

PNG_1X1 = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
)


def _run(coro):
    return asyncio.run(coro)


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


def _client():
    from mcp import Client

    from pageanchor.mcp.server import mcp

    return Client(mcp)


def _body(result) -> dict:
    if result.structured_content is not None:
        return result.structured_content
    return json.loads(result.content[0].text)


def _drop_volatile(payload: dict) -> dict:
    payload = json.loads(json.dumps(payload))
    payload["trace"]["trace_id"] = "X"
    payload["trace"]["timings_ms"] = {}
    return payload


def test_tools_and_resources_are_listed(corpus: Path):
    async def run():
        async with _client() as client:
            tools = await client.list_tools()
            templates = await client.list_resource_templates()
            resources = await client.list_resources()
        names = {tool.name for tool in tools.tools}
        assert names == {
            "search_documents",
            "get_page_regions",
            "select_evidence",
            "verify_quote",
            "grounded_answer",
            "export_receipt",
        }
        for tool in tools.tools:
            text = (tool.description or "").lower()
            assert "do not state a fact until verify_quote is true" in text
            assert "do not guess page content; call select_evidence" in text
        uris = {item.uri for item in resources.resources}
        assert "corpus://manifest" in uris
        patterns = {item.uri_template for item in templates.resource_templates}
        assert "doc://{doc_id}/meta" in patterns
        assert "doc://{doc_id}/page/{page}" in patterns
        assert "doc://{doc_id}/page/{page}/regions" in patterns

    _run(run())


def test_resources_serve_manifest_regions_and_png(corpus: Path):
    async def run():
        async with _client() as client:
            manifest = await client.read_resource("corpus://manifest")
            meta = await client.read_resource("doc://hello/meta")
            regions = await client.read_resource("doc://hello/page/1/regions")
            png = await client.read_resource("doc://hello/page/1")

        def _text(result):
            return result.contents[0].text

        assert json.loads(_text(manifest))["documents"][0]["id"] == "hello"
        assert json.loads(_text(meta)) == {
            "id": "hello",
            "title": "Hello",
            "pages": 1,
            "license": "test",
        }
        assert json.loads(_text(regions))[0]["region_id"] == "hello:p1:r0"
        blob = png.contents[0]
        data = blob.blob
        if isinstance(data, str):
            import base64

            data = base64.b64decode(data)
        assert data[:8] == b"\x89PNG\r\n\x1a\n"

    _run(run())


def test_search_evidence_verify(corpus: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        "pageanchor.mcp.tools.search_hybrid",
        lambda query, k: [PageHit(doc_id="hello", page=1, score=0.8, source="hybrid")],
    )

    async def run():
        async with _client() as client:
            search = await client.call_tool(
                "search_documents",
                {"query": "token", "k": 5, "mode": "hybrid"},
            )
            evidence = await client.call_tool(
                "select_evidence",
                {"query": "TOKEN", "doc_id": "hello", "page": 1, "max_regions": 5},
            )
            regions = await client.call_tool(
                "get_page_regions",
                {"doc_id": "hello", "page": 1},
            )
            verify = await client.call_tool(
                "verify_quote",
                {
                    "quote": "THE_TOKEN_42",
                    "doc_id": "hello",
                    "page": 1,
                    "region_id": "hello:p1:r0",
                },
            )
        search_body = _body(search)
        uuid.UUID(search_body["trace_id"], version=4)
        assert search_body["hits"][0]["page"] == 1
        uuid.UUID(_body(evidence)["trace_id"], version=4)
        assert _body(evidence)["regions"][0]["region_id"] == "hello:p1:r0"
        assert _body(regions)["regions"][0]["text"] == "THE_TOKEN_42 lives here"
        uuid.UUID(_body(verify)["trace_id"], version=4)
        assert _body(verify)["ok"] is True

    _run(run())


def test_grounded_answer_matches_core(corpus: Path, monkeypatch: pytest.MonkeyPatch):
    from pageanchor.ground import answer as answer_mod

    def fake_search(query, k):
        return [PageHit(doc_id="hello", page=1, score=0.9, source="text")]

    def fake_generate(question, regions):
        return GeneratorOutput(
            answer="THE_TOKEN_42",
            citations=[
                GeneratorCitation(region_id="hello:p1:r0", quote="THE_TOKEN_42")
            ],
        )

    monkeypatch.setattr(answer_mod, "search_text", fake_search)
    monkeypatch.setattr(answer_mod, "_generate_deepseek", fake_generate)

    core = grounded_answer("What is the token?", "text", strict=True).model_dump(mode="json")

    async def run():
        async with _client() as client:
            result = await client.call_tool(
                "grounded_answer",
                {"question": "What is the token?", "mode": "text", "strict": True},
            )
        assert not result.is_error
        mcp_body = _body(result)
        assert _drop_volatile(mcp_body) == _drop_volatile(core)
        assert mcp_body["answer"] == "THE_TOKEN_42"
        assert mcp_body["citations"][0]["verified"] is True

    _run(run())


def test_grounded_answer_envelope_wraps_same_object(corpus: Path, monkeypatch: pytest.MonkeyPatch):
    fake = GroundedAnswer(
        question="What is the token?",
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
            retrieval_mode="text",
            hits=[PageHit(doc_id="hello", page=1, score=0.9, source="text")],
        ),
    )
    monkeypatch.setattr("pageanchor.mcp.tools.run_grounded_answer", lambda *a, **k: fake)

    async def run():
        async with _client() as client:
            result = await client.call_tool(
                "grounded_answer",
                {"question": "What is the token?", "mode": "text"},
            )
        body = _body(result)
        assert body["trace"]["trace_id"] == fake.trace.trace_id
        assert body["answer"] == "ViDoRe"

    _run(run())


def test_export_receipt_copies_manifest_hash(corpus: Path):
    fake = GroundedAnswer(
        question="token?",
        answer=None,
        abstain=True,
        abstain_reason="unsupported",
        citations=[
            Citation(
                doc_id="hello",
                page=1,
                region_id="hello:p1:r0",
                bbox=(0.1, 0.1, 0.5, 0.2),
                quote="Single-Task Training",
                quote_in_region=True,
                answer_in_quote=False,
            )
        ],
        trace=Trace(trace_id=new_trace_id(), retrieval_mode="hybrid"),
    )

    async def run():
        async with _client() as client:
            result = await client.call_tool(
                "export_receipt",
                {"answer": fake.model_dump(mode="json")},
            )
        assert not result.is_error
        body = _body(result)
        assert body["documents"][0]["sha256"] == "abc"
        assert body["abstain_reason"] == "unsupported"
        assert body["trace_id"] == fake.trace.trace_id

    _run(run())
