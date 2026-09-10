# Architecture

Every client answers with the same Pydantic object: `GroundedAnswer` from `pageanchor.ground.answer.grounded_answer`. CLI and MCP return it as-is. `POST /v1/answer` also copies `trace.trace_id` to a top-level `trace_id` for the overlay. If the core fields disagree across clients, the adapters are wrong, not the model.

```
apps/web (Next.js)  →  HTTP  →  pageanchor.api (FastAPI)
                                      │
CLI / eval / MCP  ─────────────────────►  pageanchor.{ingest,retrieve,ground}
                                      │
                                      ▼
                         pages PNG | regions JSON | LanceDB
```

`pageanchor` is one installable package. Ingest, retrieve, ground, and verify do not import FastAPI, MCP, or anything under `apps/web`. FastAPI, MCP, CLI, and eval are thin wrappers around the same functions.

The browser talks HTTP because it cannot import Python. MCP imports core directly. A second HTTP backend for MCP would drift from CLI and eval; we did not add one.

## Data

The corpus is frozen and local. `corpus/manifest.json` is the source of truth for document ids, page counts, SHA-256, licenses, and `frozen_at`. PDFs are not in git. `pageanchor ingest --all` fetches each `download_url` over HTTPS and refuses a file whose hash does not match.

Ingest writes:

| Artifact | Path | Role |
| --- | --- | --- |
| Page images | `corpus/pages/{doc_id}/p{page}.png` | Overlay and visual index. 180 DPI, 1-based `p{n}.png`. |
| Layout regions | `corpus/regions/{doc_id}.json` | `Region[]` with normalized bboxes and extracted text. |
| Text index | LanceDB table `pageanchor_text` | One row per region chunk; payload `doc_id`, `page`, `region_id`, `bbox`. |
| Visual index | LanceDB table `pageanchor_visual` | One row per page; ColQwen2 multi-vector blob. |

LanceDB is a directory (`LANCEDB_URI`, default `./corpus/lancedb`). There is no vector-database container.

Layout defaults to PyMuPDF text blocks so gold quotes stay stable on Windows. `PAGEANCHOR_LAYOUT=docling` (and `uv sync --extra ingest`) switches the extractor; that changes region text and needs a freeze bump.

## Ask path

`grounded_answer(question, mode, strict=True)`:

1. **Retrieve pages.** `text` embeds the query with Qwen3-Embedding-0.6B and collapses chunks to `(doc_id, page)`. `visual` encodes the query with ColQwen2 and scores every page with numpy MaxSim (brute force; fine until the corpus is far past a thousand pages). Encoders use CUDA when `torch.cuda.is_available()` (override with `PAGEANCHOR_DEVICE=cpu` or `cuda`). `hybrid` is Reciprocal Rank Fusion over page keys, `k_rrf=60`. Default production mode is `hybrid`.
2. **Select regions.** On each hit page, rank stored regions by token Jaccard with the query (question stopwords dropped). Keep the global top 5.
3. **Generate.** DeepSeek V4 (`deepseek-v4-flash` via the OpenAI SDK) must return structured `GeneratorOutput`: an answer or abstain, plus citations whose `region_id` is in the prompt and whose `quote` is a verbatim substring of that region.
4. **Verify.** Each quote is checked with `verify_quote` against the cited region's text. The answer is checked with `answer_in_quote` against each quote. `verified` is both.
5. **Policy.** Empty hits → `abstain_reason="no_hits"`. Unknown `region_id`, unparseable generator output, empty citations, or a null answer while not abstaining → `generator_invalid`. Generator `abstain=true` → `unanswerable`. If `strict` and any citation fails quote-in-region → `abstain=true`, `answer=None`, `abstain_reason="verify_failed"`. If the quotes are in their regions but the answer is not a normalized substring of any citation quote, `abstain_reason="unsupported"`. Citations stay on the object with `verified=false` so the trace is inspectable. There is no retry loop.

`Trace` (hits, selected regions, verify rows, timings, `trace_id`) is part of the answer, not a side log.

## Verify

Normalization is Unicode NFKC, whitespace collapsed to single spaces, strip, **case preserved**. `"ViDoRe"` does not match `"vidore"`. Table cells and proper nouns are the product.

Verify is a substring check. It does not score entailment. `verified` requires quote-in-region and answer-in-quote. Wrong-page restatements that happen to contain the answer string can still pass; that remains a retrieval miss, scored as citation-page error.

`low_retrieval_score` exists on `AbstainReason` but is unused. There is no global score cutoff; see [EVAL.md](EVAL.md).

## HTTP vs MCP

| Client | Transport | Why |
| --- | --- | --- |
| Web overlay | `http://localhost:8000` | Browser. CORS allows `http://localhost:3000` only. No auth. |
| CLI / eval | in-process | Same functions, JSON on stdout. |
| MCP | stdio | Agent host spawns `python -m pageanchor.mcp.server`. Tools call core. Resources serve manifest, metadata, page PNGs, and regions. |

MCP tool copy tells the agent not to state a fact until nested verify is true, and not to guess page content: call `select_evidence`.

## Pages and boxes

Pages are 1-based everywhere (API, MCP, gold, UI). BBoxes are `x0, y0, x1, y1` in `[0, 1]`, origin top-left, page-relative. The overlay draws `Citation.bbox` on the ingested PNG, so retrieve space and pixel space match.

## Non-goals

User upload, auth, chat history, SSE MCP, an HTTP MCP client, ColPali patch-to-region fusion, generator retry, and a second corpus format. If a behavior is needed in two clients, it belongs in core.
