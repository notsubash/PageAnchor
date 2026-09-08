from __future__ import annotations

import hashlib
import json
import urllib.request
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from pageanchor.config import (
    DOC_ID_RE,
    MAX_PDF_BYTES,
    layout_engine,
    load_settings,
    under_root,
)
from pageanchor.models import Region

from .index_text import EmbedFn, has_indexed_doc, index_text
from .layout import extract_regions
from .render import render_pdf


def pdf_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ingest_document(
    doc: dict[str, Any],
    corpus_root: Path,
    *,
    embed: EmbedFn | None = None,
    lancedb_uri: str | None = None,
) -> dict[str, Any]:
    doc_id = _require_doc_id(doc["id"])
    pdf_path = _pdf_path(corpus_root, doc["path"])
    if not pdf_path.is_file():
        raise FileNotFoundError(f"missing PDF {pdf_path}")
    digest = pdf_sha256(pdf_path)
    expected = doc["sha256"]
    if digest != expected:
        raise ValueError(f"sha256 mismatch for {doc_id}: expected {expected}, got {digest}")
    uri = lancedb_uri or str(load_settings().lancedb_uri)
    pages_dir = under_root(corpus_root, "pages", doc_id)
    regions_path = under_root(corpus_root, "regions", f"{doc_id}.json")
    expected_pages = int(doc["pages"])
    png_names = {path.name for path in pages_dir.glob("p*.png")} if pages_dir.is_dir() else set()
    pngs_ok = png_names == {f"p{page}.png" for page in range(1, expected_pages + 1)}
    engine = layout_engine()
    regions_ok = regions_path.is_file() and _stored_layout(regions_path) == engine
    indexed = has_indexed_doc(uri, doc_id)
    if pngs_ok and regions_ok and indexed:
        return {"skipped": True, "doc_id": doc_id}
    if not pngs_ok:
        render_pdf(pdf_path, pages_dir)
    if not regions_ok:
        regions = extract_regions(pdf_path, doc_id)
        regions_path.parent.mkdir(parents=True, exist_ok=True)
        regions_path.write_text(
            json.dumps([region.model_dump() for region in regions], indent=2),
            encoding="utf-8",
        )
        _write_layout(regions_path, engine)
    else:
        regions = [
            Region.model_validate(item)
            for item in json.loads(regions_path.read_text(encoding="utf-8"))
        ]
    if not indexed:
        print(f"indexing {doc_id} ({len(regions)} regions)", flush=True)
        index_text(regions, uri, embed=embed)
    return {"skipped": False, "doc_id": doc_id}


def download_pdf(doc: dict[str, Any], dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    url = doc.get("download_url") or _pdf_url(str(doc.get("source_url") or ""))
    if not url:
        raise FileNotFoundError(f"missing {dest} and no download_url/source_url")
    _require_https(url)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "pageanchor/0.1 (research corpus fetch)"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        _require_https(response.geturl())
        data = response.read(MAX_PDF_BYTES + 1)
    if len(data) > MAX_PDF_BYTES:
        raise ValueError(f"PDF too large for {doc['id']}")
    dest.write_bytes(data)
    digest = pdf_sha256(dest)
    expected = doc.get("sha256")
    if expected and digest != expected:
        dest.unlink(missing_ok=True)
        raise ValueError(f"downloaded hash mismatch for {doc['id']}")


def _pdf_url(source_url: str) -> str:
    if "arxiv.org/abs/" in source_url:
        return source_url.replace("/abs/", "/pdf/")
    return source_url


def _require_https(url: str) -> None:
    if urlparse(url).scheme != "https":
        raise ValueError(f"only https downloads are allowed: {url}")


def _require_doc_id(doc_id: str) -> str:
    if not DOC_ID_RE.match(doc_id):
        raise ValueError(f"invalid doc_id {doc_id!r}")
    return doc_id


def _pdf_path(corpus_root: Path, rel: str) -> Path:
    path = Path(rel)
    if path.is_absolute() or ".." in path.parts or path.parts[:1] != ("pdfs",):
        raise ValueError(f"invalid corpus path {rel!r}")
    return under_root(corpus_root, path)


def _layout_mark(regions_path: Path) -> Path:
    return regions_path.with_name(regions_path.name + ".layout")


def _stored_layout(regions_path: Path) -> str:
    mark = _layout_mark(regions_path)
    if not mark.is_file():
        return "pymupdf"
    return mark.read_text(encoding="utf-8").strip() or "pymupdf"


def _write_layout(regions_path: Path, engine: str) -> None:
    _layout_mark(regions_path).write_text(engine, encoding="utf-8")


def ingest_all(
    *,
    doc_id: str | None = None,
    all_docs: bool = False,
    corpus_root: Path | None = None,
) -> Iterator[dict[str, Any]]:
    root = Path(corpus_root or load_settings().corpus_root)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    docs = list(manifest["documents"])
    if doc_id:
        doc_id = _require_doc_id(doc_id)
        docs = [item for item in docs if item["id"] == doc_id]
        if not docs:
            raise ValueError(f"unknown doc id {doc_id}")
    elif not all_docs:
        raise ValueError("pass --all or --doc-id")
    for doc in docs:
        _require_doc_id(doc["id"])
        pdf_path = _pdf_path(root, doc["path"])
        if pdf_path.is_file() and pdf_sha256(pdf_path) != doc["sha256"]:
            pdf_path.unlink()
        if not pdf_path.is_file():
            download_pdf(doc, pdf_path)
        yield ingest_document(doc, root)
