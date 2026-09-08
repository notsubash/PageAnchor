from pageanchor.eval.metrics import score_run
from pageanchor.ids import new_trace_id
from pageanchor.models import Citation, GroundedAnswer, PageHit, Trace


def _answer(
    question: str,
    *,
    abstain: bool,
    answer: str | None,
    hits: list[PageHit],
    citations: list[Citation],
    reason=None,
) -> GroundedAnswer:
    return GroundedAnswer(
        question=question,
        answer=answer,
        abstain=abstain,
        abstain_reason=reason,
        citations=citations,
        trace=Trace(trace_id=new_trace_id(), retrieval_mode="text", hits=hits),
    )


def test_score_run_recall_citation_verify_and_abstain():
    gold = [
        {
            "id": "q1",
            "question": "token?",
            "answerable": True,
            "gold_doc_id": "hello",
            "gold_pages": [1],
            "gold_quote": "THE_TOKEN_42",
            "type": "plain_text",
        },
        {
            "id": "q2",
            "question": "missing paper?",
            "answerable": False,
            "gold_doc_id": None,
            "gold_pages": [],
            "gold_quote": "",
            "type": "unanswerable",
        },
    ]
    cite = Citation(
        doc_id="hello",
        page=1,
        region_id="hello:p1:r0",
        bbox=(0.1, 0.1, 0.2, 0.2),
        quote="THE_TOKEN_42",
        verified=True,
    )
    answers = [
        _answer(
            "token?",
            abstain=False,
            answer="THE_TOKEN_42",
            hits=[PageHit(doc_id="hello", page=1, score=1.0, source="text")],
            citations=[cite],
        ),
        _answer(
            "missing paper?",
            abstain=True,
            answer=None,
            hits=[],
            citations=[],
            reason="unanswerable",
        ),
    ]
    metrics = score_run(gold, answers, latencies_ms=[10.0, 30.0])
    assert metrics["recall_at_5"] == 1.0
    assert metrics["citation_page_hit"] == 1.0
    assert metrics["verify_pass_rate"] == 1.0
    assert metrics["abstain_precision"] == 1.0
    assert metrics["abstain_recall"] == 1.0
    assert metrics["latency_p50_ms"] == 20.0
