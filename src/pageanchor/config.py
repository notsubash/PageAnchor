from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_GENERATOR_MODEL = "deepseek-v4-flash"
DEFAULT_TEXT_EMBEDDING_MODEL = "Qwen/Qwen3-Embedding-0.6B"
DEFAULT_VISUAL_RETRIEVE_MODEL = "vidore/colqwen2-v1.0"
TEXT_TABLE = "pageanchor_text"
DOC_ID_RE = re.compile(r"^[a-zA-Z0-9._-]+$")
MAX_PDF_BYTES = 100 * 1024 * 1024


def layout_engine() -> str:
    value = os.getenv("PAGEANCHOR_LAYOUT", "pymupdf").strip().lower()
    return value or "pymupdf"


def under_root(root: Path, *parts: str | Path) -> Path:
    resolved_root = root.resolve()
    dest = resolved_root.joinpath(*parts).resolve()
    dest.relative_to(resolved_root)
    return dest


def _as_bool(value: str | None, default: bool = True) -> bool:
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    deepseek_api_key: str
    deepseek_base_url: str
    corpus_root: Path
    lancedb_uri: Path
    generator_model: str
    text_embedding_model: str
    visual_retrieve_model: str
    strict_verify: bool


def load_settings() -> Settings:
    load_dotenv()
    return Settings(
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
        deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", DEFAULT_DEEPSEEK_BASE_URL),
        corpus_root=Path(os.getenv("PAGEANCHOR_CORPUS_ROOT", "./corpus")),
        lancedb_uri=Path(os.getenv("LANCEDB_URI", "./corpus/lancedb")),
        generator_model=os.getenv("GENERATOR_MODEL", DEFAULT_GENERATOR_MODEL),
        text_embedding_model=os.getenv("TEXT_EMBEDDING_MODEL", DEFAULT_TEXT_EMBEDDING_MODEL),
        visual_retrieve_model=os.getenv(
            "VISUAL_RETRIEVE_MODEL", DEFAULT_VISUAL_RETRIEVE_MODEL
        ),
        strict_verify=_as_bool(os.getenv("STRICT_VERIFY"), True),
    )


def generator_client(settings: Settings | None = None) -> OpenAI:
    settings = settings or load_settings()
    return OpenAI(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url)
