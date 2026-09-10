# Eval

Gold is 30 questions in `corpus/eval/gold_questions.jsonl`, frozen `2026-09-08` in `corpus/manifest.json`. Distribution: 6 `plain_text`, 6 `table`, 6 `figure`, 6 `layout`, 6 `unanswerable`. Authoring notes: [corpus/eval/README.md](../corpus/eval/README.md).

Reproduce:

```bash
uv run pageanchor ingest --all
uv run pageanchor ingest --visual --all   # needed for visual / hybrid
uv sync --extra dev --extra visual   # ColQwen2; list every extra you already use
uv run pageanchor eval --gold corpus/eval/gold_questions.jsonl \
  --modes text,visual,hybrid,hybrid+verify,text+verify \
  --out eval/results/YYYY-MM-DD
```

GPU (NVIDIA). PyPI torch is CPU; overlay CUDA 12.8 wheels (2.11.0+cu128 as of this writing). Same harness; write a separate dated folder so CPU and GPU rows are not mixed:

```bash
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
uv run --no-sync pageanchor eval --gold corpus/eval/gold_questions.jsonl \
  --modes text,visual,hybrid,hybrid+verify,text+verify \
  --out eval/results/YYYY-MM-DD-gpu
```

Each run writes `machine.json` (`torch`, `cuda`, `device`). After a CUDA overlay, use `uv run --no-sync` so the lock does not replace GPU torch with the CPU wheel. `--modes text,text+verify` is the text-only pair (A vs D-lite) when ColQwen2 is not installed.

The harness calls `grounded_answer(..., strict=False)` once per retrieve mode, then `apply_strict` for `*+verify`. Visual and `hybrid+verify` therefore do not double-pay the generator.

Hashes in the manifest must match the PDFs on disk. Ingest refuses a mismatch. Do not edit gold quotes after `frozen_at` except to fix page numbers; new questions are a freeze bump.

## Metrics

| Metric | Slice | Definition |
| --- | --- | --- |
| Recall@5 | answerable | Gold `(doc_id, page)` appears in `trace.hits[:5]`. |
| Citation page hit | answerable rows that produced citations | Some citation has gold `doc_id` and a gold page. |
| Verify pass rate | citations on **kept** (non-abstain) answers | Fraction with `verified=true` (quote-in-region and answer-in-quote). |
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

`eval/results/2026-09-10/` is the full ablation: Windows CPU, ColQwen2 on CPU (`vidore/colqwen2-v1.0`), generator `deepseek-v4-flash`. Visual index: 160 pages. Text index: 3193 chunks.

| system | recall@5 | citation page hit | verify pass | abstain P | abstain R | p50 ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A text | 0.708 | 0.917 | 0.917 | 0.333 | 1.000 | 1819 |
| B visual | 0.875 | 0.923 | 1.000 | 0.353 | 1.000 | 2104 |
| C hybrid | 0.875 | 0.923 | 1.000 | 0.353 | 1.000 | 2675 |
| D hybrid+verify | 0.875 | 0.923 | 1.000 | 0.353 | 1.000 | 2675 |
| D-lite text+verify | 0.708 | 0.917 | 1.000 | 0.316 | 1.000 | 1819 |

Recall@5 is 17/24 (text) and 21/24 (visual and hybrid). D verify pass equals C, so the strict path is not miswired. D-lite raises text verify pass from 0.917 to 1.000 by abstaining on the one unverified citation (q017). Abstain recall is 1.0 on the six unanswerable items. Precision is ~0.35 because 11 or 12 answerable questions were also refused (`unanswerable`, `verify_failed`, or `unsupported`).

Recall@5 on answerable gold by type:

| type | n | text | visual | hybrid |
| --- | ---: | ---: | ---: | ---: |
| table | 6 | 0.667 | 0.833 | 0.833 |
| figure | 6 | 0.667 | 0.833 | 0.833 |
| layout | 6 | 0.833 | 0.833 | 0.833 |
| plain_text | 6 | 0.667 | 1.000 | 1.000 |

