from pageanchor.ground.receipt import build_receipt, crop_citation_png
from pageanchor.ids import new_trace_id
from pageanchor.models import Citation, GroundedAnswer, Trace

PNG_1X1 = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
)


def test_build_receipt_copies_hash_from_manifest(tmp_path, monkeypatch):
    monkeypatch.setenv("PAGEANCHOR_CORPUS_ROOT", str(tmp_path))
    (tmp_path / "manifest.json").write_text(
        '{"version":"1.0.0","ingest_version":"1","documents":[{"id":"hello","title":"H","path":"pdfs/h.pdf","pages":1,"sha256":"abc","license":"t"}]}',
        encoding="utf-8",
    )
    answer = GroundedAnswer(
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
    receipt = build_receipt(answer, corpus_root=tmp_path)
    assert receipt.documents[0].sha256 == "abc"
    assert receipt.abstain_reason == "unsupported"
    assert receipt.trace_id == answer.trace.trace_id


def test_crop_citation_png_returns_png_bytes(tmp_path, monkeypatch):
    monkeypatch.setenv("PAGEANCHOR_CORPUS_ROOT", str(tmp_path))
    page_dir = tmp_path / "pages" / "hello"
    page_dir.mkdir(parents=True)
    (page_dir / "p1.png").write_bytes(PNG_1X1)
    data = crop_citation_png("hello", 1, (0.0, 0.0, 1.0, 1.0), corpus_root=tmp_path)
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
