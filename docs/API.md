# HTTP API

FastAPI app: `pageanchor.api.main:app`. Same `GroundedAnswer` as `pageanchor ask` and the MCP `grounded_answer` tool.

```bash
uv run --extra api python -m uvicorn pageanchor.api.main:app --reload --port 8000
```

Or `docker compose up api` (bind-mounts the repo; LanceDB stays on disk). CORS: `http://localhost:3000` only. No authentication.

Every JSON response includes `trace_id` (UUID4). `POST /v1/answer` also returns the full `trace` object; the top-level `trace_id` duplicates `trace.trace_id`.

Pages are 1-based. BBoxes are normalized `[x0, y0, x1, y1]`.

## Routes

| Method | Path | Maps to |
| --- | --- | --- |
| GET | `/health` | Process up, whether LanceDB opened, table row counts |
| GET | `/v1/corpus` | `manifest.json` |
| GET | `/v1/docs/{doc_id}` | Manifest row |
| GET | `/v1/docs/{doc_id}/pages/{page}` | Page PNG (`image/png`) |
| GET | `/v1/docs/{doc_id}/pages/{page}/regions` | `Region[]` |
| POST | `/v1/search` | `search_text` / `search_visual` / `search_hybrid` |
| POST | `/v1/evidence` | `select_regions` |
| POST | `/v1/verify` | `verify_quote` against the stored region |
| POST | `/v1/answer` | `grounded_answer` |
| POST | `/v1/receipt` | `build_receipt` from a `GroundedAnswer` |

## Bodies

```json
POST /v1/search    { "query": "...", "k": 5, "mode": "hybrid" }
POST /v1/evidence   { "query": "...", "doc_id": "...", "page": 3, "max_regions": 5 }
POST /v1/verify     { "quote": "...", "doc_id": "...", "page": 14, "region_id": "..." }
POST /v1/answer     { "question": "...", "mode": "hybrid", "strict": true }
POST /v1/receipt    <GroundedAnswer JSON from /v1/answer>
```

`mode` is `text` | `visual` | `hybrid`. Default for search and answer is `hybrid`. `strict` defaults to `true`. The overlay only offers those three keys. `bm25` is a CLI/eval retrieve mode on `grounded_answer`, not an overlay button.

`POST /v1/receipt` takes the same `GroundedAnswer` object and returns a receipt: question, answer, abstain, citations, nested verify rows, cited `doc_id` → manifest `sha256`, `ingest_version`, layout engine, retrieve mode, `trace_id`, generator model. Use this so PDF hashes cannot drift from a client-side copy.

`POST /v1/answer` returns a `GroundedAnswer`:

```json
{
  "question": "...",
  "answer": "string or null",
  "abstain": false,
  "abstain_reason": null,
  "citations": [
    {
      "doc_id": "bls-cpi-20250115",
      "page": 2,
      "region_id": "bls-cpi-20250115:p2:r13",
      "bbox": [0.09, 0.44, 0.75, 0.46],
      "quote": "Table A. Percent changes in CPI for All Urban Consumers (CPI-U): U.S. city average",
      "verified": true
    }
  ],
  "trace": {
    "trace_id": "...",
    "retrieval_mode": "hybrid",
    "hits": [],
    "regions": [],
    "verify": [],
    "timings_ms": {}
  },
  "trace_id": "..."
}
```

`abstain_reason` is one of `low_retrieval_score` (unused), `no_hits`, `verify_failed`, `unsupported`, `unanswerable`, `generator_invalid`.

On abstain, `answer` is `null`. Failed citations remain on `citations` with `verified: false`.

## Errors

| Status | When |
| --- | --- |
| 400 | Invalid `doc_id` (`ValueError`) |
| 422 | Request schema, including `page < 1` |
| 404 | Unknown document, missing page PNG, missing regions, unknown `region_id` |
| 503 | LanceDB missing, visual table missing, or visual encoder failed to import (`FileNotFoundError` / `ImportError` from retrieve / answer) |

Missing visual index: hybrid and visual search return 503 with a message to run `pageanchor ingest --visual`. The UI can still use `mode=text`. ColQwen2 import failures (torch/torchvision mismatch) are also 503; overlay CUDA 12.8 wheels after the visual extra, then `uv run --no-sync`.

## curl

```bash
curl -s http://localhost:8000/health

curl -s http://localhost:8000/v1/answer -H "content-type: application/json" \
  -d "{\"question\":\"What is the title of Table A in the January 2025 CPI release?\",\"mode\":\"hybrid\",\"strict\":true}"
```

The overlay in `apps/web` calls only this API (`NEXT_PUBLIC_API_URL`, default `http://localhost:8000`). Types live in `apps/web/lib/api.ts` and match the Pydantic models by hand.
