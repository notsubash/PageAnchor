# PageAnchor

Visually grounded document Q&A with verifiable page citations.

Every answer must cite a verifiable region on a page, or refuse. Web, MCP, CLI, and eval call the same grounding layer.

This repo is Apache-2.0 for code. Per-document licenses are in [corpus/LICENSE.md](corpus/LICENSE.md). PDFs are not committed; hashes in `corpus/manifest.json` are the source of truth.

## Stack notes

Vector storage is **LanceDB** (embedded, Apache-2.0) at `LANCEDB_URI` (default `./corpus/lancedb`). There is no vector-database container.

The answer generator is **DeepSeek V4** (`deepseek-v4-flash` by default) via the OpenAI Python SDK pointed at `https://api.deepseek.com`.

Retrieval encoders:

- **Text:** `Qwen/Qwen3-Embedding-0.6B` (local, Apache-2.0) through `sentence-transformers`. DeepSeek has no embeddings API.
- **Visual:** `vidore/colqwen2-v1.0` is configured but not wired into `ask` yet.

Layout defaults to **PyMuPDF** text blocks so gold quotes stay stable on Windows. Set `PAGEANCHOR_LAYOUT=docling` (and `uv sync --extra ingest`) to use Docling instead; that changes region text and is a freeze bump.

Query and passage embeddings truncate at 1024 tokens. Region chunks are 1500 characters, so that ceiling is enough; the model default of 32k is too slow on CPU.

## Development

Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --extra dev
cp .env.example .env   # set DEEPSEEK_API_KEY
uv run pytest
uv run ruff check .
```

## Corpus, ask, eval

```bash
uv run pageanchor ingest --all
uv run pageanchor ask "What benchmark does ColPali introduce?" --mode text
uv run pageanchor eval --gold corpus/eval/gold_questions.jsonl --modes text,text+verify --out eval/results/2026-09-08
```

`ingest --all` is idempotent: the same PDF hash with existing pages, regions, and LanceDB rows is skipped.

If Docling is required, `docker compose --profile ingest up` runs ingest in Linux.

CI runs pytest and ruff only. It does not download the corpus, Docling, or GPU models.
