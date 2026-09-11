# MCP

Same retrieve, region, verify, and answer functions as the CLI and HTTP API, over stdio. The server imports `pageanchor` core. It does not call HTTP (see [ARCHITECTURE.md](ARCHITECTURE.md)).

Do not state a fact until nested verify is true (`quote_in_region` and `answer_in_quote`). Do not guess page content; call `select_evidence`.

## Run

`uv sync` replaces extras. Keep `mcp` on the same sync as whatever else you use:

```bash
uv sync --extra dev --extra api --extra mcp
uv run python -m pageanchor.mcp.server
```

Or add the extra only for this process: `uv run --extra mcp python -m pageanchor.mcp.server`.

Cursor (or Claude Desktop) launches that command as a subprocess. Stdout is the protocol; keep logs on stderr.

`load_settings()` reads `.env` from the process working directory. Put `DEEPSEEK_API_KEY` there (see `.env.example`). Never put a real API key in MCP config.

## Cursor

Project file `.cursor/mcp.json`, or the same object under Cursor Settings → MCP:

```json
{
  "mcpServers": {
    "pageanchor": {
      "command": "uv",
      "args": [
        "--directory",
        "${workspaceFolder}",
        "run",
        "--extra",
        "mcp",
        "python",
        "-m",
        "pageanchor.mcp.server"
      ],
      "env": {
        "PAGEANCHOR_CORPUS_ROOT": "${workspaceFolder}/corpus",
        "LANCEDB_URI": "${workspaceFolder}/corpus/lancedb"
      }
    }
  }
}
```

`${workspaceFolder}` is the repo root. `DEEPSEEK_API_KEY` stays in `.env` (or your OS environment). Do not paste a key into this JSON.

Ingest the corpus before searching (`uv run pageanchor ingest --all`). Visual/hybrid search also needs `uv run pageanchor ingest --visual --all`.

## Resources


| URI                                  | MIME             | Body                  |
| ------------------------------------ | ---------------- | --------------------- |
| `corpus://manifest`                  | application/json | manifest              |
| `doc://{doc_id}/meta`                | application/json | title, pages, license |
| `doc://{doc_id}/page/{page}`         | image/png        | page PNG              |
| `doc://{doc_id}/page/{page}/regions` | application/json | regions               |

Pages are 1-based.

## Tools


| Tool               | Core function               |
| ------------------ | --------------------------- |
| `search_documents` | `search_text/visual/hybrid` |
| `get_page_regions` | load regions JSON           |
| `select_evidence`  | `select_regions`            |
| `verify_quote`     | `verify_quote` on stored region text |
| `grounded_answer`  | `grounded_answer`           |
| `export_receipt`   | `build_receipt` from a `GroundedAnswer` |

`grounded_answer` returns the same `GroundedAnswer` object as `pageanchor ask` and `POST /v1/answer`.

## Agent workflow

1. `search_documents`
2. `select_evidence` on a top hit
3. Draft from region text only
4. Nested verify per claim (quote in region, answer in quote)
5. Optional `grounded_answer` for parity with the web UI
6. Optional `export_receipt` for the PDF hashes behind the citations
