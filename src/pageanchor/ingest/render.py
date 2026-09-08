from __future__ import annotations

from pathlib import Path

import pymupdf


def render_pdf(pdf_path: Path, out_dir: Path, dpi: int = 180) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(pdf_path)
    paths: list[Path] = []
    try:
        matrix = pymupdf.Matrix(dpi / 72, dpi / 72)
        for page in doc:
            dest = out_dir / f"p{page.number + 1}.png"
            page.get_pixmap(matrix=matrix, alpha=False).save(dest)
            paths.append(dest)
    finally:
        doc.close()
    return paths
