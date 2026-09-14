from __future__ import annotations

import re
import unicodedata

from pageanchor.ground.verify import answer_in_quote, verify_quote
from pageanchor.models import Citation, GroundedAnswer, PageHit, ScoredRegion, VerifyResult
from pageanchor.retrieve.rerank import cue_boost

_YEAR_RE = re.compile(r"\b(\d{4})\b")
_TOKEN_RE = re.compile(r"[a-z0-9]+")
_WS_RE = re.compile(r"\s+")

DEFAULT_CORPUS_TITLES = {
    "adam": "arxiv-1412-adam",
    "colpali": "arxiv-2407-colpali",
    "layoutlmv3": "arxiv-2204-layoutlmv3",
    "glue": "arxiv-1804-glue",
    "mmwr": "cdc-mmwr-7331a1",
    "cpi": "bls-cpi-20250115",
}


def _fold(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    return _WS_RE.sub(" ", text).strip().casefold()


def _folded_in(answer: str | None, text: str) -> bool:
    if not answer:
        return False
    needle = _fold(answer)
    return bool(needle) and needle in _fold(text)


def _alnum_tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


def _token_overlap(question: str, text: str) -> float:
    left = _alnum_tokens(question)
    right = _alnum_tokens(text)
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _cue_score(question: str, region: ScoredRegion) -> float:
    hit = PageHit(doc_id=region.doc_id, page=region.page, score=0.0, source="hybrid")
    return cue_boost(question, hit, [region.text])


def _named_title_docs(question: str, corpus_titles: dict[str, str]) -> list[str]:
    return [
        doc_id
        for token, doc_id in corpus_titles.items()
        if re.search(rf"\b{re.escape(token)}\b", question, re.IGNORECASE)
    ]


def _shortest_folded_span(answer: str, region_text: str) -> str:
    target = _fold(answer)
    if not target:
        return answer
    if answer in region_text:
        return answer
    for length in range(len(answer), len(region_text) + 1):
        for start in range(0, len(region_text) - length + 1):
            window = region_text[start : start + length]
            if _fold(window) == target:
                return window
    for length in range(len(answer), len(region_text) + 1):
        for start in range(0, len(region_text) - length + 1):
            window = region_text[start : start + length]
            if target in _fold(window):
                return window
    return answer


def _region_score(
    question: str, region: ScoredRegion, max_len: int
) -> float:
    length_term = (len(region.text) / max_len) if max_len else 0.0
    return _cue_score(question, region) + _token_overlap(question, region.text) + length_term


def question_constraints(
    question: str, *, corpus_titles: dict[str, str] | None = None
) -> None | str:
    titles = DEFAULT_CORPUS_TITLES if corpus_titles is None else corpus_titles
    years = _YEAR_RE.findall(question)
    named = [
        token
        for token in titles
        if re.search(rf"\b{re.escape(token)}\b", question, re.IGNORECASE)
    ]
    if not years and not named:
        return None
    return "|".join([*years, *named])


def canonical_region(
    answer: str | None,
    cited: ScoredRegion,
    candidates: list[ScoredRegion],
    question: str,
) -> ScoredRegion:
    if not _folded_in(answer, cited.text):
        return cited
    matches = [
        region
        for region in candidates
        if region.doc_id == cited.doc_id and _folded_in(answer, region.text)
    ]
    if not matches:
        return cited
    max_len = max(len(region.text) for region in matches)
    best = matches[0]
    best_score = _region_score(question, best, max_len)
    for region in matches[1:]:
        score = _region_score(question, region, max_len)
        if score > best_score or (score == best_score and region.page > best.page):
            best = region
            best_score = score
    return best


def _rewrite_citation(
    answer_text: str | None,
    quote: str,
    cited: ScoredRegion,
    canon: ScoredRegion,
) -> tuple[str | None, str, ScoredRegion] | None:
    if canon.region_id == cited.region_id:
        return None
    if answer_text is None or not _folded_in(answer_text, canon.text):
        return None
    span = _shortest_folded_span(answer_text, canon.text)
    new_quote = quote if verify_quote(quote, canon.text) else span
    new_answer = span
    if not verify_quote(new_quote, canon.text) or not answer_in_quote(new_answer, new_quote):
        return None
    return new_answer, new_quote, canon


def apply_canonical(
    answer: GroundedAnswer, candidates: list[ScoredRegion]
) -> GroundedAnswer:
    by_id = {region.region_id: region for region in candidates}
    rewritten: list[Citation] = []
    new_answer = answer.answer
    for citation in answer.citations:
        cited = by_id.get(citation.region_id)
        if cited is None:
            rewritten.append(citation)
            continue
        canon = canonical_region(answer.answer, cited, candidates, answer.question)
        adopted = _rewrite_citation(answer.answer, citation.quote, cited, canon)
        if adopted is None:
            rewritten.append(citation)
            continue
        new_answer, quote, canon = adopted
        qin = verify_quote(quote, canon.text)
        ain = answer_in_quote(new_answer, quote)
        rewritten.append(
            Citation(
                doc_id=canon.doc_id,
                page=canon.page,
                region_id=canon.region_id,
                bbox=canon.bbox,
                quote=quote,
                verified=qin and ain,
                quote_in_region=qin,
                answer_in_quote=ain,
            )
        )

    verify_rows = [
        VerifyResult(
            ok=citation.verified,
            quote=citation.quote,
            matched_text=citation.quote if citation.quote_in_region else None,
            doc_id=citation.doc_id,
            page=citation.page,
            region_id=citation.region_id or "",
            quote_in_region=citation.quote_in_region,
            answer_in_quote=citation.answer_in_quote,
        )
        for citation in rewritten
    ]
    result = answer.model_copy(
        update={
            "answer": new_answer,
            "citations": rewritten,
            "trace": answer.trace.model_copy(update={"verify": verify_rows}),
        }
    )
    if question_constraints(answer.question) is None or not rewritten:
        return result

    titles = DEFAULT_CORPUS_TITLES
    years = _YEAR_RE.findall(answer.question)
    if years:
        texts = [
            by_id[citation.region_id].text
            for citation in rewritten
            if citation.region_id in by_id
        ]
        if not any(all(year in text for year in years) for text in texts):
            return result.model_copy(
                update={"abstain": True, "abstain_reason": "unanswerable", "answer": None}
            )

    expected = list(dict.fromkeys(_named_title_docs(answer.question, titles)))
    if expected and any(citation.doc_id != expected[0] for citation in rewritten):
        return result.model_copy(
            update={"abstain": True, "abstain_reason": "unanswerable", "answer": None}
        )
    return result
