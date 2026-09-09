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
