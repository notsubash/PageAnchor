# PageAnchor

Visually grounded document Q&A with verifiable page citations.

Every answer must cite a verifiable region on a page, or refuse. Web, MCP, CLI, and eval call the same grounding layer.

**Implementation plan:** [docs/PLAN.md](docs/PLAN.md)

This repo is Apache-2.0 for code. Per-document licenses live with the frozen corpus once it is added.

## Stack notes

Vector storage is **LanceDB** (embedded, Apache-2.0) at `LANCEDB_URI` (default `./corpus/lancedb`). There is no vector-database container. Docker Compose is a stub until the Phase 3 API service.

The answer generator is **DeepSeek V4** (`deepseek-v4-flash` by default) via the OpenAI Python SDK pointed at `https://api.deepseek.com`.

Retrieval uses two encoders, not one CLIP-style model:

- **Text (Phase 1):** `Qwen/Qwen3-Embedding-0.6B` (local, Apache-2.0). DeepSeek has no embeddings API. MiniLM is too weak for tables and papers.
- **Visual (Phase 2):** `vidore/colqwen2-v1.0` (ColPali-family late interaction, Apache-2.0). Page-as-image multi-vectors + MaxSim. The original ColPali checkpoint is Gemma-licensed, so we do not use it.

## Development

Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
```

Copy `.env.example` to `.env` and set `DEEPSEEK_API_KEY` when you reach generator work in Phase 1. The generator uses DeepSeek V4 (`deepseek-v4-flash` by default) through the OpenAI-compatible SDK at `https://api.deepseek.com`.
