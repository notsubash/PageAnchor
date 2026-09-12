from pageanchor.ground.answer import GeneratorCitation, GeneratorOutput, grounded_answer
from pageanchor.ids import region_id
from pageanchor.models import PageHit, ScoredRegion
from pageanchor.retrieve.rerank import POOL_K


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


def test_select_evidence_visual_flag_follows_env(monkeypatch):
    seen: dict = {}

    def fake_select(question, hits, **kwargs):
        seen.clear()
        seen.update(kwargs)
        return []

    monkeypatch.setattr("pageanchor.ground.answer.select_evidence", fake_select)
    hits = [PageHit(doc_id="hello", page=1, score=1.0, source="text")]
    monkeypatch.delenv("PAGEANCHOR_VISUAL_REGIONS", raising=False)
    grounded_answer("q", "hybrid", hits=hits, generate=lambda q, r: GeneratorOutput())
    assert seen.get("visual") is True
    grounded_answer("q", "text", hits=hits, generate=lambda q, r: GeneratorOutput())
    assert seen.get("visual") is False
    monkeypatch.setenv("PAGEANCHOR_VISUAL_REGIONS", "1")
    grounded_answer("q", "text", hits=hits, generate=lambda q, r: GeneratorOutput())
    assert seen.get("visual") is False
    monkeypatch.setenv("PAGEANCHOR_VISUAL_REGIONS", "0")
    grounded_answer("q", "hybrid", hits=hits, generate=lambda q, r: GeneratorOutput())
    assert seen.get("visual") is False
    monkeypatch.delenv("PAGEANCHOR_VISUAL_REGIONS", raising=False)
    grounded_answer("q", "visual", hits=hits, generate=lambda q, r: GeneratorOutput())
    assert seen.get("visual") is True


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


def test_answer_in_one_of_two_quotes_is_supported():
    region_a = _region("CoLA 8.5k train examples", 0)
    region_b = _region("Single-Task Training on headings", 1)

    def fake_generate(question, regions):
        return GeneratorOutput(
            answer="8.5k",
            citations=[
                GeneratorCitation(region_id=region_a.region_id, quote="CoLA 8.5k"),
                GeneratorCitation(
                    region_id=region_b.region_id, quote="Single-Task Training"
                ),
            ],
        )

    result = grounded_answer(
        "How many CoLA training examples?",
        "text",
        strict=True,
        hits=[PageHit(doc_id="hello", page=1, score=1.0, source="text")],
        regions=[region_a, region_b],
        generate=fake_generate,
    )
    assert result.abstain is False
    assert result.answer == "8.5k"
    assert result.citations[0].answer_in_quote is True
    assert result.citations[1].answer_in_quote is False
    assert result.citations[0].verified is True
    assert result.citations[1].verified is False


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


def test_grounded_answer_search_uses_pool_k_and_reranks(monkeypatch):
    search_calls: list[int] = []
    select_hits: list[list[PageHit]] = []
    load_calls: list[tuple[str, int | None]] = []

    def fake_search(query, k, **kwargs):
        search_calls.append(k)
        return [
            PageHit(doc_id="arxiv-2407-colpali", page=1, score=0.8, source="hybrid"),
            PageHit(doc_id="arxiv-2407-colpali", page=5, score=0.7, source="hybrid"),
        ]

    def fake_select(question, hits, **kwargs):
        select_hits.append(list(hits))
        return []

    def fake_load_regions(root, doc_id: str, page: int | None = None):
        load_calls.append((doc_id, page))
        if doc_id == "arxiv-2407-colpali" and page == 7:
            from pageanchor.models import Region

            return [
                Region(
                    doc_id=doc_id,
                    page=page,
                    region_id=f"{doc_id}:p{page}:r0",
                    type="text",
                    bbox=(0.0, 0.0, 1.0, 1.0),
                    text="Table 2 results",
                )
            ]
        raise FileNotFoundError("regions missing")

    monkeypatch.setattr("pageanchor.ground.answer.search_hybrid", fake_search)
    monkeypatch.setattr("pageanchor.ground.answer.select_evidence", fake_select)
    monkeypatch.setattr("pageanchor.ground.answer.load_regions", fake_load_regions)
    result = grounded_answer(
        "What is the title on the first slide?",
        "hybrid",
        generate=lambda q, r: GeneratorOutput(),
    )
    assert search_calls == [POOL_K]
    assert len(select_hits) == 1
    select_pages = {(h.doc_id, h.page) for h in select_hits[0]}
    assert ("arxiv-2407-colpali", 3) in select_pages
    assert len(result.trace.hits) <= POOL_K
    assert len(result.trace.hits) > 2
    assert load_calls


def test_grounded_answer_injected_hits_skip_expand_rerank(monkeypatch):
    search_called = False
    select_hits: list[list[PageHit]] = []

    def fake_search(query, k, **kwargs):
        nonlocal search_called
        search_called = True
        return []

    def fake_select(question, hits, **kwargs):
        select_hits.append(list(hits))
        return []

    monkeypatch.setattr("pageanchor.ground.answer.search_hybrid", fake_search)
    monkeypatch.setattr("pageanchor.ground.answer.select_evidence", fake_select)
    injected = [PageHit(doc_id="hello", page=1, score=1.0, source="text")]
    grounded_answer(
        "q",
        "hybrid",
        hits=injected,
        generate=lambda q, r: GeneratorOutput(),
    )
    assert search_called is False
    assert select_hits == [injected]


def test_apply_strict_keeps_answer_if_any_quote_contains_it():
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
                quote="CoLA 8.5k",
                verified=True,
                quote_in_region=True,
                answer_in_quote=True,
            ),
            Citation(
                doc_id="hello",
                page=1,
                region_id="hello:p1:r1",
                bbox=(0.1, 0.1, 0.5, 0.2),
                quote="Single-Task Training",
                verified=False,
                quote_in_region=True,
                answer_in_quote=False,
            ),
        ],
        trace=Trace(trace_id=new_trace_id(), retrieval_mode="hybrid"),
    )
    strict = apply_strict(answer)
    assert strict.abstain is False
    assert strict.answer == "8.5k"
