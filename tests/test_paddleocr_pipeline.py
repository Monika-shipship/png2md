import base64
import json
from pathlib import Path

from docpage2md_app.config import AppConfig
from docpage2md_app import cli
from docpage2md_app.input_inspection import build_page_chunks
from docpage2md_app.paddleocr_pipeline import process_paddleocr_artifact_task


_PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


def _artifact(root: Path, text: str = "群论笔记") -> Path:
    images = root / "images"
    images.mkdir(parents=True)
    (images / "fig.png").write_bytes(_PNG_1X1)
    (root / "image_manifest.json").write_text(json.dumps({"fig": "images/fig.png"}), encoding="utf-8")
    payload = {
        "layoutParsingResults": [
            {
                "prunedResult": {
                    "parsing_res_list": [
                        {"block_label": "title", "block_content": text},
                        {"block_label": "text", "block_content": "令 $G$ 为群。"},
                    ]
                },
                "markdown": {"text": text, "images": {"fig": "fig"}},
            }
        ]
    }
    (root / "result.jsonl").write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
    (root / "job.json").write_text(json.dumps({"source": "notes.pdf"}), encoding="utf-8")
    return root


def test_paddleocr_pipeline_renders_artifact(tmp_path):
    artifact = _artifact(tmp_path / "artifact")
    config = AppConfig(output_folder=str(tmp_path / "out"), engine_mode="paddleocr_only")

    result = process_paddleocr_artifact_task(artifact, config, doc_name="notes")

    output = Path(result["output_dir"])
    assert (output / "Slide_01.md").exists()
    assert (output / "notes_FULL.md").exists()
    assert (output / "run_report.json").exists()
    assert (output / "ir" / "document_ir.json").exists()
    assert (output / "paddleocr_raw" / "result.jsonl").exists()
    report = json.loads((output / "run_report.json").read_text(encoding="utf-8"))
    assert report["engine_mode"] == "paddleocr_only"
    assert report["models"]["layout_engine"]["model"] == "PaddleOCR-VL-1.6"


def test_paddleocr_chunk_merge_renumbers_outputs(tmp_path):
    output_dir = tmp_path / "out" / "Deck"
    chunk_dir = tmp_path / "out" / "Deck__chunk_002"
    (chunk_dir / "assets").mkdir(parents=True)
    (chunk_dir / "assets" / "fig.png").write_bytes(b"png")
    (chunk_dir / "ir").mkdir()
    (chunk_dir / "ir" / "page_001_ir.json").write_text("{}", encoding="utf-8")
    (chunk_dir / "paddleocr_raw").mkdir()
    (chunk_dir / "paddleocr_raw" / "result.jsonl").write_text("{}", encoding="utf-8")
    (chunk_dir / "Slide_01.md").write_text("# Slide 1\n\n![图](assets/fig.png)\n", encoding="utf-8")
    (chunk_dir / "Slide_01.meta.json").write_text(json.dumps({"slide_no": 1, "status": "ok"}), encoding="utf-8")
    (chunk_dir / "run_report.json").write_text(
        json.dumps(
            {
                "doc_name": "Deck__chunk_002",
                "status": "ok",
                "models": {},
                "cost": {"estimated": None, "actual_tokens": None, "note": ""},
                "paddleocr": {},
                "pages": [{"slide_no": 1, "final": {"status": "ok", "included_in_full": True}, "validation": {"warnings": []}}],
            }
        ),
        encoding="utf-8",
    )
    chunks = build_page_chunks(251, chunk_size=100)

    cli._merge_paddleocr_chunk_outputs(
        output_dir,
        "Deck",
        [{"index": 2, "output_dir": str(chunk_dir)}],
        chunks,
        progress=None,
    )

    assert (output_dir / "Slide_101.md").exists()
    assert "assets/chunk_002/fig.png" in (output_dir / "Slide_101.md").read_text(encoding="utf-8")
    assert (output_dir / "paddleocr_raw" / "chunk_002" / "result.jsonl").exists()


def test_paddleocr_251_pages_split_to_three_chunks():
    chunks = build_page_chunks(251, chunk_size=100)

    assert [chunk.page_ranges for chunk in chunks] == ["1-100", "101-200", "201-251"]
