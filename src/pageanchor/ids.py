from __future__ import annotations

import uuid


def region_id(doc_id: str, page: int, index: int) -> str:
    return f"{doc_id}:p{page}:r{index}"


def new_trace_id() -> str:
    return str(uuid.uuid4())
