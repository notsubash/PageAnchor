import uuid

import pytest
from pydantic import ValidationError

from pageanchor.ids import new_trace_id, region_id
from pageanchor.models import Citation, GroundedAnswer, Region, Trace


def test_region_id_format():
    assert region_id("arxiv-2407-colpali", 1, 0) == "arxiv-2407-colpali:p1:r0"


def test_trace_id_is_uuid4():
    value = new_trace_id()
    parsed = uuid.UUID(value)
    assert parsed.version == 4
    assert str(parsed) == value


def test_region_rejects_page_zero():
    with pytest.raises(ValidationError):
        Region(
            doc_id="d",
            page=0,
            region_id="d:p0:r0",
            type="text",
            bbox=(0.0, 0.0, 1.0, 1.0),
            text="x",
        )


def test_grounded_answer_roundtrip():
    answer = GroundedAnswer(
        question="What is ViDoRe?",
        answer=None,
        abstain=True,
        abstain_reason="no_hits",
        citations=[],
        trace=Trace(trace_id=new_trace_id(), retrieval_mode="text"),
    )
    loaded = GroundedAnswer.model_validate(answer.model_dump())
    assert loaded.abstain is True
    assert loaded.abstain_reason == "no_hits"
    assert loaded.citations == []


def test_citation_defaults():
    cite = Citation(
        doc_id="d",
        page=1,
        bbox=(0.1, 0.1, 0.5, 0.5),
        quote="hello",
    )
    assert cite.region_id is None
    assert cite.verified is False
