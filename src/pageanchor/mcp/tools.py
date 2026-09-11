from __future__ import annotations

from typing import Annotated, Any

from mcp.server import MCPServer
from pydantic import Field

from pageanchor.config import load_settings
from pageanchor.corpus import find_region, load_regions
from pageanchor.ground.answer import grounded_answer as run_grounded_answer
from pageanchor.ground.receipt import build_receipt
from pageanchor.ground.regions import select_regions
from pageanchor.ground.verify import verify_quote as quote_in_region
from pageanchor.ids import new_trace_id
from pageanchor.models import GroundedAnswer, OverlayMode, Receipt, RetrievalMode
from pageanchor.retrieve.hybrid import search_hybrid
from pageanchor.retrieve.text import search_text
from pageanchor.retrieve.visual import search_visual

_FACT_RULE = (
    "Do not state a fact until verify_quote is true. "
    "Do not guess page content; call select_evidence."
)


def register_tools(mcp: MCPServer) -> None:
    @mcp.tool(description="Search the frozen corpus and return page hits. " + _FACT_RULE)
    def search_documents(
        query: str,
        k: Annotated[int, Field(ge=1)] = 5,
        mode: OverlayMode = "hybrid",
    ) -> dict[str, Any]:
        hits = {
            "text": search_text,
            "visual": search_visual,
            "hybrid": search_hybrid,
        }[mode](query, k)
        return {"trace_id": new_trace_id(), "hits": [hit.model_dump() for hit in hits]}

    @mcp.tool(description="Load stored layout regions for a page. " + _FACT_RULE)
    def get_page_regions(
        doc_id: str,
        page: Annotated[int, Field(ge=1)],
    ) -> dict[str, Any]:
        regions = load_regions(load_settings().corpus_root, doc_id, page)
        return {
            "trace_id": new_trace_id(),
            "regions": [region.model_dump() for region in regions],
        }

    @mcp.tool(
        description="Rank layout regions on a page by overlap with the query. " + _FACT_RULE
    )
    def select_evidence(
        query: str,
        doc_id: str,
        page: Annotated[int, Field(ge=1)],
        max_regions: Annotated[int, Field(ge=1)] = 5,
    ) -> dict[str, Any]:
        regions = select_regions(
            query,
            doc_id,
            page,
            max_regions=max_regions,
            corpus_root=load_settings().corpus_root,
        )
        return {
            "trace_id": new_trace_id(),
            "regions": [region.model_dump() for region in regions],
        }

    @mcp.tool(
        description=(
            "Check that quote is a normalized substring of the stored region text. "
            + _FACT_RULE
        )
    )
    def verify_quote(
        quote: str,
        doc_id: str,
        page: Annotated[int, Field(ge=1)],
        region_id: str,
    ) -> dict[str, Any]:
        region = find_region(load_settings().corpus_root, doc_id, page, region_id)
        ok = quote_in_region(quote, region.text)
        return {
            "trace_id": new_trace_id(),
            "ok": ok,
            "quote": quote,
            "matched_text": quote if ok else None,
            "doc_id": region.doc_id,
            "page": region.page,
            "region_id": region.region_id,
        }

    @mcp.tool(
        name="grounded_answer",
        description=(
            "Same GroundedAnswer object as the CLI and HTTP API. "
            + _FACT_RULE
            + " Prefer search_documents then select_evidence then verify_quote."
        ),
    )
    def call_grounded_answer(
        question: str,
        mode: RetrievalMode = "hybrid",
        strict: bool = True,
    ) -> GroundedAnswer:
        return run_grounded_answer(question, mode, strict=strict)

    @mcp.tool(
        description="Export a citation receipt with PDF hashes. " + _FACT_RULE
    )
    def export_receipt(answer: GroundedAnswer) -> Receipt:
        return build_receipt(answer)
