from __future__ import annotations

import json
import time
from pathlib import Path

from pageanchor.eval.metrics import score_run
from pageanchor.eval.report import render_report
from pageanchor.ground.answer import apply_strict, grounded_answer
from pageanchor.models import GroundedAnswer

_RETRIEVE_MODES = {"text", "visual", "hybrid"}


def run_eval(gold_path: str, modes: list[str], out_dir: str) -> dict:
    gold = [
        json.loads(line)
        for line in Path(gold_path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    parsed = [_parse_mode(mode) for mode in modes]
    retrieve_needed: list[str] = []
    for retrieve, _verify in parsed:
        if retrieve not in retrieve_needed:
            retrieve_needed.append(retrieve)

    raw: dict[str, tuple[list[GroundedAnswer], list[float]]] = {}
    for retrieve in retrieve_needed:
        answers: list[GroundedAnswer] = []
        latencies: list[float] = []
        for row in gold:
            started = time.perf_counter()
            print(f"eval {retrieve} {row['id']}", flush=True)
            answers.append(grounded_answer(row["question"], retrieve, strict=False))
            latencies.append((time.perf_counter() - started) * 1000)
        raw[retrieve] = (answers, latencies)

    results: dict = {}
    for mode, (retrieve, verify) in zip(modes, parsed, strict=True):
        mode = mode.strip()
        answers, latencies = raw[retrieve]
        if verify:
            answers = [apply_strict(answer) for answer in answers]
        results[mode] = {
            "metrics": score_run(gold, answers, latencies),
            "answers": [answer.model_dump() for answer in answers],
        }

    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "metrics.json").write_text(
        json.dumps({mode: payload["metrics"] for mode, payload in results.items()}, indent=2),
        encoding="utf-8",
    )
    (dest / "answers.json").write_text(
        json.dumps({mode: payload["answers"] for mode, payload in results.items()}, indent=2),
        encoding="utf-8",
    )
    (dest / "report.md").write_text(render_report(results, gold), encoding="utf-8")
    return results


def _parse_mode(mode: str) -> tuple[str, bool]:
    mode = mode.strip()
    verify = False
    retrieve = mode
    if mode.endswith("+verify"):
        retrieve = mode[: -len("+verify")]
        verify = True
    elif mode.endswith("_verify"):
        retrieve = mode[: -len("_verify")]
        verify = True
    if retrieve not in _RETRIEVE_MODES:
        raise ValueError(f"unknown eval mode {mode!r}")
    return retrieve, verify
