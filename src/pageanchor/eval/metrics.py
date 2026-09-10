from __future__ import annotations

import statistics

from pageanchor.ground.verify import answer_in_quote, verify_quote
from pageanchor.models import GroundedAnswer

_ABSTAIN_REASONS = (
    "unanswerable",
    "verify_failed",
    "unsupported",
    "generator_invalid",
    "no_hits",
)


def score_run(
    gold: list[dict],
    answers: list[GroundedAnswer],
    latencies_ms: list[float],
) -> dict:
    if len(gold) != len(answers):
        raise ValueError("gold and answers must be the same length")
    pairs = list(zip(gold, answers, strict=True))
    answerable = [(row, answer) for row, answer in pairs if row["answerable"]]
    unanswerable = [(row, answer) for row, answer in pairs if not row["answerable"]]

    recall_hits = 0
    for row, answer in answerable:
        gold_pages = set(row["gold_pages"])
        gold_doc = row["gold_doc_id"]
        if any(
            hit.doc_id == gold_doc and hit.page in gold_pages for hit in answer.trace.hits[:5]
        ):
            recall_hits += 1
    recall_at_5 = recall_hits / len(answerable) if answerable else 0.0

    cite_hits = 0
    cite_n = 0
    for row, answer in answerable:
        if not answer.citations:
            continue
        cite_n += 1
        gold_pages = set(row["gold_pages"])
        if any(
            citation.doc_id == row["gold_doc_id"] and citation.page in gold_pages
            for citation in answer.citations
        ):
            cite_hits += 1
    citation_page_hit = cite_hits / cite_n if cite_n else 0.0

    kept_citations = [
        citation for answer in answers if not answer.abstain for citation in answer.citations
    ]
    if kept_citations:
        verify_pass_rate = sum(citation.verified for citation in kept_citations) / len(
            kept_citations
        )
        quote_support_rate = sum(citation.answer_in_quote for citation in kept_citations) / len(
            kept_citations
        )
    else:
        empty = 1.0 if answers and all(answer.abstain for answer in answers) else 0.0
        verify_pass_rate = empty
        quote_support_rate = empty

    abstained = [answer for answer in answers if answer.abstain]
    true_positives = sum(1 for row, answer in pairs if answer.abstain and not row["answerable"])
    abstain_precision = true_positives / len(abstained) if abstained else 0.0
    abstain_recall = true_positives / len(unanswerable) if unanswerable else 0.0

    region_n = 0
    region_hits = 0
    for row, answer in answerable:
        quote = str(row.get("gold_quote") or "")
        if not quote:
            continue
        region_n += 1
        if any(verify_quote(quote, region.text) for region in answer.trace.regions):
            region_hits += 1
    region_hit = region_hits / region_n if region_n else 0.0

    match_n = 0
    match_hits = 0
    for row, answer in answerable:
        expected = row.get("gold_answer")
        if not expected or answer.abstain or answer.answer is None:
            continue
        match_n += 1
        if answer_in_quote(str(expected), answer.answer):
            match_hits += 1
    answer_match = match_hits / match_n if match_n else 0.0

    abstain_by_reason = {
        "answerable": {reason: 0.0 for reason in _ABSTAIN_REASONS},
        "unanswerable": {reason: 0.0 for reason in _ABSTAIN_REASONS},
    }
    for row, answer in pairs:
        if not answer.abstain:
            continue
        bucket = "answerable" if row["answerable"] else "unanswerable"
        reason = answer.abstain_reason
        if reason in abstain_by_reason[bucket]:
            abstain_by_reason[bucket][reason] += 1.0

    return {
        "n": float(len(gold)),
        "recall_at_5": recall_at_5,
        "citation_page_hit": citation_page_hit,
        "verify_pass_rate": verify_pass_rate,
        "quote_support_rate": quote_support_rate,
        "region_hit": region_hit,
        "answer_match": answer_match,
        "abstain_precision": abstain_precision,
        "abstain_recall": abstain_recall,
        "abstain_by_reason": abstain_by_reason,
        "latency_p50_ms": float(statistics.median(latencies_ms)) if latencies_ms else 0.0,
    }
