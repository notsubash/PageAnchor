from __future__ import annotations

from mcp.server import MCPServer

from pageanchor.mcp.resources import register_resources
from pageanchor.mcp.tools import register_tools

mcp = MCPServer(
    "PageAnchor",
    instructions=(
        "PageAnchor answers only from a frozen local PDF corpus. "
        "Do not state a fact until verify_quote is true. "
        "Do not guess page content; call select_evidence. "
        "Workflow: search_documents, then select_evidence on a top hit, "
        "draft from region text only, then verify_quote per claim. "
        "Optional grounded_answer matches the CLI and web UI object."
    ),
)
register_resources(mcp)
register_tools(mcp)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
