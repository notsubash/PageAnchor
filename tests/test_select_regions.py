import json

from pageanchor.ground.regions import select_evidence, select_regions
from pageanchor.models import PageHit, Region


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


def test_select_regions_ignores_question_stopwords(tmp_path, monkeypatch):
    monkeypatch.setenv("PAGEANCHOR_CORPUS_ROOT", str(tmp_path))
    regions = [
        Region(
            doc_id="d",
            page=1,
            region_id="d:p1:r0",
            type="text",
            bbox=(0.0, 0.0, 1.0, 0.2),
            text="Query: What is the key approach used in the PDP architecture?",
        ),
        Region(
            doc_id="d",
            page=1,
            region_id="d:p1:r1",
            type="text",
            bbox=(0.0, 0.2, 1.0, 0.4),
            text="The PaliGemma-3B model projects SigLIP patch embeddings",
        ),
    ]
    out = tmp_path / "regions"
    out.mkdir()
    (out / "d.json").write_text(
        json.dumps([region.model_dump() for region in regions]), encoding="utf-8"
    )
    ranked = select_regions(
        "what embedding model was used in colpali", "d", 1, max_regions=2
    )
    assert ranked[0].region_id == "d:p1:r1"


def test_select_evidence_caps_regions_per_page(tmp_path, monkeypatch):
    monkeypatch.setenv("PAGEANCHOR_CORPUS_ROOT", str(tmp_path))
    rows = []
    for page in (1, 2):
        for index in range(3):
            rows.append(
                Region(
                    doc_id="d",
                    page=page,
                    region_id=f"d:p{page}:r{index}",
                    type="text",
                    bbox=(0.0, 0.1 * index, 1.0, 0.1 * index + 0.1),
                    text="PaliGemma embedding model " * (3 - index),
                ).model_dump()
            )
    out = tmp_path / "regions"
    out.mkdir()
    (out / "d.json").write_text(json.dumps(rows), encoding="utf-8")

    def fake_embed(texts: list[str]) -> list[list[float]]:
        return [[float(len(text)), 0.0] for text in texts]

    picked = select_evidence(
        "PaliGemma",
        [
            PageHit(doc_id="d", page=1, score=1.0, source="text"),
            PageHit(doc_id="d", page=2, score=0.9, source="text"),
        ],
        max_regions=5,
        per_page=2,
        embed_query=fake_embed,
        embed_passages=fake_embed,
        corpus_root=tmp_path,
    )
    counts: dict[int, int] = {}
    for region in picked:
        counts[region.page] = counts.get(region.page, 0) + 1
    assert len(picked) == 4
    assert counts[1] == 2
    assert counts[2] == 2


def test_select_evidence_dense_rerank_beats_jaccard_trap(tmp_path, monkeypatch):
    monkeypatch.setenv("PAGEANCHOR_CORPUS_ROOT", str(tmp_path))
    rows = [
        Region(
            doc_id="d",
            page=1,
            region_id="d:p1:r0",
            type="text",
            bbox=(0.0, 0.0, 1.0, 0.2),
            text="Model Embedding size (KB) BGE-M3 ColPali",
        ).model_dump(),
        Region(
            doc_id="d",
            page=1,
            region_id="d:p1:r1",
            type="text",
            bbox=(0.0, 0.2, 1.0, 0.4),
            text="The PaliGemma-3B model projects SigLIP-So400m/14 patch embeddings into Gemma-2B",
        ).model_dump(),
    ]
    out = tmp_path / "regions"
    out.mkdir()
    (out / "d.json").write_text(json.dumps(rows), encoding="utf-8")

    def embed_query(texts: list[str]) -> list[list[float]]:
        return [[0.0, 1.0] for _ in texts]

    def embed_passages(texts: list[str]) -> list[list[float]]:
        out_vec = []
        for text in texts:
            if "PaliGemma-3B" in text:
                out_vec.append([0.0, 1.0])
            else:
                out_vec.append([1.0, 0.0])
        return out_vec

    picked = select_evidence(
        "what embedding model was used in colpali",
        [PageHit(doc_id="d", page=1, score=1.0, source="hybrid")],
        max_regions=1,
        embed_query=embed_query,
        embed_passages=embed_passages,
        corpus_root=tmp_path,
    )
    assert picked[0].region_id == "d:p1:r1"


