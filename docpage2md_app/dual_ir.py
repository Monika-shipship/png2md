from __future__ import annotations

from typing import Any

from .fusion import FUSION_VERSION, fuse_document_irs


DUAL_ADAPTER_VERSION = FUSION_VERSION


def merge_mineru_paddleocr_ir(
    mineru_ir: dict[str, Any],
    paddleocr_ir: dict[str, Any],
    *,
    engine_mode: str = "dual_hybrid",
) -> dict[str, Any]:
    """Backward-compatible wrapper around the checked fusion layer."""
    return fuse_document_irs(mineru_ir, paddleocr_ir, engine_mode=engine_mode).document_ir
