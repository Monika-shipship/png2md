from __future__ import annotations

import hashlib
from pathlib import Path

from .files import write_json


PADDLEOCR_CACHE_SCHEMA_VERSION = 1


def paddleocr_cache_root(output_folder: str | Path) -> Path:
    return Path(output_folder) / ".paddleocr_cache"


def cache_key_for_source(
    source: str | Path,
    *,
    page_ranges: str | None = None,
    model: str = "PaddleOCR-VL-1.6",
) -> str:
    text = f"{Path(source).resolve() if Path(str(source)).exists() else source}|{page_ranges or ''}|{model}"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]


def task_cache_dir(output_folder: str | Path, cache_key: str) -> Path:
    return paddleocr_cache_root(output_folder) / cache_key


def write_task_manifest(dest_dir: str | Path, **metadata) -> None:
    write_json(
        Path(dest_dir) / "paddleocr_task_manifest.json",
        {
            "schema_version": PADDLEOCR_CACHE_SCHEMA_VERSION,
            **metadata,
        },
    )
