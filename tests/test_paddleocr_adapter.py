import base64
import json
from pathlib import Path

from docpage2md_app.paddleocr_adapter import adapt_paddleocr_artifacts
from docpage2md_app.paddleocr_artifacts import discover_paddleocr_artifacts


_PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


def _write_minimal_artifact(root: Path) -> Path:
    images = root / "images"
    images.mkdir(parents=True)
    (images / "fig.png").write_bytes(_PNG_1X1)
    (root / "image_manifest.json").write_text(json.dumps({"fig": "images/fig.png"}), encoding="utf-8")
    payload = {
        "layoutParsingResults": [
            {
                "prunedResult": {
                    "parsing_res_list": [
                        {"block_label": "title", "block_content": "群论笔记", "score": 88},
                        {"block_label": "text", "block_content": "令 $G$ 为群。", "score": 0.61},
                        {"block_label": "display_formula", "block_content": "a^2+b^2=c^2", "confidence": "0.92"},
                        {"block_label": "image", "block_content": "图示 <img src=\"fig\" />"},
                    ]
                },
                "markdown": {"text": "# 群论笔记", "images": {"fig": "fig"}},
                "outputImages": {"layout_det_res": "fig"},
            }
        ]
    }
    (root / "result.jsonl").write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
    (root / "job.json").write_text(json.dumps({"source": "notes.pdf"}), encoding="utf-8")
    return root


def test_paddleocr_adapter_reads_layout_results(tmp_path):
    artifact = _write_minimal_artifact(tmp_path / "artifact")

    document_ir = adapt_paddleocr_artifacts(discover_paddleocr_artifacts(artifact), source_path="notes.pdf")

    assert document_ir["engine_mode"] == "paddleocr_only"
    assert len(document_ir["pages"]) == 1
    blocks = document_ir["pages"][0]["blocks"]
    assert [block["type"] for block in blocks] == ["heading", "paragraph", "formula_block", "figure_note"]
    assert [block["confidence"] for block in blocks] == [0.88, 0.61, 0.92, 0.62]
    assert [block["confidence_label"] for block in blocks] == ["high", "medium", "high", "medium"]
    assert all(isinstance(block["confidence"], float) for block in blocks)
    assert blocks[2]["latex"]
    assert document_ir["assets"][0]["source_path"].endswith("fig.png")


def test_paddleocr_adapter_markdown_fallback_uses_numeric_confidence(tmp_path):
    artifact = tmp_path / "artifact"
    artifact.mkdir()
    (artifact / "result.md").write_text("只有 Markdown 的 PaddleOCR 结果。", encoding="utf-8")

    document_ir = adapt_paddleocr_artifacts(discover_paddleocr_artifacts(artifact), source_path="notes.pdf")

    block = document_ir["pages"][0]["blocks"][0]
    assert block["type"] == "paragraph"
    assert block["confidence"] == 0.62
    assert block["confidence_label"] == "medium"


def test_paddleocr_adapter_skips_bad_jsonl_and_keeps_empty_page(tmp_path):
    artifact = tmp_path / "artifact"
    artifact.mkdir()
    payload = {"layoutParsingResults": [{"prunedResult": {"parsing_res_list": []}, "markdown": {"text": "", "images": {}}}]}
    (artifact / "result.jsonl").write_text("not-json\n" + json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")

    document_ir = adapt_paddleocr_artifacts(discover_paddleocr_artifacts(artifact), source_path="blank.pdf")

    assert len(document_ir["pages"]) == 1
    assert document_ir["pages"][0]["blocks"] == []
    assert document_ir["pages"][0]["raw_text"] == ""
