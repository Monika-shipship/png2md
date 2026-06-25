import pytest

from docpage2md_app.config import AppConfig
from docpage2md_app.mineru_client import MinerUApiError, MinerUClient


def test_mineru_client_requires_token_without_reading_repo_files():
    with pytest.raises(MinerUApiError) as exc:
        MinerUClient(AppConfig(), token="")

    assert "MINERU_API_TOKEN" in str(exc.value)


def test_mineru_precise_api_default_payload_uses_vlm_and_document_options():
    config = AppConfig(mineru_page_ranges="1-3")
    client = MinerUClient(config, token="test-token")

    payload = client._default_payload(page_ranges=None)

    assert payload == {
        "model_version": "vlm",
        "enable_formula": True,
        "enable_table": True,
        "language": "ch",
        "is_ocr": True,
        "page_ranges": "1-3",
    }


def test_mineru_precise_api_payload_uses_configured_document_options():
    config = AppConfig(
        mineru_model_version="pipeline",
        mineru_is_ocr=False,
        mineru_enable_formula=False,
        mineru_enable_table=True,
        mineru_language="en",
    )
    client = MinerUClient(config, token="test-token")

    payload = client._default_payload(page_ranges="2-4")

    assert payload == {
        "model_version": "pipeline",
        "enable_formula": False,
        "enable_table": True,
        "language": "en",
        "is_ocr": False,
        "page_ranges": "2-4",
    }


def test_mineru_html_payload_skips_pdf_options():
    client = MinerUClient(AppConfig(mineru_model_version="MinerU-HTML"), token="test-token")

    payload = client._default_payload()

    assert payload == {"model_version": "MinerU-HTML"}


def test_mineru_batch_upload_payload_uses_file_level_page_ranges(monkeypatch, tmp_path):
    first = tmp_path / "notes.pdf"
    second = tmp_path / "slides.pptx"
    first.write_bytes(b"pdf")
    second.write_bytes(b"ppt")
    client = MinerUClient(AppConfig(), token="test-token")
    captured = {}

    def fake_post(path, payload):
        captured["path"] = path
        captured["payload"] = payload
        return {"code": 0, "msg": "ok", "data": {"batch_id": "batch-1", "file_urls": ["u1", "u2"]}}

    monkeypatch.setattr(client, "_post_json", fake_post)

    response = client.request_upload_urls([first, second], page_ranges="1-5")

    assert response["data"]["batch_id"] == "batch-1"
    assert captured["path"] == "/api/v4/file-urls/batch"
    assert captured["payload"]["model_version"] == "vlm"
    assert captured["payload"]["enable_formula"] is True
    assert captured["payload"]["enable_table"] is True
    assert captured["payload"]["language"] == "ch"
    assert captured["payload"]["files"] == [
        {"name": "notes.pdf", "data_id": "notes", "is_ocr": True, "page_ranges": "1-5"},
        {"name": "slides.pptx", "data_id": "slides", "is_ocr": True, "page_ranges": "1-5"},
    ]


def test_mineru_batch_results_parse_all_files(monkeypatch):
    client = MinerUClient(AppConfig(), token="test-token")

    def fake_get(path):
        assert path == "/api/v4/extract-results/batch/batch-1"
        return {
            "code": 0,
            "msg": "ok",
            "trace_id": "trace",
            "data": {
                "batch_id": "batch-1",
                "extract_result": [
                    {"task_id": "task-a", "file_name": "a.pdf", "data_id": "a", "state": "done", "full_zip_url": "zip-a"},
                    {"task_id": "task-b", "file_name": "b.docx", "data_id": "b", "state": "done", "full_zip_url": "zip-b"},
                ],
            },
        }

    monkeypatch.setattr(client, "_get_json", fake_get)

    results = client.query_batch_results("batch-1")

    assert [result.file_name for result in results] == ["a.pdf", "b.docx"]
    assert [result.full_zip_url for result in results] == ["zip-a", "zip-b"]
    assert [result.task_id for result in results] == ["task-a", "task-b"]
