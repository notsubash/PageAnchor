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
    note = ""
    if gold:
        note += _type_note(results, gold)
        note += _wrong_cite_note(results, gold)
        note += _verify_policy_note(results)
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


def _wrong_cite_note(results: dict, gold: list[dict]) -> str:
    mode = next((name for name in ("text", "hybrid", "visual") if name in results), None)
    if mode is None:
        return ""
    rows: list[tuple[str, str, str, str, str]] = []
    for row, answer in zip(gold, results[mode]["answers"], strict=True):
        if not row["answerable"]:
            continue
        payload = GroundedAnswer.model_validate(answer) if isinstance(answer, dict) else answer
        if not payload.citations:
            continue
        gold_pages = set(row["gold_pages"])
        gold_doc = row["gold_doc_id"]
        if any(
            citation.doc_id == gold_doc and citation.page in gold_pages
            for citation in payload.citations
        ):
            continue
        cited = ", ".join(
            dict.fromkeys(f"{c.doc_id} p.{c.page}" for c in payload.citations)
        )
        gold_s = f"{gold_doc} p.{','.join(str(page) for page in row['gold_pages'])}"
        rows.append(
            (row["id"], str(row.get("type") or ""), cited, gold_s, (payload.answer or "")[:80])
        )
    if not rows:
        return ""
    lines = [
        "",
        "Answerable questions whose citations missed the gold page "
        f"(mode `{mode}`):",
        "",
        "| id | type | cited | gold |",
        "| --- | --- | --- | --- |",
    ]
    for qid, qtype, cited, gold_s, _answer in rows:
        lines.append(f"| {qid} | {qtype} | {cited} | {gold_s} |")
    qid, qtype, cited, gold_s, answer = next(
        (row for row in rows if row[1] == "table"), rows[0]
    )
    lines.extend(
        [
            "",
            f"Example: `{qid}` ({qtype}) answered {answer!r} citing {cited}; gold is {gold_s}.",
            "Verify only checks that the quote is a normalized substring of the cited "
            "region. It does not check that the quote entails the answer.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def _verify_policy_note(results: dict) -> str:
    loose = results.get("hybrid") or results.get("text")
    strict = results.get("hybrid+verify") or results.get("text+verify")
    if not loose or not strict:
        return ""
    loose_v = loose["metrics"]["verify_pass_rate"]
    strict_v = strict["metrics"]["verify_pass_rate"]
    if strict_v + 1e-9 < loose_v:
        return (
            "Strict verify pass rate is below the matching retrieve-only run. "
            "That usually means the abstain path is dropping verified citations "
            "or keeping unverified ones in the answer field.\n"
        )
    return ""


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
