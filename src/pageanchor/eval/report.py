from __future__ import annotations


def render_report(results: dict) -> str:
    labels = {"text": "A text", "text+verify": "D-lite text+verify"}
    lines = [
        "# Text retrieve eval",
        "",
        "A keeps the generator answer even when a citation quote fails verify. "
        "D-lite abstains on any failed quote. Verify pass rate is computed on citations "
        "attached to kept (non-abstain) answers.",
        "",
        "| system | recall@5 | citation page hit | verify pass | abstain P | abstain R | p50 ms |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for mode, payload in results.items():
        metrics = payload["metrics"]
        name = labels.get(mode, mode)
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
    return "\n".join(lines) + "\n"
