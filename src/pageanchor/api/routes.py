from __future__ import annotations

import json
from pathlib import Path

import lancedb
from fastapi import APIRouter, Depends, HTTPException
from fastapi import Path as PathParam
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from pageanchor.api.deps import get_settings
from pageanchor.config import DOC_ID_RE, Settings, under_root
from pageanchor.ground.answer import grounded_answer
from pageanchor.ground.regions import select_regions
from pageanchor.ground.verify import verify_quote
from pageanchor.ids import new_trace_id
from pageanchor.ingest.index_text import table_names
from pageanchor.models import Region, RetrievalMode
from pageanchor.retrieve.hybrid import search_hybrid
from pageanchor.retrieve.text import search_text
from pageanchor.retrieve.visual import search_visual

router = APIRouter()


class SearchBody(BaseModel):
    query: str
    k: int = Field(default=5, ge=1)
    mode: RetrievalMode = "hybrid"


class EvidenceBody(BaseModel):
    query: str
    doc_id: str
    page: int = Field(ge=1)
    max_regions: int = Field(default=5, ge=1)


class VerifyBody(BaseModel):
    quote: str
    doc_id: str
    page: int = Field(ge=1)
    region_id: str


class AnswerBody(BaseModel):
    question: str
    mode: RetrievalMode = "hybrid"
    strict: bool = True


@router.get("/health")
def health(settings: Settings = Depends(get_settings)) -> dict:
    open_, tables = _table_counts(settings.lancedb_uri)
    return _traced(ok=True, lancedb_open=open_, tables=tables)


@router.get("/v1/corpus")
def corpus(settings: Settings = Depends(get_settings)) -> dict:
    return _traced(**_manifest(settings.corpus_root))


@router.get("/v1/docs/{doc_id}")
def doc_row(doc_id: str, settings: Settings = Depends(get_settings)) -> dict:
    doc_id = _require_doc_id(doc_id)
    for doc in _manifest(settings.corpus_root).get("documents", []):
        if doc.get("id") == doc_id:
            return _traced(**doc)
    raise HTTPException(404, "unknown doc_id")


@router.get("/v1/docs/{doc_id}/pages/{page}")
def page_png(
    doc_id: str,
    page: int = PathParam(ge=1),
    settings: Settings = Depends(get_settings),
) -> FileResponse:
    doc_id = _require_doc_id(doc_id)
    path = under_root(settings.corpus_root, "pages", doc_id, f"p{page}.png")
    if not path.is_file():
        raise HTTPException(404, "page image missing")
    return FileResponse(path, media_type="image/png")


@router.get("/v1/docs/{doc_id}/pages/{page}/regions")
def page_regions(
    doc_id: str,
    page: int = PathParam(ge=1),
    settings: Settings = Depends(get_settings),
) -> dict:
    regions = [region.model_dump() for region in _load_regions(settings.corpus_root, doc_id, page)]
    return _traced(regions=regions)


@router.post("/v1/search")
def search(body: SearchBody) -> dict:
    try:
        modes = {"text": search_text, "visual": search_visual, "hybrid": search_hybrid}
        hits = modes[body.mode](body.query, body.k)
    except FileNotFoundError as exc:
        raise HTTPException(503, str(exc)) from exc
    return _traced(hits=[hit.model_dump() for hit in hits])


@router.post("/v1/evidence")
def evidence(body: EvidenceBody, settings: Settings = Depends(get_settings)) -> dict:
    try:
        regions = select_regions(
            body.query,
            _require_doc_id(body.doc_id),
            body.page,
            max_regions=body.max_regions,
            corpus_root=settings.corpus_root,
        )
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return _traced(regions=[region.model_dump() for region in regions])


@router.post("/v1/verify")
def verify(body: VerifyBody, settings: Settings = Depends(get_settings)) -> dict:
    region = _find_region(settings.corpus_root, body.doc_id, body.page, body.region_id)
    ok = verify_quote(body.quote, region.text)
    return _traced(
        ok=ok,
        quote=body.quote,
        matched_text=body.quote if ok else None,
        doc_id=region.doc_id,
        page=region.page,
        region_id=region.region_id,
    )


@router.post("/v1/answer")
def answer(body: AnswerBody) -> dict:
    try:
        result = grounded_answer(body.question, body.mode, strict=body.strict)
    except FileNotFoundError as exc:
        raise HTTPException(503, str(exc)) from exc
    payload = result.model_dump()
    payload["trace_id"] = result.trace.trace_id
    return payload


def _traced(**fields) -> dict:
    return {"trace_id": new_trace_id(), **fields}


def _require_doc_id(doc_id: str) -> str:
    if not DOC_ID_RE.match(doc_id):
        raise HTTPException(400, f"invalid doc_id {doc_id!r}")
    return doc_id


def _manifest(root: Path) -> dict:
    path = root / "manifest.json"
    if not path.is_file():
        raise HTTPException(404, "manifest missing")
    return json.loads(path.read_text(encoding="utf-8"))


def _load_regions(root: Path, doc_id: str, page: int | None = None) -> list[Region]:
    path = under_root(root, "regions", f"{_require_doc_id(doc_id)}.json")
    if not path.is_file():
        raise HTTPException(404, "regions missing")
    regions = [Region.model_validate(item) for item in json.loads(path.read_text(encoding="utf-8"))]
    if page is None:
        return regions
    return [region for region in regions if region.page == page]


def _find_region(root: Path, doc_id: str, page: int, region_id: str) -> Region:
    for region in _load_regions(root, doc_id, page):
        if region.region_id == region_id:
            return region
    raise HTTPException(404, "region not found")


def _table_counts(uri: Path) -> tuple[bool, dict[str, int]]:
    if not uri.exists():
        return False, {}
    db = lancedb.connect(str(uri))
    counts = {
        name: db.open_table(name).to_arrow().num_rows for name in sorted(table_names(db))
    }
    return True, counts
