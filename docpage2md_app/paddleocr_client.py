from __future__ import annotations

import base64
import json
import mimetypes
import random
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import AppConfig
from .files import write_json, write_text_atomic
from .run_logger import ProgressCallback, safe_progress
from .secrets import get_secret_value


PADDLEOCR_SUPPORTED_MODELS = (
    "PaddleOCR-VL-1.6",
    "PaddleOCR-VL-1.5",
    "PaddleOCR-VL",
    "PP-StructureV3",
    "PP-OCRv5",
)
PADDLEOCR_RETRY_HTTP_STATUS = {429, 503, 504}


class PaddleOCRError(RuntimeError):
    pass


@dataclass(frozen=True)
class PaddleOCRJobStatus:
    job_id: str
    state: str
    trace_id: str | None = None
    error_msg: str | None = None
    result_url: dict[str, str] | None = None
    total_pages: int | None = None
    extracted_pages: int | None = None
    raw: dict[str, Any] | None = None


class PaddleOCRClient:
    def __init__(self, config: AppConfig, *, progress: ProgressCallback | None = None):
        self.config = config
        self.progress = progress
        self.base_url = config.paddleocr_base_url.rstrip("/")
        self.job_url = f"{self.base_url}/api/v2/ocr/jobs"
        self.api_key = get_secret_value(config.paddleocr_api_key_env)
        if not self.api_key:
            raise PaddleOCRError(f"未找到 PaddleOCR Token：{config.paddleocr_api_key_env}")

    def submit_local_file(self, path: str | Path, *, page_ranges: str | None = None, batch_id: str | None = None) -> str:
        source = Path(path)
        if not source.exists() or not source.is_file():
            raise PaddleOCRError(f"PaddleOCR 本地文件不存在：{source}")
        safe_progress(self.progress, f"PaddleOCR submit local file: source={source.name}, model={self.config.paddleocr_model}, page_ranges={page_ranges or 'all'}")
        fields: dict[str, Any] = {
            "model": self.config.paddleocr_model,
            "optionalPayload": json.dumps(build_optional_payload(self.config), ensure_ascii=False),
        }
        if page_ranges:
            fields["pageRanges"] = page_ranges
        if batch_id:
            fields["batchId"] = batch_id
        response = self._request_multipart(self.job_url, fields=fields, file_path=source)
        return _job_id_from_response(response)

    def submit_url(self, url: str, *, page_ranges: str | None = None, batch_id: str | None = None) -> str:
        safe_progress(self.progress, f"PaddleOCR submit URL: source={_safe_url_label(url)}, model={self.config.paddleocr_model}, page_ranges={page_ranges or 'all'}")
        payload: dict[str, Any] = {
            "fileUrl": url,
            "model": self.config.paddleocr_model,
            "optionalPayload": build_optional_payload(self.config),
        }
        if page_ranges:
            payload["pageRanges"] = page_ranges
        if batch_id:
            payload["batchId"] = batch_id
        response = self._request_json(self.job_url, data=payload, method="POST")
        return _job_id_from_response(response)

    def wait_for_job(self, job_id: str, *, poll_interval: float = 5.0, timeout: float | None = None) -> PaddleOCRJobStatus:
        started = time.monotonic()
        while True:
            status = self.get_job_status(job_id)
            if status.state == "pending":
                safe_progress(self.progress, f"PaddleOCR job pending: job_id={job_id}")
            elif status.state == "running":
                detail = ""
                if status.total_pages is not None and status.extracted_pages is not None:
                    detail = f", pages={status.extracted_pages}/{status.total_pages}"
                safe_progress(self.progress, f"PaddleOCR job running: job_id={job_id}{detail}")
            elif status.state == "done":
                safe_progress(
                    self.progress,
                    f"PaddleOCR job done: job_id={job_id}, pages={status.extracted_pages or status.total_pages or 'unknown'}",
                )
                return status
            elif status.state == "failed":
                raise PaddleOCRError(f"PaddleOCR 任务失败：{status.error_msg or 'unknown error'}")
            else:
                safe_progress(self.progress, f"PaddleOCR job state: job_id={job_id}, state={status.state}")
            if timeout and time.monotonic() - started > timeout:
                raise PaddleOCRError(f"PaddleOCR 任务超时：{job_id}")
            time.sleep(max(0.5, poll_interval))

    def get_job_status(self, job_id: str) -> PaddleOCRJobStatus:
        response = self._request_json(f"{self.job_url}/{job_id}", method="GET")
        data = response.get("data") if isinstance(response.get("data"), dict) else {}
        progress = data.get("extractProgress") if isinstance(data.get("extractProgress"), dict) else {}
        return PaddleOCRJobStatus(
            job_id=str(data.get("jobId") or job_id),
            state=str(data.get("state") or "unknown"),
            trace_id=str(response.get("traceId") or "") or None,
            error_msg=str(data.get("errorMsg") or "") or None,
            result_url=data.get("resultUrl") if isinstance(data.get("resultUrl"), dict) else None,
            total_pages=_optional_int(progress.get("totalPages")),
            extracted_pages=_optional_int(progress.get("extractedPages")),
            raw=response,
        )

    def download_job_artifact(
        self,
        status: PaddleOCRJobStatus,
        artifact_dir: str | Path,
        *,
        source: str,
        page_ranges: str | None = None,
    ) -> Path:
        root = Path(artifact_dir)
        root.mkdir(parents=True, exist_ok=True)
        write_json(
            root / "job.json",
            {
                "provider": "paddleocr",
                "source": source,
                "page_ranges": page_ranges,
                "model": self.config.paddleocr_model,
                "api_key_env": self.config.paddleocr_api_key_env,
                "job_id": status.job_id,
                "trace_id": status.trace_id,
                "status": status.raw,
            },
        )
        result_url = status.result_url or {}
        json_url = result_url.get("jsonUrl") or result_url.get("jsonlUrl")
        markdown_url = result_url.get("markdownUrl")
        if json_url:
            safe_progress(self.progress, f"PaddleOCR downloading JSONL result: job_id={status.job_id}")
            text = self._download_text(json_url)
            write_text_atomic(root / "result.jsonl", text if text.endswith("\n") else text + "\n")
        if markdown_url:
            safe_progress(self.progress, f"PaddleOCR downloading Markdown result: job_id={status.job_id}")
            write_text_atomic(root / "result.md", self._download_text(markdown_url))
        self._download_result_images(root)
        return root

    def _download_result_images(self, root: Path) -> None:
        jsonl = root / "result.jsonl"
        if not jsonl.exists():
            return
        image_manifest: dict[str, str] = {}
        images_dir = root / "images"
        for line_index, line in enumerate(jsonl.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            for page_index, page_result in enumerate(_iter_layout_results(payload), start=1):
                markdown = page_result.get("markdown") if isinstance(page_result.get("markdown"), dict) else {}
                images = markdown.get("images") if isinstance(markdown.get("images"), dict) else {}
                for image_key, image_value in images.items():
                    local = self._save_image_value(images_dir, f"line_{line_index:03d}/markdown/{image_key}", image_value)
                    if local:
                        image_manifest[str(image_key)] = local.relative_to(root).as_posix()
                output_images = page_result.get("outputImages") if isinstance(page_result.get("outputImages"), dict) else {}
                for image_key, image_value in output_images.items():
                    local = self._save_image_value(images_dir, f"line_{line_index:03d}/output/{image_key}_{page_index}.jpg", image_value)
                    if local:
                        image_manifest[str(image_key)] = local.relative_to(root).as_posix()
                input_image = page_result.get("inputImage")
                if isinstance(input_image, str) and input_image.strip():
                    local = self._save_image_value(images_dir, f"line_{line_index:03d}/input/inputImage_{page_index}.jpg", input_image)
                    if local:
                        image_manifest.setdefault("inputImage", local.relative_to(root).as_posix())
        if image_manifest:
            write_json(root / "image_manifest.json", image_manifest)

    def _save_image_value(self, images_dir: Path, relative_name: str, value: Any) -> Path | None:
        if not isinstance(value, str) or not value.strip():
            return None
        target = images_dir / relative_name.lstrip("/\\")
        if target.suffix == "":
            target = target.with_suffix(".jpg")
        target.parent.mkdir(parents=True, exist_ok=True)
        raw = value.strip()
        try:
            if raw.startswith("http://") or raw.startswith("https://"):
                data = self._download_bytes(raw)
            else:
                data = _decode_image_data(raw)
            target.write_bytes(data)
            return target
        except Exception as exc:
            safe_progress(self.progress, f"PaddleOCR image download skipped: target={target.name}, error={exc}")
            return None

    def _download_text(self, url: str) -> str:
        return self._download_bytes(url).decode("utf-8", errors="replace")

    def _download_bytes(self, url: str) -> bytes:
        req = urllib.request.Request(url, headers={"User-Agent": "DocPage2MD-PaddleOCR/1.0"})
        with self._open_with_retry(req, timeout=60) as response:
            return response.read()

    def _request_json(self, url: str, *, data: dict[str, Any] | None = None, method: str = "GET") -> dict[str, Any]:
        body = None if data is None else json.dumps(data, ensure_ascii=False).encode("utf-8")
        headers = {"Authorization": f"bearer {self.api_key}"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        return self._send_json_request(req)

    def _request_multipart(self, url: str, *, fields: dict[str, Any], file_path: Path) -> dict[str, Any]:
        boundary = f"----DocPage2MD{uuid.uuid4().hex}"
        body = _multipart_body(fields, file_path, boundary)
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Authorization": f"bearer {self.api_key}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
            method="POST",
        )
        return self._send_json_request(req)

    def _send_json_request(self, req: urllib.request.Request) -> dict[str, Any]:
        raw = ""
        try:
            with self._open_with_retry(req, timeout=60) as response:
                raw = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise PaddleOCRError(f"PaddleOCR HTTP {exc.code}: {_safe_error_text(body)}") from exc
        except urllib.error.URLError as exc:
            raise PaddleOCRError(f"PaddleOCR 网络错误：{exc.reason}") from exc
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise PaddleOCRError(f"PaddleOCR 返回不是 JSON：{_safe_error_text(raw)}") from exc
        code = payload.get("code")
        if code not in (0, "0", None):
            raise PaddleOCRError(f"PaddleOCR API 错误 {code}: {_safe_error_text(payload.get('msg') or payload.get('errorMsg') or payload)}")
        return payload

    def _open_with_retry(self, req: urllib.request.Request, *, timeout: int):
        max_retries = max(0, int(self.config.api_max_retries or 0))
        base_sleep = max(0.0, float(self.config.api_retry_base_sleep or 0.0))
        max_sleep = max(0.0, float(self.config.api_retry_max_sleep or 0.0))
        attempt = 0
        while True:
            try:
                return urllib.request.urlopen(req, timeout=timeout)
            except urllib.error.HTTPError as exc:
                if exc.code not in PADDLEOCR_RETRY_HTTP_STATUS or attempt >= max_retries:
                    raise
                safe_progress(
                    self.progress,
                    f"PaddleOCR request retry: status={exc.code}, attempt={attempt + 1}/{max_retries}, url={_safe_url_label(req.full_url)}",
                )
                _sleep_for_retry(attempt, base_sleep, max_sleep)
                attempt += 1
            except urllib.error.URLError:
                if attempt >= max_retries:
                    raise
                safe_progress(
                    self.progress,
                    f"PaddleOCR request retry: status=network, attempt={attempt + 1}/{max_retries}, url={_safe_url_label(req.full_url)}",
                )
                _sleep_for_retry(attempt, base_sleep, max_sleep)
                attempt += 1


def build_optional_payload(config: AppConfig) -> dict[str, Any]:
    return {
        "useDocOrientationClassify": bool(config.paddleocr_doc_orientation),
        "useDocUnwarping": bool(config.paddleocr_doc_unwarping),
        "useChartRecognition": bool(config.paddleocr_chart_recognition),
        "useLayoutDetection": bool(config.paddleocr_layout_detection),
        "useFormulaRecognition": bool(config.paddleocr_formula_recognition),
        "useTableRecognition": bool(config.paddleocr_table_recognition),
        "visualize": bool(config.paddleocr_visualize),
    }


def _job_id_from_response(response: dict[str, Any]) -> str:
    data = response.get("data") if isinstance(response.get("data"), dict) else {}
    job_id = str(data.get("jobId") or "").strip()
    if not job_id:
        raise PaddleOCRError(f"PaddleOCR 未返回 jobId：{response}")
    return job_id


def _multipart_body(fields: dict[str, Any], file_path: Path, boundary: str) -> bytes:
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"),
                str(value).encode("utf-8"),
                b"\r\n",
            ]
        )
    mime = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
    chunks.extend(
        [
            f"--{boundary}\r\n".encode("utf-8"),
            f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'.encode("utf-8"),
            f"Content-Type: {mime}\r\n\r\n".encode("utf-8"),
            file_path.read_bytes(),
            b"\r\n",
            f"--{boundary}--\r\n".encode("utf-8"),
        ]
    )
    return b"".join(chunks)


