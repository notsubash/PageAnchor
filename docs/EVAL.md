# Eval

Gold is 30 questions in `corpus/eval/gold_questions.jsonl`, frozen `2026-09-08` in `corpus/manifest.json`. Distribution: 6 `plain_text`, 6 `table`, 6 `figure`, 6 `layout`, 6 `unanswerable`. Authoring notes: [corpus/eval/README.md](../corpus/eval/README.md).

Reproduce:

```bash
uv run pageanchor ingest --all
uv run pageanchor ingest --visual --all   # needed for visual / hybrid
uv run pageanchor eval --gold corpus/eval/gold_questions.jsonl \
  --modes text,visual,hybrid,hybrid+verify \
  --out eval/results/YYYY-MM-DD
```

`--modes text,text+verify` is the text-only pair (A vs D-lite) when ColQwen2 is not installed.

The harness calls `grounded_answer(..., strict=False)` once per retrieve mode, then `apply_strict` for `*+verify`. Visual and `hybrid+verify` therefore do not double-pay the generator.

Hashes in the manifest must match the PDFs on disk. Ingest refuses a mismatch. Do not edit gold quotes after `frozen_at` except to fix page numbers; new questions are a freeze bump.

## Metrics

| Metric | Slice | Definition |
| --- | --- | --- |
| Recall@5 | answerable | Gold `(doc_id, page)` appears in `trace.hits[:5]`. |
| Citation page hit | answerable rows that produced citations | Some citation has gold `doc_id` and a gold page. |
| Verify pass rate | citations on **kept** (non-abstain) answers | Fraction with `verified=true`. |
| Abstain precision | all 30 | Among abstains, share that are gold-unanswerable. |
| Abstain recall | 6 unanswerable | Share of unanswerable rows that abstained. |
| Latency p50 | all rows | Median `grounded_answer` wall time, ms. |

Systems:

| Label | `--modes` | Policy |
| --- | --- | --- |
| A | `text` | Keep the generator answer even if a quote fails verify. |
| B | `visual` | Same, visual retrieve. |
| C | `hybrid` | Same, RRF. |
| D | `hybrid+verify` | Any unverified citation → abstain, `answer=null`. |
| D-lite | `text+verify` | Strict verify on text retrieve. |

Headline system is D. If D's verify pass rate is below C on the same run, the strict path is miswired; do not treat that table as a result.

nDCG, table exact match, and cost are not scored.

## Committed run

`eval/results/2026-09-08/` is Windows CPU, text retrieve only, generator `deepseek-v4-flash`. Visual extra was not loaded. A and D-lite match because the generator did not keep unverified quotes.

| system | recall@5 | citation page hit | verify pass | abstain P | abstain R | p50 ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A text | 0.708 | 0.556 | 1.000 | 0.500 | 1.000 | 1825 |
| D-lite text+verify | 0.708 | 0.556 | 1.000 | 0.500 | 1.000 | 1825 |

Recall@5 is 17/24. Citation page hit is among answerable rows that produced citations. Abstain recall is 1.0 on the six unanswerable items. Precision is 0.5 because six answerable questions were also refused (`unanswerable` or `generator_invalid`).

To add B/C/D, re-run the four-mode command above on a machine with `--extra visual` and commit a new dated folder. Do not overwrite `2026-09-08` if the generator or index changed.

## Failure case

**q011** (table): "How many CoLA training examples does the GLUE table list?" Gold is `arxiv-1804-glue` page 2, quote `CoLA 8.5k`. Text retrieve@5 never ranked page 2. The generator answered `8.5k` and cited page 8 headings (`Single-Task Training`, `Multi-Task Training`). Both quotes verified: they are substrings of those regions. The number is not on the cited page.

That is the product boundary. Verify does not ask whether the quote supports the answer. Citation page hit is the metric that catches it.

Related misses in the same run (full table in `eval/results/2026-09-08/report.md`):

- **q012** (table): Table 2 lives on ColPali page 7. Retrieve ranked page 4 (Table 1) and cited page 21, which restates `nDCG@5`. The answer is right; the box would be wrong.
- **q016** (figure / slides): first-slide title is page 1, `Expanding Our View`. Text retrieve never ranked page 1 and cited the FAQ on page 29. Sparse slide text is why visual retrieve exists; this run does not yet prove it.

## Score cutoff

`RETRIEVAL_MIN_SCORE` is not wired. `low_retrieval_score` is unused.

On this gold, unanswerable rows still retrieve (top-hit scores about 0.43–0.59). Answerable hits sit in the same band (about 0.50–0.73). A cutoff of `0.35` would never fire. A threshold high enough to drop unanswerable hits would also drop answerable ones. We abstain on `no_hits`, `verify_failed`, `generator_invalid`, and model `unanswerable` only.

If you tune later, record the value and the six question ids in this file. Do not pick the threshold on the full 30.

## CI

`uv run pytest tests/` is GPU-free. It uses a one-page fixture PDF and mocked retrieve/generate. It does not download the corpus or ColQwen2. GPU tests are `pytest.mark.gpu` and are skipped in CI.
