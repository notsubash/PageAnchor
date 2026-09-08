from __future__ import annotations

import statistics

from pageanchor.models import GroundedAnswer


def score_run(
    gold: list[dict],
    answers: list[GroundedAnswer],
    latencies_ms: list[float],
) -> dict[str, float]:
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
    else:
        verify_pass_rate = 1.0 if answers and all(answer.abstain for answer in answers) else 0.0

    abstained = [answer for answer in answers if answer.abstain]
    true_positives = sum(1 for row, answer in pairs if answer.abstain and not row["answerable"])
    abstain_precision = true_positives / len(abstained) if abstained else 0.0
    abstain_recall = true_positives / len(unanswerable) if unanswerable else 0.0

    return {
        "n": float(len(gold)),
        "recall_at_5": recall_at_5,
        "citation_page_hit": citation_page_hit,
        "verify_pass_rate": verify_pass_rate,
        "abstain_precision": abstain_precision,
        "abstain_recall": abstain_recall,
        "latency_p50_ms": float(statistics.median(latencies_ms)) if latencies_ms else 0.0,
    }