def test_select_evidence_longest_table_beats_jaccard_heading(tmp_path, monkeypatch):
    monkeypatch.setenv("PAGEANCHOR_CORPUS_ROOT", str(tmp_path))
    table_id = "d:p1:r_table"
    table_text = (
        "MNLI 392k matched mismatched QQP 363k QNLI 108k SST-2 67k "
        "CoLA 8.5k STS-B 7k MRPC 3.7k RTE 2.5k WNLI 634 "
        "Single-Task Training Multi-Task Training "
        "accuracy F1 Matthews correlation benchmark scores "
    ) * 6
    headings = [
        "CoLA training examples",
        "CoLA training examples count",
        "many CoLA training examples here",
        "CoLA training set examples",
        "training examples CoLA many",
    ]
    rows = [
        Region(
            doc_id="d",
            page=1,
            region_id=f"d:p1:r{index}",
            type="text",
            bbox=(0.0, 0.05 * index, 1.0, 0.05 * index + 0.05),
            text=heading,
        ).model_dump()
        for index, heading in enumerate(headings)
    ]
    rows.append(
        Region(
            doc_id="d",
            page=1,
            region_id=table_id,
            type="text",
            bbox=(0.0, 0.4, 1.0, 0.9),
            text=table_text,
        ).model_dump()
    )
    out = tmp_path / "regions"
    out.mkdir()
    (out / "d.json").write_text(json.dumps(rows), encoding="utf-8")

    query = "How many CoLA training examples?"
    jaccard_only = select_regions(query, "d", 1, max_regions=3, corpus_root=tmp_path)
    assert table_id not in {region.region_id for region in jaccard_only}

    def embed_query(texts: list[str]) -> list[list[float]]:
        return [[0.0, 1.0] for _ in texts]

    def embed_passages(texts: list[str]) -> list[list[float]]:
        return [[0.0, 1.0] if "CoLA 8.5k" in text else [1.0, 0.0] for text in texts]

    picked = select_evidence(
        query,
        [PageHit(doc_id="d", page=1, score=1.0, source="hybrid")],
        max_regions=5,
        pool_per_page=3,
        embed_query=embed_query,
        embed_passages=embed_passages,
        corpus_root=tmp_path,
    )
    assert table_id in {region.region_id for region in picked}
    assert all(region.type == "text" for region in picked)


def test_select_evidence_two_pass_covers_each_hit_page(tmp_path, monkeypatch):
    monkeypatch.setenv("PAGEANCHOR_CORPUS_ROOT", str(tmp_path))
    rows = []
    for page, tag in ((1, "HIGH"), (2, "MID"), (3, "LOW")):
        for index in range(3):
            rows.append(
                Region(
                    doc_id="d",
                    page=page,
                    region_id=f"d:p{page}:r{index}",
                    type="text",
                    bbox=(0.0, 0.1 * index, 1.0, 0.1 * index + 0.1),
                    text=f"GLUE {tag}{index} CoLA evidence",
                ).model_dump()
            )
    out = tmp_path / "regions"
    out.mkdir()
    (out / "d.json").write_text(json.dumps(rows), encoding="utf-8")

    def embed_query(texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] for _ in texts]

    def embed_passages(texts: list[str]) -> list[list[float]]:
        vecs = []
        for text in texts:
            if "HIGH" in text:
                vecs.append([10.0, 0.0])
            elif "MID" in text:
                vecs.append([5.0, 0.0])
            else:
                vecs.append([1.0, 0.0])
        return vecs

    picked = select_evidence(
        "GLUE CoLA evidence",
        [
            PageHit(doc_id="d", page=1, score=1.0, source="hybrid"),
            PageHit(doc_id="d", page=2, score=0.9, source="hybrid"),
            PageHit(doc_id="d", page=3, score=0.8, source="hybrid"),
        ],
        max_regions=5,
        per_page=2,
        embed_query=embed_query,
        embed_passages=embed_passages,
        corpus_root=tmp_path,
    )
    assert {region.page for region in picked} == {1, 2, 3}
    assert {region.page for region in picked[:3]} == {1, 2, 3}
