# PageAnchor

**Every answer cites a verifiable region on a page, or it refuses.**

Text-only RAG is fluent and uncheckable on layout-heavy PDFs. PageAnchor retrieves pages, picks layout regions, asks the generator for verbatim quotes, and keeps the answer only if each quote is a normalized substring of the cited region. Web, CLI, MCP, and eval call the same `grounded_answer` function.

![Citation overlay on BLS CPI Table A](docs/images/citation-overlay.png)

Code is Apache-2.0. Per-document licenses: [corpus/LICENSE.md](corpus/LICENSE.md). PDFs are not in git; SHA-256 in `corpus/manifest.json` is the source of truth.

## Layout

```
apps/web (Next.js)  →  HTTP  →  pageanchor.api (FastAPI)
                                      │
CLI / eval / MCP  ─────────────────────►  pageanchor.{ingest,retrieve,ground}
                                      │
                                      ▼
                         pages PNG | regions JSON | LanceDB
```

LanceDB is a directory (`LANCEDB_URI`, default `./corpus/lancedb`). There is no vector-database container. Default ask mode is `hybrid` (RRF of text + visual pages). Overlay draws `Citation.bbox` on the ingested PNG.

Details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) · [docs/API.md](docs/API.md) · [docs/MCP.md](docs/MCP.md) · [docs/EVAL.md](docs/EVAL.md)

## Run

Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --extra dev --extra api --extra mcp
cp .env.example .env   # set DEEPSEEK_API_KEY
uv run pytest
uv run ruff check .
```

Visual retrieve needs torch + ColQwen2. `uv sync` replaces extras, so list every extra you need:

```bash
uv sync --extra dev --extra api --extra mcp --extra visual
```

### Corpus

```bash
uv run pageanchor ingest --all
uv run pageanchor ask "What is the title of Table A in the January 2025 CPI release?" --mode text
```

`ingest --all` is idempotent: the same PDF hash with existing pages, regions, and LanceDB rows is skipped.

Visual retrieve: `uv sync --extra visual` then `pageanchor ingest --visual --all`. After that, `--mode hybrid` is the default production path. `--visual` fills `pageanchor_visual`; re-running skips docs already indexed.

If Docling or ColQwen2 is painful on Windows:

```bash
docker compose --profile ingest up
docker compose --profile ingest run --rm ingest bash -lc \
  "uv sync --extra ingest --extra visual && uv run pageanchor ingest --visual --all"
```

CI runs pytest and ruff only. It does not download the corpus or GPU models.

### Overlay

```bash
docker compose up api
# or: uv run --extra api python -m uvicorn pageanchor.api.main:app --reload --port 8000
```

```bash
cd apps/web && npm install && npm run dev
```

Open http://localhost:3000. The browser talks only to `http://localhost:8000` (CORS is that origin). Override with `NEXT_PUBLIC_API_URL`. If the visual table is missing, set the UI mode to `text`.

Need a GPU or a DeepSeek key to demo live answers. Without them you can still read this README, the eval table, and the overlay screenshot.

### MCP

Stdio. Cursor config: [`.cursor/mcp.json`](.cursor/mcp.json) (`${workspaceFolder}`, no API keys). `DEEPSEEK_API_KEY` stays in `.env`.

```json
{
  "mcpServers": {
    "pageanchor": {
      "command": "uv",
      "args": ["--directory", "${workspaceFolder}", "run", "--extra", "mcp", "python", "-m", "pageanchor.mcp.server"],
      "env": {
        "PAGEANCHOR_CORPUS_ROOT": "${workspaceFolder}/corpus",
        "LANCEDB_URI": "${workspaceFolder}/corpus/lancedb"
      }
    }
  }
}
```

Do not state a fact until `verify_quote` is true. Do not guess page content; call `select_evidence`. Full tool list: [docs/MCP.md](docs/MCP.md).

## Eval

Frozen gold: 30 questions (6 each of plain text, table, figure, layout, unanswerable), `frozen_at=2026-09-08`.

Committed run (`eval/results/2026-09-08/`, Windows CPU, text retrieve, `deepseek-v4-flash`):

| system | recall@5 | citation page hit | verify pass | abstain P | abstain R | p50 ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A text | 0.708 | 0.556 | 1.000 | 0.500 | 1.000 | 1825 |
| D-lite text+verify | 0.708 | 0.556 | 1.000 | 0.500 | 1.000 | 1825 |

A and D-lite match: the generator did not keep unverified quotes. Abstain recall is 1.0 on the six unanswerable items. Precision is 0.5 because six answerable questions were also refused.

Text retrieve cited the wrong page on table and slide questions even when the answer string looked right. **q011** answered `8.5k` for GLUE CoLA size while citing page 8 headings; gold is the table on page 2. Verify passed. That is the thesis: fluency is not evidence. Reproduce and metric definitions: [docs/EVAL.md](docs/EVAL.md).

Reproduce the table:

```bash
uv run pageanchor eval --gold corpus/eval/gold_questions.jsonl \
  --modes text,text+verify --out eval/results/$(date +%F)
```

Visual / hybrid (B, C, D) need `--extra visual` and the visual index:

```bash
uv run pageanchor eval --gold corpus/eval/gold_questions.jsonl \
  --modes text,visual,hybrid,hybrid+verify --out eval/results/$(date +%F)
```

Commit a new dated folder; do not silently edit gold.

## Stack

- Generator: DeepSeek V4 (`deepseek-v4-flash`) via the OpenAI SDK at `https://api.deepseek.com`
- Text retrieve: `Qwen/Qwen3-Embedding-0.6B` (sentence-transformers)
- Visual retrieve: `vidore/colqwen2-v1.0` (ColQwen2), page MaxSim
- Layout: PyMuPDF (default) or Docling
- Web: Next.js 15, PNG overlay (not PDF.js)

## Not v1

User upload, auth, multi-tenant, chat history, SSE MCP, Kubernetes, HF Space, ColPali fine-tune, generator retry, IoU vs hand-drawn boxes, crawling.

## Write-up

Outline for a portfolio post (not in this repo):

1. Why fluent RAG is uncheckable on tables and slides
2. One `GroundedAnswer` behind CLI, HTTP, and MCP
3. Ablation table and the q011 miss ([docs/EVAL.md](docs/EVAL.md))
4. Overlay screenshot above
5. What we refused to build
