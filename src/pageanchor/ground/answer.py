from __future__ import annotations

import json
import time
from collections.abc import Callable

from pydantic import BaseModel, Field

from pageanchor.config import generator_client, load_settings
from pageanchor.ground.regions import select_regions
from pageanchor.ground.verify import answer_in_quote, verify_quote
from pageanchor.ids import new_trace_id
from pageanchor.models import (
    AbstainReason,
    Citation,
    GroundedAnswer,
    PageHit,
    RetrievalMode,
    ScoredRegion,
    Trace,
    VerifyResult,
)
from pageanchor.retrieve.hybrid import search_hybrid
from pageanchor.retrieve.text import search_text
from pageanchor.retrieve.visual import search_visual

GenerateFn = Callable[[str, list[ScoredRegion]], "GeneratorOutput"]


class GeneratorCitation(BaseModel):
    region_id: str
    quote: str


class GeneratorOutput(BaseModel):
    answer: str | None = None
    abstain: bool = False
    abstain_reason: AbstainReason | None = None
    citations: list[GeneratorCitation] = Field(default_factory=list)


_SYSTEM = """You answer only from the provided regions.
Reply with one JSON object with keys answer, abstain, abstain_reason, citations.
citations is a list of {region_id, quote} objects. answer is a string or null.
Rules:
- Each citation.quote must be a verbatim substring of that region's text.
- citation.region_id must be one of the provided region_id values.
- The answer string must be a verbatim substring of at least one citation.quote.
  Use a short extractive span (a name, a number, a title), not a paraphrase.
- If the regions do not contain the answer, abstain=true,
  abstain_reason="unanswerable", answer=null, citations=[].
- Otherwise set abstain=false, a short answer, and at least one citation.
The model may only use abstain_reason "unanswerable". Other reasons are set
by the system after verify.
"""


def grounded_answer(
    question: str,
    mode: RetrievalMode = "hybrid",
    strict: bool = True,
    *,
    hits: list[PageHit] | None = None,
    regions: list[ScoredRegion] | None = None,
    generate: GenerateFn | None = None,
    k: int = 5,
) -> GroundedAnswer:
    started = time.perf_counter()
    timings: dict[str, float] = {}
    trace_id = new_trace_id()
    search_fn = {"text": search_text, "visual": search_visual, "hybrid": search_hybrid}.get(mode)
    if search_fn is None:
        raise ValueError(f"retrieval mode {mode!r} is not implemented yet")

    search_started = time.perf_counter()
    if hits is None:
        hits = search_fn(question, k)
    timings["search_ms"] = (time.perf_counter() - search_started) * 1000

    if not hits:
        timings["total_ms"] = (time.perf_counter() - started) * 1000
        return GroundedAnswer(
            question=question,
            answer=None,
            abstain=True,
            abstain_reason="no_hits",
            citations=[],
            trace=Trace(
                trace_id=trace_id,
                retrieval_mode=mode,
                hits=[],
                timings_ms=timings,
            ),
        )

    select_started = time.perf_counter()
    if regions is None:
        pool: list[ScoredRegion] = []
        seen: set[tuple[str, int]] = set()
        for hit in hits:
            key = (hit.doc_id, hit.page)
            if key in seen:
                continue
            seen.add(key)
            pool.extend(select_regions(question, hit.doc_id, hit.page, max_regions=50))
        pool.sort(key=lambda region: (-region.score, region.region_id))
        regions = pool[:5]
    timings["select_ms"] = (time.perf_counter() - select_started) * 1000

    generate_started = time.perf_counter()
    generate_fn = generate or _generate_deepseek
    try:
        generated = generate_fn(question, regions)
    except Exception:
        generated = None
    timings["generate_ms"] = (time.perf_counter() - generate_started) * 1000
    return _apply_policy(
        question,
        mode,
        strict,
        generated,
        hits,
        regions,
        trace_id,
        timings,
        started,
    )


