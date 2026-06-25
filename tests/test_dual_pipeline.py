import base64
import json
from pathlib import Path

from docpage2md_app.config import AppConfig
from docpage2md_app.dual_ir import merge_mineru_paddleocr_ir
from docpage2md_app.dual_pipeline import process_dual_artifact_task
from docpage2md_app.files import read_json
from docpage2md_app.input_inspection import build_page_chunks
from docpage2md_app.mineru_adapter import load_mineru_document_ir
from docpage2md_app.paddleocr_adapter import load_paddleocr_document_ir


MINERU_FIXTURE = Path("tests/fixtures/mineru_public/minimal_artifact")
_PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


def _paddle_artifact(root: Path) -> Path:
    images = root / "images"
    images.mkdir(parents=True)
    (images / "page.jpg").write_bytes(_PNG_1X1)
    (root / "image_manifest.json").write_text(json.dumps({"page": "images/page.jpg"}), encoding="utf-8")
    payload = {
        "layoutParsingResults": [
            {
                "prunedResult": {
                    "parsing_res_list": [
                        {"block_label": "title", "block_content": "Sample Document"},
                        {"block_label": "text", "block_content": "PaddleOCR says $E=mc^2$ and adds cross evidence."},
                    ]
                },
                "markdown": {"text": "Sample Document\n\nPaddleOCR says $E=mc^2$.", "images": {}},
                "inputImage": "page",
            }
        ],
        "dataInfo": {"numPages": 1, "type": "pdf"},
    }
    (root / "result.jsonl").write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
    (root / "job.json").write_text(json.dumps({"source": "sample.pdf"}), encoding="utf-8")
    return root


def test_dual_ir_merges_paddleocr_as_secondary_evidence(tmp_path):
    paddle = _paddle_artifact(tmp_path / "paddle")
    mineru_ir = load_mineru_document_ir(MINERU_FIXTURE, engine_mode="dual_hybrid")
    paddle_ir = load_paddleocr_document_ir(paddle, engine_mode="dual_hybrid")

    merged = merge_mineru_paddleocr_ir(mineru_ir, paddle_ir)

    page = merged["pages"][0]
    assert merged["engine_mode"] == "dual_hybrid"
    assert page["dual_evidence"]["mineru"]["available"] is True
    assert page["dual_evidence"]["paddleocr"]["available"] is True
    assert "[MinerU]" in page["raw_text"]
    assert "[PaddleOCR]" in page["raw_text"]
    assert page["blocks"][0]["evidence"]["dual_parser"]["secondary_available"] is True


def test_dual_pipeline_renders_and_records_both_raw_dirs(tmp_path):
    paddle = _paddle_artifact(tmp_path / "paddle")
    config = AppConfig(output_folder=str(tmp_path / "out"), engine_mode="dual_hybrid")

    result = process_dual_artifact_task(
        MINERU_FIXTURE,
        paddle,
        config,
        doc_name="dual_fixture",
        vision_backend=lambda page, block, image, config: {"success": True, "description": block.get("description") or block.get("text") or ""},
        brain_backend=lambda page, context, config: {"success": True, "ops": [], "usage": {"prompt_tokens": 1, "completion_tokens": 1}},
    )

    output = Path(result["output_dir"])
    assert (output / "Slide_01.md").exists()
    assert (output / "dual_fixture_FULL.md").exists()
    assert (output / "mineru_raw" / "full.md").exists()
    assert (output / "paddleocr_raw" / "result.jsonl").exists()
    report = read_json(output / "run_report.json")
    assert report["engine_mode"] == "dual_hybrid"
    assert report["dual_parser"]["strategy"] == "candidate_group_checked_ops"
    assert report["fusion"]["summary"]["candidate_groups"] >= 1
    assert report["hybrid_enrichment"]["enabled"] is True
    assert report["summary"]["markdown_source_counts"]["dual_hybrid_enriched_ir"] == 1
    assert (output / "ir" / "mineru_document_ir.json").exists()
    assert (output / "ir" / "paddleocr_document_ir.json").exists()
    assert (output / "ir" / "fused_document_ir.json").exists()
    document_ir = read_json(output / "ir" / "document_ir.json")
    assert document_ir["pages"][0]["dual_evidence"]["paddleocr"]["block_count"] == 2
    assert document_ir["pages"][0]["fusion"]["candidate_groups"]


def test_dual_page_limit_uses_paddleocr_chunk_size():
    chunks = build_page_chunks(251, chunk_size=100)

    assert [chunk.page_ranges for chunk in chunks] == ["1-100", "101-200", "201-251"]
