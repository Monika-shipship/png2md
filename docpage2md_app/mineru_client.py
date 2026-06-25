import json
import http.client
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import AppConfig
from .env import get_env_value
from .run_logger import ProgressCallback, safe_progress


class MinerUError(RuntimeError):
    pass


class MinerUApiError(MinerUError):
    def __init__(self, message: str, *, code: int | None = None, trace_id: str | None = None):
        super().__init__(message)
        self.code = code
        self.trace_id = trace_id


class MinerUProtocolError(MinerUError):
    pass


class MinerUTimeoutError(MinerUError):
    pass


@dataclass(frozen=True)
class MinerUTaskResult:
    task_id: str | None
    batch_id: str | None
    state: str
    full_zip_url: str | None
    raw: dict[str, Any]
    file_name: str | None = None
    data_id: str | None = None


class MinerUClient:
    def __init__(self, config: AppConfig, *, token: str | None = None, progress: ProgressCallback | None = None):
        self.config = config
        self.base_url = config.mineru_base_url.rstrip("/")
        self.token = token if token is not None else get_env_value(config.mineru_api_token_env)
        self.progress = progress
        if not self.token:
            raise MinerUApiError(
                f"Missing MinerU token. Set environment variable {config.mineru_api_token_env}.",
                code=None,
            )
        self._log(f"MinerU client ready: base_url={self.base_url}, token_env={config.mineru_api_token_env}")

    def submit_url(
        self,
        file_url: str,
        *,
        page_ranges: str | None = None,
        data_id: str | None = None,
        no_cache: bool = False,
    ) -> dict[str, Any]:
        payload = self._default_payload(page_ranges=page_ranges, data_id=data_id)
        payload.update({"url": file_url, "no_cache": bool(no_cache)})
        self._log(
            "MinerU submit URL task: "
            f"model={payload.get('model_version')}, page_ranges={payload.get('page_ranges') or 'all'}"
        )
        return self._post_json("/api/v4/extract/task", payload)

    def request_upload_urls(
        self,
        files: list[Path],
        *,
        page_ranges: str | None = None,
    ) -> dict[str, Any]:
        if not files:
            raise ValueError("At least one local file is required for MinerU upload.")
        if len(files) > 50:
            raise ValueError("MinerU local batch upload supports at most 50 files per request.")
        self._log(
            f"MinerU request upload URLs: files={len(files)}, "
            f"page_ranges={(page_ranges or self.config.mineru_page_ranges) or 'all'}, "
            f"model={self.config.mineru_model_version}"
        )
        payload = self._batch_payload(page_ranges=page_ranges)
        effective_page_ranges = page_ranges or self.config.mineru_page_ranges
        payload["files"] = []
        for path in files:
            file_item: dict[str, Any] = {
                "name": path.name,
                "data_id": _safe_data_id(path.stem),
            }
            if self.config.mineru_model_version != "MinerU-HTML":
                file_item["is_ocr"] = self.config.mineru_is_ocr
            if effective_page_ranges:
                file_item["page_ranges"] = effective_page_ranges
            payload["files"].append(file_item)
        return self._post_json("/api/v4/file-urls/batch", payload)

    def upload_file(self, path: str | Path, upload_url: str) -> None:
        file_path = Path(path)
        if not file_path.exists() or not file_path.is_file():
            raise FileNotFoundError(file_path)
        try:
            self._log(f"Uploading file to MinerU signed URL: name={file_path.name}, bytes={file_path.stat().st_size}")
            _put_file_to_signed_url(file_path, upload_url)
            self._log(f"Upload complete: name={file_path.name}")
        except MinerUApiError:
            raise
        except OSError as exc:
            raise MinerUApiError(f"MinerU upload failed: {_safe_error(exc)}") from exc

    def submit_local_file(self, path: str | Path, *, page_ranges: str | None = None) -> str:
        return self.submit_local_files([Path(path)], page_ranges=page_ranges)

    def submit_local_files(self, files: list[str | Path], *, page_ranges: str | None = None) -> str:
        file_paths = [Path(path) for path in files]
        for file_path in file_paths:
            if not file_path.exists() or not file_path.is_file():
                raise FileNotFoundError(file_path)
        response = self.request_upload_urls(file_paths, page_ranges=page_ranges)
        data = _data(response)
        batch_id = data.get("batch_id")
        urls = data.get("file_urls") or []
        if not batch_id or not urls:
            raise MinerUProtocolError("MinerU upload-url response missed batch_id or file_urls.")
        if len(urls) != len(file_paths):
            raise MinerUProtocolError("MinerU upload-url response count did not match requested files.")
        for file_path, upload_url in zip(file_paths, urls):
            self.upload_file(file_path, upload_url)
        self._log(f"MinerU local upload submitted: batch_id={batch_id}, files={len(file_paths)}")
        return str(batch_id)

    def query_task(self, task_id: str) -> MinerUTaskResult:
        self._log(f"Query MinerU task: task_id={task_id}")
        response = self._get_json(f"/api/v4/extract/task/{task_id}")
        data = _data(response)
        return MinerUTaskResult(
            task_id=str(data.get("task_id") or task_id),
            batch_id=None,
            state=str(data.get("state") or ""),
            full_zip_url=data.get("full_zip_url"),
            raw=response,
            file_name=data.get("file_name"),
            data_id=data.get("data_id"),
        )

    def query_batch(self, batch_id: str) -> MinerUTaskResult:
        results = self.query_batch_results(batch_id)
        if not results:
            raise MinerUProtocolError("MinerU batch response missed extract_result.")
        return results[0]

    def query_batch_results(self, batch_id: str) -> list[MinerUTaskResult]:
        self._log(f"Query MinerU batch: batch_id={batch_id}")
        response = self._get_json(f"/api/v4/extract-results/batch/{batch_id}")
        data = _data(response)
        results = data.get("extract_result") or []
        parsed: list[MinerUTaskResult] = []
        for item in results:
            if not isinstance(item, dict):
                continue
            parsed.append(
                MinerUTaskResult(
                    task_id=str(item.get("task_id") or "") or None,
                    batch_id=str(data.get("batch_id") or batch_id),
                    state=str(item.get("state") or ""),
                    full_zip_url=item.get("full_zip_url"),
                    raw={"code": response.get("code"), "msg": response.get("msg"), "trace_id": response.get("trace_id"), "data": item},
                    file_name=item.get("file_name"),
                    data_id=item.get("data_id"),
                )
            )
        return parsed

    def wait_for_task(self, task_id: str, *, timeout: int = 900, interval: float = 3.0) -> MinerUTaskResult:
        return self._wait(lambda: self.query_task(task_id), timeout=timeout, interval=interval)

    def wait_for_batch(self, batch_id: str, *, timeout: int = 900, interval: float = 3.0) -> MinerUTaskResult:
        return self._wait(lambda: self.query_batch(batch_id), timeout=timeout, interval=interval)

    def wait_for_batch_results(
        self,
        batch_id: str,
        *,
        expected_count: int | None = None,
        timeout: int = 900,
        interval: float = 3.0,
    ) -> list[MinerUTaskResult]:
        started = time.monotonic()
        poll_no = 0
        last_results: list[MinerUTaskResult] = []
        while time.monotonic() - started <= timeout:
            results = self.query_batch_results(batch_id)
            last_results = results
            poll_no += 1
            self._log_batch_poll(batch_id, poll_no, results)
            if expected_count is not None and len(results) < expected_count:
                time.sleep(interval)
                continue
            failed = [result for result in results if result.state == "failed"]
            if failed:
                result = failed[0]
                message = _result_error_message(result.raw)
                label = result.file_name or result.data_id or result.task_id or "unknown file"
                raise MinerUApiError(f"MinerU batch file failed ({label}): {message}")
            if results and all(result.state == "done" and result.full_zip_url for result in results):
                self._log(f"MinerU batch done: batch_id={batch_id}, files={len(results)}")
                return results
            time.sleep(interval)
        states = ", ".join(f"{result.file_name or result.task_id}:{result.state}" for result in last_results) or "unknown"
        raise MinerUTimeoutError(f"MinerU batch timed out after {timeout}s, last states={states}.")

    def download_zip(self, full_zip_url: str, dest: str | Path) -> Path:
        target = Path(dest)
        target.parent.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(full_zip_url, method="GET")
        try:
            self._log(f"Downloading MinerU result zip: dest={target}")
            with urllib.request.urlopen(request, timeout=900) as response:
                target.write_bytes(response.read())
            self._log(f"MinerU result zip saved: dest={target}, bytes={target.stat().st_size}")
        except urllib.error.HTTPError as exc:
            raise MinerUApiError(f"MinerU zip download failed with HTTP {exc.code}.", code=exc.code) from exc
        except urllib.error.URLError as exc:
            raise MinerUApiError(f"MinerU zip download failed: {_safe_error(exc)}") from exc
        return target

    def _wait(self, query_func, *, timeout: int, interval: float) -> MinerUTaskResult:
        started = time.monotonic()
        poll_no = 0
        last: MinerUTaskResult | None = None
        while time.monotonic() - started <= timeout:
            result = query_func()
            last = result
            poll_no += 1
            self._log(f"MinerU task poll #{poll_no}: task_id={result.task_id}, state={result.state}")
            if result.state == "done":
                if not result.full_zip_url:
                    raise MinerUProtocolError("MinerU task finished without full_zip_url.")
                self._log(f"MinerU task done: task_id={result.task_id}")
                return result
            if result.state == "failed":
                message = _result_error_message(result.raw)
                raise MinerUApiError(f"MinerU task failed: {message}")
            time.sleep(interval)
        state = last.state if last else "unknown"
        raise MinerUTimeoutError(f"MinerU task timed out after {timeout}s, last state={state}.")

    def _default_payload(self, *, page_ranges: str | None = None, data_id: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model_version": self.config.mineru_model_version,
        }
        if self.config.mineru_model_version != "MinerU-HTML":
            payload.update(
                {
                    "enable_formula": self.config.mineru_enable_formula,
                    "enable_table": self.config.mineru_enable_table,
                    "language": self.config.mineru_language,
                    "is_ocr": self.config.mineru_is_ocr,
                }
            )
        page_ranges = page_ranges or self.config.mineru_page_ranges
        if page_ranges:
            payload["page_ranges"] = page_ranges
        if data_id:
            payload["data_id"] = data_id
        return payload

    def _batch_payload(self, *, page_ranges: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model_version": self.config.mineru_model_version,
            "files": [],
        }
        if self.config.mineru_model_version != "MinerU-HTML":
            payload.update(
                {
                    "enable_formula": self.config.mineru_enable_formula,
                    "enable_table": self.config.mineru_enable_table,
                    "language": self.config.mineru_language,
                }
            )
        # Filled by request_upload_urls so Path normalization is centralized there.
        return payload

    def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request_json(path, method="POST", payload=payload)

    def _get_json(self, path: str) -> dict[str, Any]:
        return self._request_json(path, method="GET")

    def _request_json(self, path: str, *, method: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = json.dumps(payload or {}, ensure_ascii=False).encode("utf-8") if payload is not None else None
        started = time.monotonic()
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "Accept": "*/*",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=900) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise MinerUApiError(f"MinerU HTTP error {exc.code}.", code=exc.code) from exc
        except urllib.error.URLError as exc:
            raise MinerUApiError(f"MinerU request failed: {_safe_error(exc)}") from exc
        except json.JSONDecodeError as exc:
            raise MinerUProtocolError("MinerU returned non-JSON response.") from exc

        code = body.get("code")
        if code != 0:
            raise MinerUApiError(str(body.get("msg") or "MinerU API error."), code=code, trace_id=body.get("trace_id"))
        elapsed = time.monotonic() - started
        self._log(f"MinerU HTTP {method} {path} ok: elapsed={elapsed:.2f}s, trace_id={body.get('trace_id') or ''}")
        return body

    def _log(self, message: str) -> None:
        safe_progress(self.progress, message)

    def _log_batch_poll(self, batch_id: str, poll_no: int, results: list[MinerUTaskResult]) -> None:
        if not results:
            self._log(f"MinerU batch poll #{poll_no}: batch_id={batch_id}, no results yet")
            return
        states: dict[str, int] = {}
        labels = []
        for result in results:
            state = result.state or "unknown"
            states[state] = states.get(state, 0) + 1
            labels.append(f"{result.file_name or result.task_id or 'unknown'}={state}")
        state_text = ", ".join(f"{key}:{value}" for key, value in sorted(states.items()))
        detail = "; ".join(labels[:8])
        suffix = f"; {detail}" if detail else ""
        self._log(f"MinerU batch poll #{poll_no}: batch_id={batch_id}, states={state_text}{suffix}")


