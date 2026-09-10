import json

from pageanchor.eval.run import run_eval
from pageanchor.ground.answer import apply_strict
from pageanchor.ids import new_trace_id
from pageanchor.models import Citation, GroundedAnswer, PageHit, Trace


def _answer(mode: str, *, abstain: bool, verified: bool) -> GroundedAnswer:
    cite = Citation(
        doc_id="hello",
        page=1,
        region_id="hello:p1:r0",
        bbox=(0.1, 0.1, 0.2, 0.2),
        quote="THE_TOKEN_42",
        verified=verified,
    )
    return GroundedAnswer(
        question="token?",
        answer=None if abstain else "THE_TOKEN_42",
        abstain=abstain,
        abstain_reason="verify_failed" if abstain else None,
        citations=[cite],
        trace=Trace(
            trace_id=new_trace_id(),
            retrieval_mode=mode if mode in {"text", "visual", "hybrid"} else "hybrid",
            hits=[PageHit(doc_id="hello", page=1, score=1.0, source="text")],
        ),
    )


def test_run_eval_hybrid_verify_reuses_hybrid_answers(tmp_path, monkeypatch):
    gold = tmp_path / "gold.jsonl"
    gold.write_text(
        json.dumps(
            {
                "id": "q1",
                "question": "token?",
                "answerable": True,
                "gold_doc_id": "hello",
                "gold_pages": [1],
                "gold_quote": "THE_TOKEN_42",
                "type": "plain_text",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    calls: list[str] = []

    def fake_ga(question, mode, strict=True, **kwargs):
        calls.append(mode)
        return _answer(mode, abstain=False, verified=False)

    monkeypatch.setattr("pageanchor.eval.run.grounded_answer", fake_ga)
    out = tmp_path / "out"
    results = run_eval(str(gold), ["hybrid", "hybrid+verify"], str(out))
    assert calls == ["hybrid"]
    assert results["hybrid"]["answers"][0]["abstain"] is False
    assert results["hybrid+verify"]["answers"][0]["abstain"] is True
    assert results["hybrid+verify"]["answers"][0]["abstain_reason"] == "verify_failed"
    strict = apply_strict(_answer("hybrid", abstain=False, verified=False))
    assert strict.abstain is True


def test_report_lists_wrong_citation_page():
    from pageanchor.eval.report import render_report

    gold = [
        {
            "id": "q011",
            "question": "CoLA n?",
            "answerable": True,
            "gold_doc_id": "glue",
            "gold_pages": [2],
            "gold_quote": "CoLA 8.5k",
            "type": "table",
        }
    ]
    answer = _answer("text", abstain=False, verified=True)
    answer = answer.model_copy(
        update={
            "answer": "8.5k",
            "citations": [
                answer.citations[0].model_copy(
                    update={
                        "doc_id": "glue",
                        "page": 8,
                        "quote": "Single-Task Training",
                    }
                )
            ],
        }
    )
    md = render_report(
        {
            "text": {
                "metrics": {
                    "recall_at_5": 0.0,
                    "citation_page_hit": 0.0,
                    "verify_pass_rate": 1.0,
                    "abstain_precision": 0.0,
                    "abstain_recall": 0.0,
                    "latency_p50_ms": 1.0,
                },
                "answers": [answer],
            }
        },
        gold,
    )
    assert "| q011 | table | glue p.8 | glue p.2 |" in md
    assert "8.5k" in md
