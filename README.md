# PageAnchor

Visually grounded document Q&A with verifiable page citations.

Every answer must cite a verifiable region on a page, or refuse. Web, MCP, CLI, and eval call the same grounding layer.

This repo is Apache-2.0 for code. Per-document licenses are in [corpus/LICENSE.md](corpus/LICENSE.md). PDFs are not committed; hashes in `corpus/manifest.json` are the source of truth.

## Stack notes

Vector storage is **LanceDB** (embedded, Apache-2.0) at `LANCEDB_URI` (default `./corpus/lancedb`). There is no vector-database container.

The answer generator is **DeepSeek V4** (`deepseek-v4-flash` by default) via the OpenAI Python SDK pointed at `https://api.deepseek.com`.

Retrieval encoders:

- **Text:** `Qwen/Qwen3-Embedding-0.6B` (local, Apache-2.0) through `sentence-transformers`. DeepSeek has no embeddings API.
- **Visual:** `vidore/colqwen2-v1.0` (ColQwen2, Apache-2.0) through `colpali-engine`. Page multi-vectors go in LanceDB table `pageanchor_visual`; queries use brute-force numpy MaxSim. Install with `uv sync --extra visual`. Default `ask` mode is `hybrid` (RRF of text + visual pages).

Layout defaults to **PyMuPDF** text blocks so gold quotes stay stable on Windows. Set `PAGEANCHOR_LAYOUT=docling` (and `uv sync --extra ingest`) to use Docling instead; that changes region text and is a freeze bump.

Query and passage embeddings truncate at 1024 tokens. Region chunks are 1500 characters, so that ceiling is enough; the model default of 32k is too slow on CPU.

## Development

Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --extra dev --extra api
cp .env.example .env   # set DEEPSEEK_API_KEY
uv run pytest
uv run ruff check .
```

Visual retrieve is optional and heavy (torch + ColQwen2):

```bash
uv sync --extra visual
```

## Corpus, ask, eval

```bash
uv run pageanchor ingest --all
uv run pageanchor ingest --visual --all
uv run pageanchor ask "What benchmark does ColPali introduce?" --mode hybrid
uv run pageanchor eval --gold corpus/eval/gold_questions.jsonl --modes text,visual,hybrid,hybrid+verify --out eval/results/2026-09-09
```

`ingest --all` is idempotent: the same PDF hash with existing pages, regions, and LanceDB rows is skipped. `--visual` adds ColQwen2 page vectors; re-running skips docs already in `pageanchor_visual`.

If Docling is painful on Windows, `docker compose --profile ingest up` runs text ingest in Linux.

For ColQwen2 visual indexing:

```bash
docker compose --profile ingest run --rm ingest bash -lc "uv sync --extra ingest --extra visual && uv run pageanchor ingest --visual --all"
```

CI runs pytest and ruff only. It does not download the corpus, Docling, or GPU models.

## HTTP API and web overlay

Same `GroundedAnswer` as `pageanchor ask`, drawn on the ingested page PNG.

```bash
uv run --extra api python -m uvicorn pageanchor.api.main:app --reload --port 8000
```

```bash
cd apps/web
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The browser talks only to `http://localhost:8000` (CORS is that origin only). Override the API URL with `NEXT_PUBLIC_API_URL`.

```bash
curl -s http://localhost:8000/health
curl -s http://localhost:8000/v1/answer -H "content-type: application/json" \
  -d "{\"question\":\"What is the title of Table A in the January 2025 CPI release?\",\"mode\":\"hybrid\",\"strict\":true}"
```

`docker compose up api` bind-mounts `corpus/` (LanceDB stays on disk). Run `npm run dev` in `apps/web` next to it. If the visual table is missing, switch the UI mode to `text`.
