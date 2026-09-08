from __future__ import annotations

from pathlib import Path

import pymupdf

from pageanchor.config import layout_engine
from pageanchor.ids import region_id
from pageanchor.models import BBox, Region, RegionType


def extract_regions(pdf_path: Path, doc_id: str) -> list[Region]:
    # Default is PyMuPDF so frozen gold quotes stay valid. Docling is opt-in.
    if layout_engine() == "docling":
        try:
            regions = _from_docling(pdf_path, doc_id)
        except Exception:
            regions = _from_pymupdf(pdf_path, doc_id)
    else:
        regions = _from_pymupdf(pdf_path, doc_id)
    return _renumber(_ensure_pages(pdf_path, doc_id, regions))


def _clamp_bbox(bbox: BBox) -> BBox:
    x0, y0, x1, y1 = bbox
    x0 = min(max(x0, 0.0), 1.0)
    y0 = min(max(y0, 0.0), 1.0)
    x1 = min(max(x1, 0.0), 1.0)
    y1 = min(max(y1, 0.0), 1.0)
    if x1 <= x0:
        x1 = min(x0 + 1e-4, 1.0)
    if y1 <= y0:
        y1 = min(y0 + 1e-4, 1.0)
    return (x0, y0, x1, y1)


def _from_pymupdf(pdf_path: Path, doc_id: str) -> list[Region]:
    doc = pymupdf.open(pdf_path)
    regions: list[Region] = []
    try:
        for page in doc:
            page_no = page.number + 1
            width, height = page.rect.width, page.rect.height
            index = 0
            for block in page.get_text("dict")["blocks"]:
                if block.get("type") != 0:
                    continue
                text = "\n".join(
                    "".join(span["text"] for span in line["spans"])
                    for line in block.get("lines", [])
                ).strip()
                if not text:
                    continue
                x0, y0, x1, y1 = block["bbox"]
                regions.append(
                    Region(
                        doc_id=doc_id,
                        page=page_no,
                        region_id=region_id(doc_id, page_no, index),
                        type="text",
                        bbox=_clamp_bbox((x0 / width, y0 / height, x1 / width, y1 / height)),
                        text=text,
                    )
                )
                index += 1
    finally:
        doc.close()
    return regions


def _from_docling(pdf_path: Path, doc_id: str) -> list[Region]:
    from docling.document_converter import DocumentConverter

    result = DocumentConverter().convert(str(pdf_path))
    dl_doc = result.document
    regions: list[Region] = []
    counts: dict[int, int] = {}
    for item, _level in dl_doc.iterate_items():
        provs = getattr(item, "prov", None) or []
        if not provs:
            continue
        prov = provs[0]
        page_no = int(prov.page_no)
        if page_no < 1:
            page_no = 1
        page = (getattr(dl_doc, "pages", None) or {}).get(page_no)
        if page is None:
            continue
        size = page.size
        width, height = float(size.width), float(size.height)
        bbox = _docling_bbox(prov.bbox, width, height)
        text = _item_text(item)
        index = counts.get(page_no, 0)
        counts[page_no] = index + 1
        regions.append(
            Region(
                doc_id=doc_id,
                page=page_no,
                region_id=region_id(doc_id, page_no, index),
                type=_region_type(getattr(item, "label", None)),
                bbox=bbox,
                text=text,
            )
        )
    if not regions:
        raise RuntimeError("docling returned no regions")
    return regions


def _docling_bbox(bbox: object, width: float, height: float) -> BBox:
    left = float(getattr(bbox, "l")) / width
    right = float(getattr(bbox, "r")) / width
    origin = str(getattr(bbox, "coord_origin", "")).upper()
    top = float(getattr(bbox, "t"))
    bottom = float(getattr(bbox, "b"))
    if "BOTTOMLEFT" in origin:
        y0 = 1.0 - (max(top, bottom) / height)
        y1 = 1.0 - (min(top, bottom) / height)
    else:
        y0 = min(top, bottom) / height
        y1 = max(top, bottom) / height
    return _clamp_bbox((min(left, right), y0, max(left, right), y1))


def _item_text(item: object) -> str:
    text = getattr(item, "text", None)
    if text:
        return str(text).strip()
    export = getattr(item, "export_to_markdown", None)
    if callable(export):
        try:
            return str(export() or "").strip()
        except Exception:
            return ""
    return ""


def _region_type(label: object) -> RegionType:
    value = str(label or "").lower()
    if "table" in value:
        return "table"
    if "picture" in value or "figure" in value or "image" in value:
        return "figure"
    if "title" in value or "heading" in value or "header" in value:
        return "title"
    if any(
        key in value
        for key in ("text", "list", "caption", "paragraph", "code", "formula", "footnote")
    ):
        return "text"
    return "other"


def _ensure_pages(pdf_path: Path, doc_id: str, regions: list[Region]) -> list[Region]:
    doc = pymupdf.open(pdf_path)
    try:
        n_pages = doc.page_count
    finally:
        doc.close()
    by_page: dict[int, list[Region]] = {page: [] for page in range(1, n_pages + 1)}
    for region in regions:
        if region.page in by_page:
            by_page[region.page].append(region)
    out: list[Region] = []
    for page in range(1, n_pages + 1):
        if by_page[page]:
            out.extend(by_page[page])
        else:
            out.append(
                Region(
                    doc_id=doc_id,
                    page=page,
                    region_id=region_id(doc_id, page, 0),
                    type="other",
                    bbox=(0.0, 0.0, 1.0, 1.0),
                    text="",
                )
            )
    return out


def _renumber(regions: list[Region]) -> list[Region]:
    counts: dict[int, int] = {}
    out: list[Region] = []
    for region in regions:
        index = counts.get(region.page, 0)
        counts[region.page] = index + 1
        out.append(
            region.model_copy(update={"region_id": region_id(region.doc_id, region.page, index)})
        )
    return out
