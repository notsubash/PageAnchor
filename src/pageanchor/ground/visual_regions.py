from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path

import numpy as np

from pageanchor.models import BBox, ScoredRegion
from pageanchor.retrieve.visual import maxsim

EmbedQueryFn = Callable[[str], list[list[float]]]
EmbedCropsFn = Callable[[Sequence[ScoredRegion]], list[list[list[float]]]]
OpenPageFn = Callable[[str, int], Path]


def score_region_crops(
    question: str,
    regions: list[ScoredRegion],
    *,
    embed_query: EmbedQueryFn | None = None,
    embed_crops: EmbedCropsFn | None = None,
    open_page: OpenPageFn | None = None,
    corpus_root: Path | None = None,
) -> list[ScoredRegion]:
    if not regions:
        return []
    query_fn = embed_query
    crops_fn = embed_crops
    if query_fn is None:
        from pageanchor.retrieve.visual import encode_query

        query_fn = encode_query
    if crops_fn is None:

        def crops_fn(regs: Sequence[ScoredRegion]) -> list[list[list[float]]]:
            return _default_embed_crops(
                regs, open_page=open_page, corpus_root=corpus_root
            )
    query_tokens = np.asarray(query_fn(question), dtype=np.float32)
    scored: list[ScoredRegion] = []
    for region, tokens in zip(regions, crops_fn(regions), strict=True):
        score = maxsim(query_tokens, np.asarray(tokens, dtype=np.float32))
        scored.append(region.model_copy(update={"score": float(score)}))
    scored.sort(key=lambda region: (-region.score, region.region_id))
    return scored


def blend_scores(
    dense: list[ScoredRegion], visual: list[ScoredRegion]
) -> list[ScoredRegion]:
    visual_by_id = {region.region_id: region.score for region in visual}
    dense_n = _minmax([region.score for region in dense])
    visual_n = _minmax(
        [visual_by_id.get(region.region_id, 0.0) for region in dense]
    )
    blended = [
        region.model_copy(update={"score": 0.5 * dense_score + 0.5 * visual_score})
        for region, dense_score, visual_score in zip(
            dense, dense_n, visual_n, strict=True
        )
    ]
    blended.sort(key=lambda region: (-region.score, region.region_id))
    return blended


def _minmax(values: list[float]) -> list[float]:
    # ponytail: per-list min-max so ColQwen2 MaxSim (sum over tokens) cannot drown Qwen3 dots.
    if not values:
        return []
    lo = min(values)
    span = max(values) - lo
    if span < 1e-12:
        return [0.5 for _ in values]
    return [(value - lo) / span for value in values]


def _default_embed_crops(
    regions: Sequence[ScoredRegion],
    *,
    open_page: OpenPageFn | None,
    corpus_root: Path | None,
) -> list[list[list[float]]]:
    # ponytail: temp PNGs so we can reuse encode_pages. Upgrade: encode PIL crops in memory.
    from tempfile import TemporaryDirectory

    from pageanchor.config import load_settings
    from pageanchor.corpus import page_png_path
    from pageanchor.retrieve.visual import encode_pages

    root = Path(corpus_root or load_settings().corpus_root)
    with TemporaryDirectory() as tmp:
        paths: list[Path] = []
        for index, region in enumerate(regions):
            page_path = (
                Path(open_page(region.doc_id, region.page))
                if open_page is not None
                else page_png_path(root, region.doc_id, region.page)
            )
            dest = Path(tmp) / f"{index}.png"
            _write_crop(page_path, region.bbox, dest)
            paths.append(dest)
        return encode_pages(paths)


def _write_crop(page_path: Path, bbox: BBox, dest: Path) -> None:
    from PIL import Image

    with Image.open(page_path) as image:
        rgb = image.convert("RGB")
        width, height = rgb.size
        x0, y0, x1, y1 = bbox
        left = int(x0 * width)
        top = int(y0 * height)
        right = min(max(int(x1 * width), left + 1), width)
        bottom = min(max(int(y1 * height), top + 1), height)
        rgb.crop((left, top, right, bottom)).save(dest)
