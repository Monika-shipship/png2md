import json
import urllib.error

import pytest

from docpage2md_app.config import AppConfig
from docpage2md_app.paddleocr_client import PaddleOCRClient, PaddleOCRError, build_optional_payload


def test_paddleocr_client_builds_optional_payload():
    config = AppConfig(
        paddleocr_doc_orientation=True,
        paddleocr_doc_unwarping=True,
        paddleocr_chart_recognition=True,
        paddleocr_layout_detection=False,
        paddleocr_formula_recognition=False,
        paddleocr_table_recognition=False,
        paddleocr_visualize=False,
    )

    payload = build_optional_payload(config)

    assert payload == {
        "useDocOrientationClassify": True,
        "useDocUnwarping": True,
        "useChartRecognition": True,
        "useLayoutDetection": False,
        "useFormulaRecognition": False,
        "useTableRecognition": False,
        "visualize": False,
    }


def test_paddleocr_client_submit_poll_download(monkeypatch, tmp_path):
    monkeypatch.setenv("PADDLEOCR_API_TOKEN", "token-for-test")
    calls = []

    def fake_urlopen(req, timeout=60):
        calls.append((req.full_url, req.get_method()))
        if req.full_url.endswith("/api/v2/ocr/jobs") and req.get_method() == "POST":
            return _Response({"code": 0, "data": {"jobId": "job-1"}})
        if req.full_url.endswith("/api/v2/ocr/jobs/job-1"):
            return _Response(
                {
                    "code": 0,
                    "traceId": "trace-1",
                    "data": {
                        "jobId": "job-1",
                        "state": "done",
                        "extractProgress": {"totalPages": 1, "extractedPages": 1},
                        "resultUrl": {"jsonlUrl": "https://download.test/result.jsonl", "markdownUrl": "https://download.test/result.md"},
                    },
                }
            )
        if req.full_url == "https://download.test/result.jsonl":
            payload = {"layoutParsingResults": [{"markdown": {"text": "hello", "images": {}}}]}
            return _BytesResponse((json.dumps(payload) + "\n").encode("utf-8"))
        if req.full_url == "https://download.test/result.md":
            return _BytesResponse(b"hello\n")
        raise AssertionError(req.full_url)

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = PaddleOCRClient(AppConfig())

    job_id = client.submit_url("https://example.com/a.pdf")
    status = client.wait_for_job(job_id, poll_interval=0.01, timeout=1)
    artifact = client.download_job_artifact(status, tmp_path / "artifact", source="https://example.com/a.pdf")

    assert job_id == "job-1"
    assert status.total_pages == 1
    assert (artifact / "result.jsonl").exists()
    assert (artifact / "result.md").read_text(encoding="utf-8") == "hello\n"
    assert any(url.endswith("/api/v2/ocr/jobs/job-1") for url, _method in calls)


def test_paddleocr_client_retries_429_503_504_and_download_failures(monkeypatch, tmp_path):
    monkeypatch.setenv("PADDLEOCR_API_TOKEN", "token-for-test")
    monkeypatch.setattr("time.sleep", lambda _seconds: None)
    monkeypatch.setattr("random.random", lambda: 0.0)
    state = {"submit": 0, "poll": 0, "download": 0}

    def fake_urlopen(req, timeout=60):
        if req.full_url.endswith("/api/v2/ocr/jobs") and req.get_method() == "POST":
            state["submit"] += 1
            if state["submit"] == 1:
                raise _http_error(req.full_url, 429, "too many")
            return _Response({"code": 0, "data": {"jobId": "job-retry"}})
        if req.full_url.endswith("/api/v2/ocr/jobs/job-retry"):
            state["poll"] += 1
            if state["poll"] == 1:
                raise _http_error(req.full_url, 503, "busy")
            if state["poll"] == 2:
                return _Response(
                    {
                        "code": 0,
                        "data": {
                            "jobId": "job-retry",
                            "state": "running",
                            "extractProgress": {"totalPages": 2, "extractedPages": 1},
                        },
                    }
                )
            return _Response(
                {
                    "code": 0,
                    "data": {
                        "jobId": "job-retry",
                        "state": "done",
                        "extractProgress": {"totalPages": 2, "extractedPages": 2},
                        "resultUrl": {"jsonlUrl": "https://download.test/result.jsonl"},
                    },
                }
            )
        if req.full_url == "https://download.test/result.jsonl":
            state["download"] += 1
            if state["download"] == 1:
                raise _http_error(req.full_url, 504, "timeout")
            payload = {"layoutParsingResults": [{"markdown": {"text": "ok", "images": {}}}]}
            return _BytesResponse((json.dumps(payload) + "\n").encode("utf-8"))
        raise AssertionError(req.full_url)

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    config = AppConfig(api_max_retries=2, api_retry_base_sleep=0, api_retry_max_sleep=0)
    client = PaddleOCRClient(config)

    job_id = client.submit_url("https://example.com/a.pdf")
    status = client.wait_for_job(job_id, poll_interval=0.01, timeout=1)
    artifact = client.download_job_artifact(status, tmp_path / "artifact", source="https://example.com/a.pdf")

    assert job_id == "job-retry"
    assert status.extracted_pages == 2
    assert state == {"submit": 2, "poll": 3, "download": 2}
    assert (artifact / "result.jsonl").exists()


def test_paddleocr_client_requires_token(monkeypatch):
    monkeypatch.delenv("PADDLEOCR_API_TOKEN", raising=False)
    monkeypatch.setattr("docpage2md_app.secrets.get_local_secret", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("docpage2md_app.secrets._get_windows_user_env", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("docpage2md_app.secrets.get_windows_credential", lambda *_args, **_kwargs: None)

    with pytest.raises(PaddleOCRError, match="PaddleOCR Token"):
        PaddleOCRClient(AppConfig())


class _Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class _BytesResponse:
    def __init__(self, data):
        self.data = data

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.data


def _http_error(url: str, code: int, body: str) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(url, code, "err", hdrs={}, fp=_ErrorBody(body))


class _ErrorBody:
    def __init__(self, body: str):
        self.body = body.encode("utf-8")

    def read(self):
        return self.body

    def close(self):
        pass
