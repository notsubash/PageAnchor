from pathlib import Path

import pytest

FIXTURE_PDF = Path(__file__).parent / "fixtures" / "hello.pdf"


@pytest.fixture
def hello_pdf() -> Path:
    assert FIXTURE_PDF.exists()
    return FIXTURE_PDF
