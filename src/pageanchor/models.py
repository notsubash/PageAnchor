from typing import Literal

from pydantic import BaseModel, Field

BBox = tuple[float, float, float, float]
RegionType = Literal["text", "table", "figure", "title", "other"]
RetrievalMode = Literal["text", "visual", "hybrid"]
AbstainReason = Literal[
    "low_retrieval_score",
    "no_hits",
    "verify_failed",
    "unsupported",
    "unanswerable",
    "generator_invalid",
]


class Region(BaseModel):
    doc_id: str
    page: int = Field(ge=1)
    region_id: str
    type: RegionType
    bbox: BBox
    text: str


class PageHit(BaseModel):
    doc_id: str
    page: int = Field(ge=1)
    score: float
    source: RetrievalMode


class ScoredRegion(Region):
    score: float


class Citation(BaseModel):
    doc_id: str
    page: int = Field(ge=1)
    region_id: str | None = None
    bbox: BBox
    quote: str
    verified: bool = False
    quote_in_region: bool = False
    answer_in_quote: bool = False


class VerifyResult(BaseModel):
    ok: bool
    quote: str
    matched_text: str | None = None
    doc_id: str
    page: int = Field(ge=1)
    region_id: str
    quote_in_region: bool = False
    answer_in_quote: bool = False


class Trace(BaseModel):
    trace_id: str
    retrieval_mode: RetrievalMode
    hits: list[PageHit] = Field(default_factory=list)
    regions: list[ScoredRegion] = Field(default_factory=list)
    verify: list[VerifyResult] = Field(default_factory=list)
    timings_ms: dict[str, float] = Field(default_factory=dict)


class GroundedAnswer(BaseModel):
    question: str
    answer: str | None
    abstain: bool
    abstain_reason: AbstainReason | None = None
    citations: list[Citation]
    trace: Trace
