from __future__ import annotations

import json
import time
from pathlib import Path

from pageanchor.eval.metrics import score_run
from pageanchor.eval.report import render_report
from pageanchor.ground.answer import apply_strict, grounded_answer


def run_eval(gold_path: str, modes: list[str], out_dir: str) -> dict:
    gold = [
        json.loads(line)
        for line in Path(gold_path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    raw = []
    latencies: list[float] = []
    for row in gold:
        started = time.perf_counter()
        print(f"eval {row['id']}", flush=True)
        raw.append(grounded_answer(row["question"], "text", strict=False))
        latencies.append((time.perf_counter() - started) * 1000)

    results: dict = {}
    for mode in modes:
        mode = mode.strip()
        if mode == "text":
            answers = raw
        elif mode in {"text+verify", "text_verify"}:
            answers = [apply_strict(answer) for answer in raw]
        else:
            raise ValueError(f"unknown eval mode {mode!r}")
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
    (dest / "report.md").write_text(render_report(results), encoding="utf-8")
    return results
