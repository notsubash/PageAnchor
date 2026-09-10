from pathlib import Path

import pytest

FIXTURE_PDF = Path(__file__).parent / "fixtures" / "hello.pdf"


@pytest.fixture(autouse=True)
def fake_text_embedder(monkeypatch: pytest.MonkeyPatch) -> None:
    # Unit tests stay GPU-free. Tests that care about ranking inject embed_query.
    def fake(texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] for _ in texts]

    monkeypatch.setattr("pageanchor.embed.embed_queries", fake)
    monkeypatch.setattr("pageanchor.embed.embed_passages", fake)


@pytest.fixture
def hello_pdf() -> Path:
    assert FIXTURE_PDF.exists()
    return FIXTURE_PDF
