from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from pageanchor.config import torch_env
from pageanchor.models import PageHit

POOL_K = 20
_MODES = ("text", "visual", "hybrid", "bm25")
SearchFn = Callable[..., list[PageHit]]


def gold_rank(hits: list[PageHit], gold_doc_id: str, gold_pages: list[int]) -> int | None:
    pages = set(gold_pages)
    for rank, hit in enumerate(hits, start=1):
        if hit.doc_id == gold_doc_id and hit.page in pages:
            return rank
    return None


def recall_at(ranks: list[int | None], k: int) -> float:
    if not ranks:
        return 0.0
    return sum(1 for rank in ranks if rank is not None and rank <= k) / len(ranks)


def rrf_fuse_lists(
    hit_lists: list[list[PageHit]],
    k: int = 5,
    k_rrf: int = 60,
) -> list[PageHit]:
    scores: dict[tuple[str, int], float] = {}

    def accumulate(hits: list[PageHit]) -> None:
        seen: set[tuple[str, int]] = set()
        for rank, hit in enumerate(hits, start=1):
            key = (hit.doc_id, hit.page)
            if key in seen:
                continue
            seen.add(key)
            scores[key] = scores.get(key, 0.0) + 1.0 / (k_rrf + rank)

    for hits in hit_lists:
        accumulate(hits)

    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0][0], item[0][1]))
    return [
        PageHit(doc_id=doc_id, page=page, score=score, source="hybrid")
        for (doc_id, page), score in ranked[:k]
    ]


def run_retrieve_eval(
    gold_path: str,
    out_dir: str,
    *,
    k: int = POOL_K,
    searches: dict[str, SearchFn] | None = None,
) -> dict:
    gold = [
        json.loads(line)
        for line in Path(gold_path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    fns = searches or _default_searches()
    rows: list[dict] = []
    for row in gold:
        if not row.get("answerable"):
            continue
        print(f"eval retrieve {row['id']}", flush=True)
        lists: dict[str, list[PageHit]] = {
            mode: fns[mode](row["question"], k) for mode in _MODES
        }
        lists["rrf3"] = rrf_fuse_lists(
            [lists["text"], lists["visual"], lists["bm25"]], k=k
        )
        ranks = {
            mode: gold_rank(lists[mode], row["gold_doc_id"], row["gold_pages"])
            for mode in (*_MODES, "rrf3")
        }
        rows.append(
            {
                "id": row["id"],
                "gold_doc_id": row["gold_doc_id"],
                "gold_pages": list(row["gold_pages"]),
                "ranks": ranks,
                "hits": {
                    mode: [hit.model_dump() for hit in lists[mode]] for mode in lists
                },
            }
        )

    recall = {
        mode: {
            "at_5": recall_at([row["ranks"][mode] for row in rows], 5),
            "at_10": recall_at([row["ranks"][mode] for row in rows], 10),
            "at_20": recall_at([row["ranks"][mode] for row in rows], k),
        }
        for mode in (*_MODES, "rrf3")
    }
    machine = torch_env()
    payload = {
        "k": k,
        "n_answerable": len(rows),
        "recall": recall,
        "rows": rows,
        "machine": machine,
    }
    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "ranks.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (dest / "machine.json").write_text(json.dumps(machine, indent=2), encoding="utf-8")
    (dest / "report.md").write_text(render_retrieve_report(payload), encoding="utf-8")
    return payload


def render_retrieve_report(payload: dict, *, machine: dict | None = None) -> str:
    machine = machine or payload.get("machine")
    n = payload["n_answerable"]
    lines = [
        "# Retrieve-only diagnostic",
        "",
        "No generator. Rank is the 1-based position of gold `(doc_id, page)` in the top-"
        f"{payload.get('k', POOL_K)} hits. `rrf3` is Reciprocal Rank Fusion of text + "
        "visual + BM25 lists (not wired into `search_hybrid` yet).",
        "",
        "| mode | Recall@5 | Recall@10 | Recall@20 |",
        "| --- | ---: | ---: | ---: |",
    ]
    for mode, metrics in payload["recall"].items():
        lines.append(
            f"| {mode} | {metrics['at_5']:.3f} | {metrics['at_10']:.3f} | {metrics['at_20']:.3f} |"
        )

    lines.extend(
        [
            "",
            "| id | gold | text | visual | hybrid | bm25 | rrf3 |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in payload["rows"]:
        gold = f"{row['gold_doc_id']} p.{','.join(str(p) for p in row['gold_pages'])}"
        ranks = row["ranks"]
        cells = " | ".join(_rank_cell(ranks.get(mode)) for mode in (*_MODES, "rrf3"))
        lines.append(f"| {row['id']} | {gold} | {cells} |")

    def _hits(mode: str) -> int:
        return sum(1 for row in payload["rows"] if row["ranks"].get(mode) is not None)

    lines.extend(
        [
            "",
            f"Gold page in hybrid@20: {_hits('hybrid')}/{n}",
            f"Gold page in BM25@20: {_hits('bm25')}/{n}",
            f"Gold page in 3-way RRF@20: {_hits('rrf3')}/{n}",
            "",
        ]
    )
    rrf3_n = _hits("rrf3")
    hybrid_n = _hits("hybrid")
    if n and hybrid_n / n >= 0.75:
        lines.append(
            "Gate: gold pages are usually inside current hybrid@20. Phase 1 is rerank + wider "
            "`select_evidence` pool, plus same-doc fill / query cues for the remaining @5 misses."
        )
    elif n and rrf3_n / n >= 0.75:
        lines.append(
            "Gate: gold pages are usually inside 3-way RRF@20. Phase 1 is rerank + wider "
            "`select_evidence` pool, plus same-doc fill / query cues for the remaining misses."
        )
    elif n and hybrid_n / n < 0.5:
        lines.append(
            "Gate: gold pages are missing at 20. Phase 1 must add same-doc fill and query cues, "
            "not just `k=20`."
        )
    else:
        lines.append(
            "Gate: mixed. Phase 1 should add `pool_k=20`, same-doc fill, and query cues."
        )
    if machine:
        torch_v = machine.get("torch") or "unknown"
        device = machine.get("device") or "unknown"
        lines.extend(["", f"Torch {torch_v} on {device}."])
    lines.append("")
    return "\n".join(lines) + "\n"


def _rank_cell(rank: int | None) -> str:
    return "miss" if rank is None else str(rank)


def _default_searches() -> dict[str, SearchFn]:
    from pageanchor.retrieve.hybrid import search_hybrid
    from pageanchor.retrieve.sparse import search_bm25
    from pageanchor.retrieve.text import search_text
    from pageanchor.retrieve.visual import search_visual

    return {
        "text": search_text,
        "visual": search_visual,
        "hybrid": search_hybrid,
        "bm25": search_bm25,
    }
