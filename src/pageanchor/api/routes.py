from __future__ import annotations

from pathlib import Path

import lancedb
from fastapi import APIRouter, Depends, HTTPException
from fastapi import Path as PathParam
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from pageanchor.api.deps import get_settings
from pageanchor.config import Settings
from pageanchor.corpus import (
    find_region,
    get_document,
    load_manifest,
    load_regions,
    page_png_path,
)
from pageanchor.ground.answer import grounded_answer
from pageanchor.ground.regions import select_regions
from pageanchor.ground.verify import verify_quote
from pageanchor.ids import new_trace_id
from pageanchor.ingest.index_text import table_names
from pageanchor.models import RetrievalMode
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
    return _traced(**_http_call(load_manifest, settings.corpus_root))


@router.get("/v1/docs/{doc_id}")
def doc_row(doc_id: str, settings: Settings = Depends(get_settings)) -> dict:
    return _traced(**_http_call(get_document, settings.corpus_root, doc_id))


@router.get("/v1/docs/{doc_id}/pages/{page}")
def page_png(
    doc_id: str,
    page: int = PathParam(ge=1),
    settings: Settings = Depends(get_settings),
) -> FileResponse:
    path = _http_call(page_png_path, settings.corpus_root, doc_id, page)
    return FileResponse(path, media_type="image/png")


@router.get("/v1/docs/{doc_id}/pages/{page}/regions")
def page_regions(
    doc_id: str,
    page: int = PathParam(ge=1),
    settings: Settings = Depends(get_settings),
) -> dict:
    regions = _http_call(load_regions, settings.corpus_root, doc_id, page)
    return _traced(regions=[region.model_dump() for region in regions])


@router.post("/v1/search")
def search(body: SearchBody) -> dict:
    modes = {"text": search_text, "visual": search_visual, "hybrid": search_hybrid}
    hits = _retrieve(modes[body.mode], body.query, body.k)
    return _traced(hits=[hit.model_dump() for hit in hits])


@router.post("/v1/evidence")
def evidence(body: EvidenceBody, settings: Settings = Depends(get_settings)) -> dict:
    regions = _http_call(
        select_regions,
        body.query,
        body.doc_id,
        body.page,
        body.max_regions,
        corpus_root=settings.corpus_root,
    )
    return _traced(regions=[region.model_dump() for region in regions])


@router.post("/v1/verify")
def verify(body: VerifyBody, settings: Settings = Depends(get_settings)) -> dict:
    region = _http_call(
        find_region, settings.corpus_root, body.doc_id, body.page, body.region_id
    )
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
    result = _retrieve(grounded_answer, body.question, body.mode, strict=body.strict)
    payload = result.model_dump()
    payload["trace_id"] = result.trace.trace_id
    return payload


def _traced(**fields) -> dict:
    return {"trace_id": new_trace_id(), **fields}


def _retrieve(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except (FileNotFoundError, ImportError) as exc:
        raise HTTPException(503, str(exc)) from exc


def _http_call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


def _table_counts(uri: Path) -> tuple[bool, dict[str, int]]:
    if not uri.exists():
        return False, {}
    db = lancedb.connect(str(uri))
    counts = {
        name: db.open_table(name).to_arrow().num_rows for name in sorted(table_names(db))
    }
    return True, counts
