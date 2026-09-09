from __future__ import annotations

from pageanchor.models import GroundedAnswer

_LABELS = {
    "text": "A text",
    "visual": "B visual",
    "hybrid": "C hybrid",
    "hybrid+verify": "D hybrid+verify",
    "text+verify": "D-lite text+verify",
}


def render_report(results: dict, gold: list[dict] | None = None) -> str:
    lines = [
        "# Retrieval ablation",
        "",
        "A/B/C keep the generator answer even when a citation quote fails verify. "
        "D / D-lite abstain on any failed quote. Verify pass rate is computed on "
        "citations attached to kept (non-abstain) answers.",
        "",
        "| system | recall@5 | citation page hit | verify pass | abstain P | abstain R | p50 ms |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for mode, payload in results.items():
        metrics = payload["metrics"]
        name = _LABELS.get(mode, mode)
        lines.append(
            "| {name} | {recall:.3f} | {cite:.3f} | {verify:.3f} | "
            "{prec:.3f} | {rec:.3f} | {p50:.0f} |".format(
                name=name,
                recall=metrics["recall_at_5"],
                cite=metrics["citation_page_hit"],
                verify=metrics["verify_pass_rate"],
                prec=metrics["abstain_precision"],
                rec=metrics["abstain_recall"],
                p50=metrics["latency_p50_ms"],
            )
        )
    note = _type_note(results, gold) if gold else ""
    return "\n".join(lines) + "\n" + note


def _type_note(results: dict, gold: list[dict]) -> str:
    if "text" not in results or "visual" not in results:
        return ""
    lines = [
        "",
        "Recall@5 on answerable gold by type (text vs visual):",
        "",
        "| type | n | text | visual |",
        "| --- | ---: | ---: | ---: |",
    ]
    for qtype in ("table", "figure", "layout", "plain_text"):
        text_r, n = _recall_type(gold, results["text"]["answers"], qtype)
        visual_r, _ = _recall_type(gold, results["visual"]["answers"], qtype)
        if n == 0:
            continue
        lines.append(f"| {qtype} | {n} | {text_r:.3f} | {visual_r:.3f} |")
    lines.append("")
    return "\n".join(lines) + "\n"


def _recall_type(gold: list[dict], answers: list, qtype: str) -> tuple[float, int]:
    hits = 0
    n = 0
    for row, answer in zip(gold, answers, strict=True):
        if not row["answerable"] or row.get("type") != qtype:
            continue
        n += 1
        payload = GroundedAnswer.model_validate(answer) if isinstance(answer, dict) else answer
        gold_pages = set(row["gold_pages"])
        gold_doc = row["gold_doc_id"]
        if any(hit.doc_id == gold_doc and hit.page in gold_pages for hit in payload.trace.hits[:5]):
            hits += 1
    return (hits / n if n else 0.0, n)
