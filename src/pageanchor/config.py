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
VISUAL_TABLE = "pageanchor_visual"
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


def torch_pair_hint(exc: BaseException, what: str) -> str:
    torch_v = "missing"
    torchvision_v = "missing"
    try:
        import torch

        torch_v = torch.__version__
    except Exception:
        pass
    try:
        import importlib.metadata as metadata

        torchvision_v = metadata.version("torchvision")
    except Exception:
        pass
    parts: list[str] = []
    seen: set[int] = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        parts.append(str(current))
        current = current.__cause__
    return (
        f"{what} (torch={torch_v}, torchvision={torchvision_v}): {' | '.join(parts)}. "
        "Torch and torchvision must match. After the visual extra, overlay CUDA 12.8 "
        "wheels with `uv pip install torch torchvision --index-url "
        "https://download.pytorch.org/whl/cu128` and run the API with `uv run --no-sync`."
    )


def torch_device() -> str:
    """cuda if available, else cpu. PAGEANCHOR_DEVICE=cpu|cuda overrides."""
    import torch

    forced = os.getenv("PAGEANCHOR_DEVICE", "").strip().lower()
    if forced == "cpu":
        return "cpu"
    if forced == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError(
                "PAGEANCHOR_DEVICE=cuda but torch cannot see a GPU. "
                "Install CUDA torch: uv pip install torch torchvision "
                "--index-url https://download.pytorch.org/whl/cu128"
            )
        return "cuda"
    if forced:
        raise ValueError("PAGEANCHOR_DEVICE must be cpu, cuda, or empty")
    return "cuda" if torch.cuda.is_available() else "cpu"


def torch_env() -> dict[str, str | bool | None]:
    try:
        import torch
    except ImportError:
        return {"torch": None, "cuda": False, "device": "unknown"}
    cuda = torch.cuda.is_available()
    return {
        "torch": torch.__version__,
        "cuda": cuda,
        "device": torch.cuda.get_device_name(0) if cuda else "cpu",
    }


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