def apply_strict(answer: GroundedAnswer) -> GroundedAnswer:
    if answer.abstain:
        return answer
    if any(not citation.quote_in_region for citation in answer.citations):
        return answer.model_copy(
            update={"abstain": True, "abstain_reason": "verify_failed", "answer": None}
        )
    if not any(citation.answer_in_quote for citation in answer.citations):
        return answer.model_copy(
            update={"abstain": True, "abstain_reason": "unsupported", "answer": None}
        )
    return answer


def _apply_policy(
    question: str,
    mode: RetrievalMode,
    strict: bool,
    generated: GeneratorOutput | None,
    hits: list[PageHit],
    regions: list[ScoredRegion],
    trace_id: str,
    timings: dict[str, float],
    started: float,
) -> GroundedAnswer:
    citations: list[Citation] = []
    verify_rows: list[VerifyResult] = []
    unknown = generated is None
    if generated is not None:
        by_id = {region.region_id: region for region in regions}
        for item in generated.citations:
            region = by_id.get(item.region_id)
            if region is None:
                unknown = True
                continue
            qin = verify_quote(item.quote, region.text)
            ain = answer_in_quote(generated.answer, item.quote)
            citations.append(
                Citation(
                    doc_id=region.doc_id,
                    page=region.page,
                    region_id=region.region_id,
                    bbox=region.bbox,
                    quote=item.quote,
                    verified=qin and ain,
                    quote_in_region=qin,
                    answer_in_quote=ain,
                )
            )
            verify_rows.append(
                VerifyResult(
                    ok=qin and ain,
                    quote=item.quote,
                    matched_text=item.quote if qin else None,
                    doc_id=region.doc_id,
                    page=region.page,
                    region_id=region.region_id,
                    quote_in_region=qin,
                    answer_in_quote=ain,
                )
            )

    abstain = False
    reason: AbstainReason | None = None
    answer_text = generated.answer if generated is not None else None
    if unknown:
        abstain, reason, answer_text = True, "generator_invalid", None
    elif citations and strict and any(not citation.quote_in_region for citation in citations):
        abstain, reason, answer_text = True, "verify_failed", None
    elif citations and strict and not any(citation.answer_in_quote for citation in citations):
        abstain, reason, answer_text = True, "unsupported", None
    elif generated.abstain:
        abstain, reason, answer_text = True, "unanswerable", None
    elif not citations or generated.answer is None:
        abstain, reason, answer_text = True, "generator_invalid", None

    timings["total_ms"] = (time.perf_counter() - started) * 1000
    return GroundedAnswer(
        question=question,
        answer=answer_text,
        abstain=abstain,
        abstain_reason=reason,
        citations=citations,
        trace=Trace(
            trace_id=trace_id,
            retrieval_mode=mode,
            hits=hits,
            regions=regions,
            verify=verify_rows,
            timings_ms=timings,
        ),
    )


def _generate_deepseek(question: str, regions: list[ScoredRegion]) -> GeneratorOutput:
    settings = load_settings()
    client = generator_client(settings)
    payload = {
        "question": question,
        "regions": [
            {
                "region_id": region.region_id,
                "doc_id": region.doc_id,
                "page": region.page,
                "bbox": list(region.bbox),
                "type": region.type,
                "text": region.text,
            }
            for region in regions
        ],
    }
    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": json.dumps(payload)},
    ]
    try:
        completion = client.beta.chat.completions.parse(
            model=settings.generator_model,
            messages=messages,
            response_format=GeneratorOutput,
            extra_body={"thinking": {"type": "disabled"}},
        )
        parsed = completion.choices[0].message.parsed
        if parsed is not None:
            return parsed
    except Exception:
        pass
    completion = client.chat.completions.create(
        model=settings.generator_model,
        messages=messages,
        response_format={"type": "json_object"},
        extra_body={"thinking": {"type": "disabled"}},
    )
    content = completion.choices[0].message.content or ""
    return GeneratorOutput.model_validate_json(content)
