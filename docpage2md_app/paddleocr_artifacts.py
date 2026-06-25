from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .files import read_json


@dataclass(frozen=True)
class PaddleOCRArtifacts:
    root: Path
    job_json: Path | None
    result_json: Path | None
    result_jsonl: Path | None
    result_md: Path | None
    image_manifest_json: Path | None
    images_dir: Path | None

    def to_manifest(self) -> dict[str, str | None]:
        return {
            "root": str(self.root),
            "job_json": _path_str(self.job_json),
            "result_json": _path_str(self.result_json),
            "result_jsonl": _path_str(self.result_jsonl),
            "result_md": _path_str(self.result_md),
            "image_manifest_json": _path_str(self.image_manifest_json),
            "images_dir": _path_str(self.images_dir),
        }


def discover_paddleocr_artifacts(root: str | Path) -> PaddleOCRArtifacts:
    artifact_root = Path(root)
    if not artifact_root.exists() or not artifact_root.is_dir():
        raise FileNotFoundError(f"PaddleOCR artifact directory not found: {artifact_root}")
    return PaddleOCRArtifacts(
        root=artifact_root,
        job_json=_existing(artifact_root / "job.json"),
        result_json=_existing(artifact_root / "result.json"),
        result_jsonl=_existing(artifact_root / "result.jsonl"),
        result_md=_existing(artifact_root / "result.md"),
        image_manifest_json=_existing(artifact_root / "image_manifest.json"),
        images_dir=_existing_dir(artifact_root / "images"),
    )


def load_artifact_json(path: Path | None) -> Any:
    if path is None:
        return None
    return read_json(path)


def resolve_artifact_image(artifacts: PaddleOCRArtifacts, image_ref: str | None) -> Path | None:
    raw = str(image_ref or "").strip()
    if not raw:
        return None
    path = Path(raw)
    if path.is_absolute() and path.exists() and path.is_file():
        return path
    normalized = raw.lstrip("/\\")
    candidates = [artifacts.root / normalized]
    if artifacts.images_dir is not None:
        candidates.append(artifacts.images_dir / normalized)
        candidates.append(artifacts.images_dir / Path(normalized).name)
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    manifest = load_artifact_json(artifacts.image_manifest_json)
    if isinstance(manifest, dict):
        local = manifest.get(raw) or manifest.get(normalized)
        if isinstance(local, str):
            return resolve_artifact_image(artifacts, local)
    return None


def _existing(path: Path) -> Path | None:
    return path if path.exists() and path.is_file() else None


def _existing_dir(path: Path) -> Path | None:
    return path if path.exists() and path.is_dir() else None


def _path_str(path: Path | None) -> str | None:
    return str(path) if path is not None else None
