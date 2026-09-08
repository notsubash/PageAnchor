from __future__ import annotations

import re
import unicodedata


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    return re.sub(r"\s+", " ", text).strip()


def verify_quote(quote: str, region_text: str) -> bool:
    normalized_quote = _normalize(quote)
    if not normalized_quote:
        return False
    return normalized_quote in _normalize(region_text)
