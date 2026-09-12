from __future__ import annotations

import re

from pageanchor.ground.verify import answer_in_quote, verify_quote
from pageanchor.models import Citation, GroundedAnswer, PageHit, ScoredRegion
from pageanchor.retrieve.rerank import cue_boost

_YEAR_RE = re.compile(r"\b(\d{4})\b")
_TOKEN_RE = re.compile(r"[a-z0-9]+")

DEFAULT_CORPUS_TITLES = {
    "adam": "arxiv-1412-adam",
    "colpali": "arxiv-2407-colpali",
    "layoutlmv3": "arxiv-2204-layoutlmv3",
    "glue": "arxiv-1804-glue",
    "mmwr": "cdc-mmwr-7331a1",
    "cpi": "bls-cpi-20250115",
}


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


def _region_score(question: str, region: ScoredRegion) -> float:
    return _cue_score(question, region) + _token_overlap(question, region.text)


def _named_title_docs(
    question: str, corpus_titles: dict[str, str]
) -> list[str]:
    return [
        doc_id
        for token, doc_id in corpus_titles.items()
        if re.search(rf"\b{re.escape(token)}\b", question, re.IGNORECASE)
    ]


def _shortest_answer_quote(answer: str, region_text: str) -> str:
    index = region_text.find(answer)
    if index >= 0:
        return answer
    # ponytail: O(n^2) window scan; regions stay short. Upgrade if quotes need NFKC mapping.
    for length in range(len(answer), len(region_text) + 1):
        for start in range(0, len(region_text) - length + 1):
            window = region_text[start : start + length]
            if verify_quote(answer, window):
                return window
    return answer


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
    if answer is None or not verify_quote(answer, cited.text):
        return cited
    best = cited
    best_score = _region_score(question, cited)
    for region in candidates:
        if region.doc_id != cited.doc_id:
            continue
        if not verify_quote(answer, region.text):
            continue
        score = _region_score(question, region)
        if score > best_score or (score == best_score and region.page < best.page):
            best = region
            best_score = score
    return best


def apply_canonical(
    answer: GroundedAnswer, candidates: list[ScoredRegion]
) -> GroundedAnswer:
    by_id = {region.region_id: region for region in candidates}
    rewritten: list[Citation] = []
    for citation in answer.citations:
        cited = by_id.get(citation.region_id)
        if cited is None:
            rewritten.append(citation)
            continue
        canon = canonical_region(answer.answer, cited, candidates, answer.question)
        quote = citation.quote
        if canon.region_id != cited.region_id and not verify_quote(quote, canon.text):
            if answer.answer is not None and verify_quote(answer.answer, canon.text):
                quote = _shortest_answer_quote(answer.answer, canon.text)
        qin = verify_quote(quote, canon.text)
        ain = answer_in_quote(answer.answer, quote)
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

    result = answer.model_copy(update={"citations": rewritten})
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
