from __future__ import annotations

from io import BytesIO
from pathlib import Path

from pageanchor.config import layout_engine, load_settings
from pageanchor.corpus import get_document, load_manifest, page_png_path
from pageanchor.models import BBox, GroundedAnswer, Receipt, ReceiptDocument


def build_receipt(answer: GroundedAnswer, *, corpus_root: Path | None = None) -> Receipt:
    root = Path(corpus_root or load_settings().corpus_root)
    manifest = load_manifest(root)
    seen: set[str] = set()
    documents: list[ReceiptDocument] = []
    for citation in answer.citations:
        if citation.doc_id in seen:
            continue
        seen.add(citation.doc_id)
        doc = get_document(root, citation.doc_id)
        documents.append(
            ReceiptDocument(id=citation.doc_id, sha256=str(doc.get("sha256") or ""))
        )
    return Receipt(
        question=answer.question,
        answer=answer.answer,
        abstain=answer.abstain,
        abstain_reason=answer.abstain_reason,
        citations=answer.citations,
        verify=answer.trace.verify,
        documents=documents,
        ingest_version=str(manifest.get("ingest_version") or ""),
        layout_engine=layout_engine(),
        retrieval_mode=answer.trace.retrieval_mode,
        trace_id=answer.trace.trace_id,
        generator_model=load_settings().generator_model,
    )


def crop_citation_png(
    doc_id: str,
    page: int,
    bbox: BBox,
    *,
    corpus_root: Path | None = None,
) -> bytes:
    from PIL import Image

    root = Path(corpus_root or load_settings().corpus_root)
    with Image.open(page_png_path(root, doc_id, page)) as image:
        rgb = image.convert("RGB")
        width, height = rgb.size
        x0, y0, x1, y1 = bbox
        left = int(x0 * width)
        top = int(y0 * height)
        right = min(max(int(x1 * width), left + 1), width)
        bottom = min(max(int(y1 * height), top + 1), height)
        buf = BytesIO()
        rgb.crop((left, top, right, bottom)).save(buf, format="PNG")
        return buf.getvalue()