Visual beats text on table, figure, and plain text. Layout is tied. Hybrid matches visual on every type; RRF did not recover an extra gold page on this freeze.

`eval/results/2026-09-10-gpu/` is the same gold and indexes on CUDA. `machine.json`: `torch 2.11.0+cu128`, `NVIDIA GeForce RTX 4070 Ti SUPER`. Query encoding used CUDA (ColQwen2 bf16, Qwen3-Embedding on cuda). Page MaxSim is still numpy on CPU.

| system | recall@5 | citation page hit | verify pass | abstain P | abstain R | p50 ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A text | 0.708 | 0.909 | 1.000 | 0.316 | 1.000 | 1346 |
| B visual | 0.875 | 0.917 | 1.000 | 0.333 | 1.000 | 1503 |
| C hybrid | 0.875 | 0.846 | 1.000 | 0.353 | 1.000 | 1486 |
| D hybrid+verify | 0.875 | 0.846 | 1.000 | 0.353 | 1.000 | 1486 |
| D-lite text+verify | 0.708 | 0.909 | 1.000 | 0.316 | 1.000 | 1346 |

Recall@5 and the type table match the CPU run. p50 is lower: text 1819 → 1346, visual 2104 → 1503, hybrid 2675 → 1486. Hybrid is close to visual-only because both encoders are on GPU; the remaining wall time is DeepSeek. Citation page hit and abstain precision moved (hybrid cite 0.923 → 0.846 from extra generator misses on q012 and q020). That is not a retrieve regression.

`eval/results/2026-09-08/` is an earlier text-only run. Do not mix rows across dates: generator behavior moved (citation page hit 0.556 → 0.917 on text). Use 2026-09-10 for CPU comparisons and 2026-09-10-gpu for CUDA latency.

## Failure and win cases

**Visual win, q017** (figure): "What image-centric layout dataset is named on the LayoutLMv3 teaser figure?" Gold is page 1, `PubLayNet`. Text retrieve never ranked page 1 and cited page 2 with an unverified quote. Visual and hybrid retrieved page 1 and cited `(b) Image-centric layout anal- ysis on PubLayNet`, verified. That is the case text RAG is supposed to lose.

**Still wrong page, q012** (table): Table 2 lives on ColPali page 7. No mode ranked page 7. Visual answered `nDCG@5` citing page 21 (the metric restated). Hybrid cited page 4 (Table 1). The string is right; the box is not.

**Nobody finds the slide, q016** (figure): first-slide title `Expanding Our View` is page 1 of the Roman deck. Text, visual, and hybrid all ranked later slides (26, 4) and the generator abstained. Page-level ColQwen2 did not save this one.

**Retrieve helped, generate did not, q011** (table): visual and hybrid both put GLUE page 2 (the CoLA table) in the top 5. Text did not. All three modes still abstained `unanswerable`. Recall@5 credits visual; the answer field stays empty.

Wrong-page citation tables for each mode: `eval/results/2026-09-10/report.md` (CPU) and `eval/results/2026-09-10-gpu/report.md` (CUDA).

## Score cutoff

`RETRIEVAL_MIN_SCORE` is not wired. `low_retrieval_score` is unused.

On this gold, unanswerable rows still retrieve (top-hit scores about 0.43–0.59). Answerable hits sit in the same band (about 0.50–0.73). A cutoff of `0.35` would never fire. A threshold high enough to drop unanswerable hits would also drop answerable ones. We abstain on `no_hits`, `verify_failed`, `unsupported`, `generator_invalid`, and model `unanswerable` only.

If you tune later, record the value and the six question ids in this file. Do not pick the threshold on the full 30.

## CI

`uv run pytest tests/` is GPU-free. It uses a one-page fixture PDF and mocked retrieve/generate. It does not download the corpus or ColQwen2. GPU tests are `pytest.mark.gpu` and are skipped in CI.
