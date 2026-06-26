from __future__ import annotations

import shutil
from pathlib import Path

from .config import DEFAULT_OUTPUT_RETENTION, OUTPUT_RETENTION_MODES, AppConfig
from .run_logger import ProgressCallback, safe_progress


def output_retention_mode(config: AppConfig) -> str:
    mode = str(getattr(config, "output_retention", DEFAULT_OUTPUT_RETENTION) or DEFAULT_OUTPUT_RETENTION).strip().lower()
    return mode if mode in OUTPUT_RETENTION_MODES else DEFAULT_OUTPUT_RETENTION


def should_write_ir(config: AppConfig) -> bool:
    return output_retention_mode(config) in {"standard", "debug"}


def should_copy_raw_artifacts(config: AppConfig) -> bool:
    return output_retention_mode(config) == "debug"


def should_cleanup_parser_cache(config: AppConfig) -> bool:
    return output_retention_mode(config) == "slim"


def retention_report(config: AppConfig) -> dict[str, object]:
    mode = output_retention_mode(config)
    return {
        "mode": mode,
        "writes_ir": should_write_ir(config),
        "copies_raw_artifacts": should_copy_raw_artifacts(config),
        "cleans_parser_cache": should_cleanup_parser_cache(config),
        "note": (
            "slim keeps final Markdown, referenced assets, metadata and run_report; "
            "standard also keeps IR; debug also keeps raw parser artifacts and cache."
        ),
    }


def cleanup_generated_cache_dir(cache_dir: str | Path, config: AppConfig, *, progress: ProgressCallback | None = None) -> None:
    if not should_cleanup_parser_cache(config):
        return
    target = Path(cache_dir)
    if not target.exists():
        return
    try:
        shutil.rmtree(target)
        safe_progress(progress, f"Parser cache cleaned by slim retention: {target}")
    except OSError as exc:
        safe_progress(progress, f"Parser cache cleanup skipped: {target}, reason={exc}")


def cleanup_cache_for_artifact_dir(
    artifact_dir: str | Path,
    config: AppConfig,
    *,
    expected_cache_root_name: str,
    progress: ProgressCallback | None = None,
) -> None:
    artifact = Path(artifact_dir)
    cache_dir = artifact.parent if artifact.name == "artifact" else artifact
    if cache_dir.parent.name != expected_cache_root_name:
        return
    cleanup_generated_cache_dir(cache_dir, config, progress=progress)
