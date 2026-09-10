from pageanchor.ground.answer import GeneratorCitation, GeneratorOutput, grounded_answer
from pageanchor.ids import region_id
from pageanchor.models import PageHit, ScoredRegion


def _region(text: str, index: int = 0) -> ScoredRegion:
    return ScoredRegion(
        doc_id="hello",
        page=1,
        region_id=region_id("hello", 1, index),
        type="text",
        bbox=(0.1, 0.1, 0.5, 0.2),
        text=text,
        score=1.0,
    )


def test_empty_hits_abstain_no_hits():
    result = grounded_answer("anything", "text", hits=[])
    assert result.abstain is True
    assert result.abstain_reason == "no_hits"
    assert result.answer is None
    assert result.citations == []


def test_empty_hits_visual_and_hybrid_keep_mode():
    for mode in ("visual", "hybrid"):
        result = grounded_answer("anything", mode, hits=[])
        assert result.abstain_reason == "no_hits"
        assert result.trace.retrieval_mode == mode


def test_bad_quote_abstains_when_strict():
    region = _region("THE_TOKEN_42 is on the page")

    def fake_generate(question, regions):
        return GeneratorOutput(
            answer="42",
            citations=[
                GeneratorCitation(region_id=region.region_id, quote="not in the region")
            ],
        )

    result = grounded_answer(
        "What is the token?",
        "text",
        strict=True,
        hits=[PageHit(doc_id="hello", page=1, score=1.0, source="text")],
        regions=[region],
        generate=fake_generate,
    )
    assert result.abstain is True
    assert result.abstain_reason == "verify_failed"
    assert result.answer is None
    assert result.citations[0].verified is False


def test_bad_quote_keeps_answer_when_not_strict():
    region = _region("THE_TOKEN_42 is on the page")

    def fake_generate(question, regions):
        return GeneratorOutput(
            answer="42",
            citations=[
                GeneratorCitation(region_id=region.region_id, quote="not in the region")
            ],
        )

    result = grounded_answer(
        "What is the token?",
        "text",
        strict=False,
        hits=[PageHit(doc_id="hello", page=1, score=1.0, source="text")],
        regions=[region],
        generate=fake_generate,
    )
    assert result.abstain is False
    assert result.answer == "42"
    assert result.citations[0].verified is False


def test_unknown_region_id_is_generator_invalid():
    region = _region("THE_TOKEN_42 is on the page")

    def fake_generate(question, regions):
        return GeneratorOutput(
            answer="42",
            citations=[GeneratorCitation(region_id="hello:p9:r99", quote="THE_TOKEN_42")],
        )

    result = grounded_answer(
        "What is the token?",
        "text",
        hits=[PageHit(doc_id="hello", page=1, score=1.0, source="text")],
        regions=[region],
        generate=fake_generate,
    )
    assert result.abstain is True
    assert result.abstain_reason == "generator_invalid"
    assert result.answer is None


def test_verified_quote_keeps_answer():
    region = _region("Hello THE_TOKEN_42")

    def fake_generate(question, regions):
        return GeneratorOutput(
            answer="THE_TOKEN_42",
            citations=[
                GeneratorCitation(region_id=region.region_id, quote="THE_TOKEN_42")
            ],
        )

    result = grounded_answer(
        "What is the token?",
        "text",
        hits=[PageHit(doc_id="hello", page=1, score=1.0, source="text")],
        regions=[region],
        generate=fake_generate,
    )
    assert result.abstain is False
    assert result.answer == "THE_TOKEN_42"
    assert result.citations[0].verified is True
    assert result.citations[0].bbox == region.bbox


def test_model_no_hits_reason_becomes_unanswerable():
    region = _region("THE_TOKEN_42 is on the page")

    def fake_generate(question, regions):
        return GeneratorOutput(answer=None, abstain=True, abstain_reason="no_hits")

    result = grounded_answer(
        "What is the token?",
        "text",
        hits=[PageHit(doc_id="hello", page=1, score=1.0, source="text")],
        regions=[region],
        generate=fake_generate,
    )
    assert result.abstain is True
    assert result.abstain_reason == "unanswerable"


def test_verify_failed_wins_over_model_abstain():
    region = _region("THE_TOKEN_42 is on the page")

    def fake_generate(question, regions):
        return GeneratorOutput(
            answer="42",
            abstain=True,
            abstain_reason="unanswerable",
            citations=[
                GeneratorCitation(region_id=region.region_id, quote="not in the region")
            ],
        )

    result = grounded_answer(
        "What is the token?",
        "text",
        strict=True,
        hits=[PageHit(doc_id="hello", page=1, score=1.0, source="text")],
        regions=[region],
        generate=fake_generate,
    )
    assert result.abstain is True
    assert result.abstain_reason == "verify_failed"
    assert result.citations[0].verified is False


def test_answer_not_in_quote_abstains_unsupported_when_strict():
    region = _region("Single-Task Training on headings")

    def fake_generate(question, regions):
        return GeneratorOutput(
            answer="8.5k",
            citations=[
                GeneratorCitation(
                    region_id=region.region_id, quote="Single-Task Training"
                )
            ],
        )

    result = grounded_answer(
        "How many CoLA training examples?",
        "text",
        strict=True,
        hits=[PageHit(doc_id="hello", page=1, score=1.0, source="text")],
        regions=[region],
        generate=fake_generate,
    )
    assert result.abstain is True
    assert result.abstain_reason == "unsupported"
    assert result.answer is None
    assert result.citations[0].quote_in_region is True
    assert result.citations[0].answer_in_quote is False
    assert result.citations[0].verified is False
    assert result.citations[0].bbox == region.bbox


def test_extractive_answer_passes_nested_verify():
    region = _region("CoLA 8.5k train examples")

    def fake_generate(question, regions):
        return GeneratorOutput(
            answer="8.5k",
            citations=[
                GeneratorCitation(region_id=region.region_id, quote="CoLA 8.5k")
            ],
        )

    result = grounded_answer(
        "How many CoLA training examples?",
        "text",
        strict=True,
        hits=[PageHit(doc_id="hello", page=1, score=1.0, source="text")],
        regions=[region],
        generate=fake_generate,
    )
    assert result.abstain is False
    assert result.answer == "8.5k"
    assert result.citations[0].verified is True
    assert result.citations[0].quote_in_region is True
    assert result.citations[0].answer_in_quote is True


def test_apply_strict_maps_support_fail_to_unsupported():
    from pageanchor.ground.answer import apply_strict
    from pageanchor.ids import new_trace_id
    from pageanchor.models import Citation, GroundedAnswer, Trace

    answer = GroundedAnswer(
        question="n?",
        answer="8.5k",
        abstain=False,
        citations=[
            Citation(
                doc_id="hello",
                page=1,
                region_id="hello:p1:r0",
                bbox=(0.1, 0.1, 0.5, 0.2),
                quote="Single-Task Training",
                verified=False,
                quote_in_region=True,
                answer_in_quote=False,
            )
        ],
        trace=Trace(trace_id=new_trace_id(), retrieval_mode="hybrid"),
    )
    strict = apply_strict(answer)
    assert strict.abstain is True
    assert strict.abstain_reason == "unsupported"
    assert strict.answer is None