def _data(response: dict[str, Any]) -> dict[str, Any]:
    data = response.get("data")
    if not isinstance(data, dict):
        raise MinerUProtocolError("MinerU response missed data object.")
    return data


def _result_error_message(response: dict[str, Any]) -> str:
    data = response.get("data")
    if isinstance(data, dict):
        result = data.get("extract_result")
        if isinstance(result, list) and result and isinstance(result[0], dict):
            return str(result[0].get("err_msg") or result[0].get("err_code") or "unknown")
        return str(data.get("err_msg") or data.get("err_code") or "unknown")
    return "unknown"


def _safe_error(exc: BaseException) -> str:
    msg = str(exc)
    return msg[:240] + "..." if len(msg) > 240 else msg


def _put_file_to_signed_url(file_path: Path, upload_url: str) -> None:
    url = str(upload_url or "").strip()
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise MinerUApiError("MinerU upload failed: invalid upload URL.")

    connection_cls = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    target = urllib.parse.urlunsplit(("", "", parsed.path or "/", parsed.query, ""))
    connection = connection_cls(parsed.hostname, port, timeout=900)
    try:
        connection.putrequest("PUT", target, skip_accept_encoding=True)
        connection.putheader("Content-Length", str(file_path.stat().st_size))
        connection.endheaders()
        with file_path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                connection.send(chunk)
        response = connection.getresponse()
        body = response.read(500)
        if response.status not in (200, 201):
            detail = body.decode("utf-8", errors="replace").strip()
            suffix = f" ({detail[:160]})" if detail else ""
            raise MinerUApiError(f"MinerU upload failed with HTTP {response.status}.{suffix}", code=response.status)
    finally:
        connection.close()


def _safe_data_id(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "_.-" else "_" for ch in value).strip("_.-")
    return (cleaned or "document")[:128]
