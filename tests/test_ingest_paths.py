import pytest

from pageanchor.config import under_root
from pageanchor.ingest import download_pdf


def test_under_root_rejects_escape(tmp_path):
    with pytest.raises(ValueError):
        under_root(tmp_path, "..", "outside.txt")


def test_download_rejects_non_https(tmp_path):
    dest = tmp_path / "pdfs" / "x.pdf"
    with pytest.raises(ValueError, match="https"):
        download_pdf(
            {
                "id": "x",
                "download_url": "http://example.com/doc.pdf",
                "sha256": "abc",
            },
            dest,
        )
