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
