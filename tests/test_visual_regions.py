import json

import pytest

from pageanchor.ground.visual_regions import blend_scores, score_region_crops
from pageanchor.models import PageHit, Region, ScoredRegion


def _r(region_id: str, text: str, score: float) -> ScoredRegion:
    return ScoredRegion(
        doc_id="d",
        page=1,
        region_id=region_id,
        type="text",
        bbox=(0.0, 0.0, 0.5, 0.5),
        text=text,
        score=score,
    )


def test_score_region_crops_uses_injected_maxsim(monkeypatch):
    regions = [_r("d:p1:r0", "caption", 0.1), _r("d:p1:r1", "PaliGemma", 0.1)]

    def embed_query(query: str):
        return [[1.0, 0.0]]

    def embed_crops(regions):
        return [[[0.0, 1.0]], [[1.0, 0.0]]]

    scored = score_region_crops(
        "q",
        regions,
        embed_query=lambda q: embed_query(q),
        embed_crops=embed_crops,
    )
    assert scored[0].region_id == "d:p1:r1"


def test_blend_scores_averages_dense_and_visual():
    dense = [_r("d:p1:r0", "a", 1.0), _r("d:p1:r1", "b", 0.0)]
    visual = [_r("d:p1:r0", "a", 0.0), _r("d:p1:r1", "b", 1.0)]
    blended = blend_scores(dense, visual)
    by_id = {region.region_id: region.score for region in blended}
    assert by_id["d:p1:r0"] == pytest.approx(0.5)
    assert by_id["d:p1:r1"] == pytest.approx(0.5)


def test_blend_scores_rescales_before_average():
    dense = [_r("d:p1:r0", "a", 1.0), _r("d:p1:r1", "b", 0.0)]
    visual = [_r("d:p1:r0", "a", 1.0), _r("d:p1:r1", "b", 40.0)]
    blended = blend_scores(dense, visual)
    by_id = {region.region_id: region.score for region in blended}
    assert by_id["d:p1:r0"] == pytest.approx(0.5)
    assert by_id["d:p1:r1"] == pytest.approx(0.5)


def test_select_evidence_visual_blends_injected_scores(tmp_path, monkeypatch):
    from pageanchor.ground.regions import select_evidence

    monkeypatch.setenv("PAGEANCHOR_CORPUS_ROOT", str(tmp_path))
    rows = [
        Region(
            doc_id="d",
            page=1,
            region_id="d:p1:r0",
            type="text",
            bbox=(0.0, 0.0, 1.0, 0.2),
            text="caption line",
        ).model_dump(),
        Region(
            doc_id="d",
            page=1,
            region_id="d:p1:r1",
            type="text",
            bbox=(0.0, 0.2, 1.0, 0.4),
            text="PaliGemma-3B",
        ).model_dump(),
    ]
    out = tmp_path / "regions"
    out.mkdir()
    (out / "d.json").write_text(json.dumps(rows), encoding="utf-8")

    def embed_text(texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] for _ in texts]

    def embed_visual_query(query: str):
        return [[1.0, 0.0]]

    def embed_crops(regions):
        return [
            [[0.0, 1.0]] if "caption" in region.text else [[1.0, 0.0]]
            for region in regions
        ]

    picked = select_evidence(
        "q",
        [PageHit(doc_id="d", page=1, score=1.0, source="hybrid")],
        max_regions=1,
        visual=True,
        embed_query=embed_text,
        embed_passages=embed_text,
        embed_visual_query=embed_visual_query,
        embed_crops=embed_crops,
        corpus_root=tmp_path,
    )
    assert picked[0].region_id == "d:p1:r1"