def _decode_image_data(value: str) -> bytes:
    raw = value.strip()
    if raw.startswith("data:"):
        raw = raw.split(",", 1)[1]
    return base64.b64decode(raw)


def _iter_layout_results(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        if isinstance(payload.get("layoutParsingResults"), list):
            return [item for item in payload["layoutParsingResults"] if isinstance(item, dict)]
        if isinstance(payload.get("result"), dict):
            return _iter_layout_results(payload["result"])
        if isinstance(payload.get("data"), dict):
            return _iter_layout_results(payload["data"])
        if "prunedResult" in payload or "markdown" in payload:
            return [payload]
    if isinstance(payload, list):
        out: list[dict[str, Any]] = []
        for item in payload:
            out.extend(_iter_layout_results(item))
        return out
    return []


def _optional_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_error_text(value: Any) -> str:
    text = str(value or "").replace("\r", " ").replace("\n", " ")
    return text[:500]


def _safe_url_label(url: str) -> str:
    parsed = urllib.parse.urlsplit(str(url))
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))


def _sleep_for_retry(attempt: int, base_sleep: float, max_sleep: float) -> None:
    if base_sleep <= 0:
        return
    delay = base_sleep * (2 ** attempt)
    if max_sleep > 0:
        delay = min(delay, max_sleep)
    delay *= 1.0 + random.random() * 0.1
    time.sleep(delay)
