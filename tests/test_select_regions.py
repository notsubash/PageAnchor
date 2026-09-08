import json

from pageanchor.ground.regions import select_regions
from pageanchor.models import Region


def test_select_regions_ranks_by_lexical_overlap(tmp_path, monkeypatch):
    monkeypatch.setenv("PAGEANCHOR_CORPUS_ROOT", str(tmp_path))
    regions = [
        Region(
            doc_id="d",
            page=1,
            region_id="d:p1:r0",
            type="text",
            bbox=(0.0, 0.0, 1.0, 0.2),
            text="unrelated weather notes",
        ),
        Region(
            doc_id="d",
            page=1,
            region_id="d:p1:r1",
            type="text",
            bbox=(0.0, 0.2, 1.0, 0.4),
            text="ViDoRe visual document retrieval benchmark",
        ),
        Region(
            doc_id="d",
            page=1,
            region_id="d:p1:r2",
            type="text",
            bbox=(0.0, 0.4, 1.0, 0.6),
            text="benchmark retrieval ViDoRe on slides",
        ),
    ]
    out = tmp_path / "regions"
    out.mkdir()
    (out / "d.json").write_text(
        json.dumps([region.model_dump() for region in regions]), encoding="utf-8"
    )
    ranked = select_regions("ViDoRe benchmark", "d", 1, max_regions=2)
    assert [region.region_id for region in ranked] == ["d:p1:r1", "d:p1:r2"]
    assert ranked[0].score >= ranked[1].score
