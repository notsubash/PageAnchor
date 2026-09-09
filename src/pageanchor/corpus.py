from __future__ import annotations

import json
from pathlib import Path

from pageanchor.config import DOC_ID_RE, under_root
from pageanchor.models import Region


def require_doc_id(doc_id: str) -> str:
    if not DOC_ID_RE.match(doc_id):
        raise ValueError(f"invalid doc_id {doc_id!r}")
    return doc_id


def load_manifest(root: Path) -> dict:
    path = Path(root) / "manifest.json"
    if not path.is_file():
        raise FileNotFoundError("manifest missing")
    return json.loads(path.read_text(encoding="utf-8"))


def get_document(root: Path, doc_id: str) -> dict:
    doc_id = require_doc_id(doc_id)
    for doc in load_manifest(root).get("documents", []):
        if doc.get("id") == doc_id:
            return doc
    raise FileNotFoundError(f"unknown doc_id {doc_id}")


def page_png_path(root: Path, doc_id: str, page: int) -> Path:
    if page < 1:
        raise ValueError("page must be >= 1")
    path = under_root(root, "pages", require_doc_id(doc_id), f"p{page}.png")
    if not path.is_file():
        raise FileNotFoundError("page image missing")
    return path


def load_regions(root: Path, doc_id: str, page: int | None = None) -> list[Region]:
    if page is not None and page < 1:
        raise ValueError("page must be >= 1")
    path = under_root(root, "regions", f"{require_doc_id(doc_id)}.json")
    if not path.is_file():
        raise FileNotFoundError("regions missing")
    regions = [Region.model_validate(item) for item in json.loads(path.read_text(encoding="utf-8"))]
    if page is None:
        return regions
    return [region for region in regions if region.page == page]


def find_region(root: Path, doc_id: str, page: int, region_id: str) -> Region:
    for region in load_regions(root, doc_id, page):
        if region.region_id == region_id:
            return region
    raise FileNotFoundError("region not found")
