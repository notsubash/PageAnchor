from pageanchor.ground.canonical import apply_canonical, question_constraints
from pageanchor.ids import new_trace_id, region_id
from pageanchor.models import Citation, GroundedAnswer, ScoredRegion, Trace, VerifyResult


def _region(doc_id: str, page: int, text: str, index: int = 0) -> ScoredRegion:
    return ScoredRegion(
        doc_id=doc_id,
        page=page,
        region_id=region_id(doc_id, page, index),
        type="text",
        bbox=(0.1, 0.1, 0.8, 0.4),
        text=text,
        score=1.0,
    )


def _answer(
    question: str,
    answer: str,
    cited: ScoredRegion,
    quote: str,
) -> GroundedAnswer:
    return GroundedAnswer(
        question=question,
        answer=answer,
        abstain=False,
        citations=[
            Citation(
                doc_id=cited.doc_id,
                page=cited.page,
                region_id=cited.region_id,
                bbox=cited.bbox,
                quote=quote,
                verified=True,
                quote_in_region=True,
                answer_in_quote=True,
            )
        ],
        trace=Trace(trace_id=new_trace_id(), retrieval_mode="hybrid"),
    )


def test_apply_canonical_moves_ndcg_restatement_to_table_page():
    cited = _region("arxiv-2407-colpali", 21, "Later restatement of nDCG@5.")
    table = _region(
        "arxiv-2407-colpali",
        7,
        "Table 2. Results are presented using nDCG@5 metrics",
    )
    question = (
        "What metric does Table 2 of the ColPali paper use to report ViDoRe results?"
    )
    result = apply_canonical(
        _answer(question, "nDCG@5", cited, "nDCG@5"),
        [cited, table],
    )
    assert result.abstain is False
    assert result.answer == "nDCG@5"
    assert result.citations[0].page == 7
    assert result.citations[0].region_id == table.region_id
    assert result.citations[0].bbox == table.bbox
    assert result.citations[0].quote == "nDCG@5"
    assert result.citations[0].verified is True


def test_apply_canonical_rebuilds_trace_verify_after_cite_repair():
    cited = _region("arxiv-2407-colpali", 21, "Later restatement of nDCG@5.")
    table = _region(
        "arxiv-2407-colpali",
        7,
        "Table 2. Results are presented using nDCG@5 metrics",
    )
    question = (
        "What metric does Table 2 of the ColPali paper use to report ViDoRe results?"
    )
    stale = VerifyResult(
        ok=True,
        quote="nDCG@5",
        matched_text="nDCG@5",
        doc_id=cited.doc_id,
        page=cited.page,
        region_id=cited.region_id,
        quote_in_region=True,
        answer_in_quote=True,
    )
    answer = _answer(question, "nDCG@5", cited, "nDCG@5")
    answer = answer.model_copy(
        update={"trace": answer.trace.model_copy(update={"verify": [stale]})}
    )
    result = apply_canonical(answer, [cited, table])
    assert result.citations[0].page == 7
    assert [row.page for row in result.trace.verify] == [7]
    assert result.trace.verify[0].region_id == table.region_id
    assert result.trace.verify[0].ok is True
    assert result.trace.verify[0].quote == "nDCG@5"
    assert result.trace.verify[0].matched_text == "nDCG@5"
    assert result.trace.verify[0].quote_in_region is True
    assert result.trace.verify[0].answer_in_quote is True


def test_apply_canonical_abstains_wrong_year_keeps_citations():
    cited = _region(
        "bls-cpi-20250115",
        1,
        "The CPI-U increased 0.4 percent on a seasonally adjusted basis in December 2024.",
    )
    question = (
        "What was the seasonally adjusted CPI-U rise in December 2023 in this corpus?"
    )
    quote = "increased 0.4 percent on a seasonally"
    result = apply_canonical(
        _answer(question, "0.4 percent", cited, quote),
        [cited],
    )
    assert result.abstain is True
    assert result.abstain_reason == "unanswerable"
    assert result.answer is None
    assert result.citations
    assert result.citations[0].page == cited.page
    assert result.citations[0].quote == quote


def test_apply_canonical_abstains_when_question_names_wrong_doc():
    cited = _region(
        "arxiv-2407-colpali",
        3,
        "ColPali is built from the PaliGemma-3B model",
    )
    question = (
        "How many parameters does PaliGemma-3B have according to the Adam paper?"
    )
    result = apply_canonical(
        _answer(question, "PaliGemma-3B", cited, "PaliGemma-3B model"),
        [cited],
    )
    assert result.abstain is True
    assert result.abstain_reason == "unanswerable"
    assert result.citations
    assert result.citations[0].doc_id == "arxiv-2407-colpali"


def test_apply_canonical_keeps_cpi_answer_when_year_matches():
    cited = _region(
        "bls-cpi-20250115",
        1,
        "The CPI-U increased 0.4 percent on a seasonally adjusted basis in December 2024.",
    )
    question = (
        "By how much did the CPI-U rise in December 2024 on a seasonally adjusted basis?"
    )
    result = apply_canonical(
        _answer(question, "0.4 percent", cited, "increased 0.4 percent on a seasonally"),
        [cited],
    )
    assert result.abstain is False
    assert result.answer == "0.4 percent"
    assert result.citations[0].page == 1
    assert result.citations[0].verified is True
    assert question_constraints("What is the token?") is None
