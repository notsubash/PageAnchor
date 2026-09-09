from __future__ import annotations

from mcp.server import MCPServer

from pageanchor.config import load_settings
from pageanchor.corpus import get_document, load_manifest, load_regions, page_png_path

_JSON = "application/json"


def register_resources(mcp: MCPServer) -> None:
    @mcp.resource("corpus://manifest", mime_type=_JSON)
    def corpus_manifest() -> dict:
        """Frozen corpus manifest (ids, titles, licenses, hashes)."""
        return load_manifest(load_settings().corpus_root)

    @mcp.resource("doc://{doc_id}/meta", mime_type=_JSON)
    def doc_meta(doc_id: str) -> dict:
        """Document title, page count, and license."""
        doc = get_document(load_settings().corpus_root, doc_id)
        return {
            "id": doc.get("id", doc_id),
            "title": doc.get("title"),
            "pages": doc.get("pages"),
            "license": doc.get("license"),
        }

    @mcp.resource("doc://{doc_id}/page/{page}", mime_type="image/png")
    def page_png(doc_id: str, page: int) -> bytes:
        """Rendered page PNG (same file ingest wrote)."""
        return page_png_path(load_settings().corpus_root, doc_id, page).read_bytes()

    @mcp.resource("doc://{doc_id}/page/{page}/regions", mime_type=_JSON)
    def page_regions(doc_id: str, page: int) -> list[dict]:
        """Layout regions for a page. Do not guess page content; call select_evidence."""
        regions = load_regions(load_settings().corpus_root, doc_id, page)
        return [region.model_dump() for region in regions]
