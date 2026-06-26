from pathlib import Path

from docpage2md_app.config import AppConfig
from docpage2md_app.files import read_json
from docpage2md_app.mineru_pipeline import process_mineru_artifact_task


FIXTURE = Path("tests/fixtures/mineru_public/minimal_artifact")


def test_mineru_artifact_pipeline_writes_markdown_assets_ir_and_report(tmp_path):
    config = AppConfig(output_folder=str(tmp_path), engine_mode="mineru_only", output_retention="debug")

    result = process_mineru_artifact_task(FIXTURE, config, doc_name="MinerUFixture", engine_mode="mineru_only")

    output_dir = Path(result["output_dir"])
    assert result["page_count"] == 1
    assert (output_dir / "Slide_01.md").exists()
    assert (output_dir / "MinerUFixture_FULL.md").exists()
    assert (output_dir / "run_report.json").exists()
    assert (output_dir / "ir" / "document_ir.json").exists()
    assert (output_dir / "ir" / "page_001_ir.json").exists()
    assert (output_dir / "mineru_raw" / "full.md").exists()
    assert list((output_dir / "assets" / "crops").iterdir())

    slide_1 = (output_dir / "Slide_01.md").read_text(encoding="utf-8")
    assert "Sample Document" in slide_1
    assert "E = mc^2" in slide_1
    assert "assets/crops/" in slide_1
    assert "<summary>图示识别内容</summary>" in slide_1
    assert "sample_fig.svg" in slide_1
    assert "> [!WARNING]" not in slide_1
    assert "OCR 正文覆盖率" not in slide_1

    report = read_json(output_dir / "run_report.json")
    assert report["engine_mode"] == "mineru_only"
    assert report["mineru"]["model_version"] == "vlm"
    assert report["summary"]["pages_total"] == 1
    assert report["summary"]["markdown_pages"] == 1
    assert "mineru_artifact" in report["summary"]["markdown_source_counts"]
    assert report["summary"]["content_inventory"]["source_block_count"] > 0
    assert report["summary"]["content_inventory"]["unaccounted_count"] == 0
    assert report["pages"][0]["content_inventory"]["summary"]["missing_visual_evidence_count"] == 0
    assert report["pages"][0]["brain"]["status"] == "skipped"
    assert report["pages"][0]["brain"]["ops_requested"] == 0
    assert report["pages"][0]["brain"]["usage"] is None
    assert isinstance(report["pages"][0]["validation"], dict)
    assert isinstance(report["pages"][0]["findings"]["initial"], list)
    assert "findings" in report["summary"]
    assert "suspects" not in report["summary"]
    assert "suspects" not in report["pages"][0]
    assert report["output_retention"]["mode"] == "debug"


def test_mineru_artifact_pipeline_slim_skips_raw_and_ir_but_keeps_markdown_assets(tmp_path):
    config = AppConfig(output_folder=str(tmp_path), engine_mode="mineru_only")

    result = process_mineru_artifact_task(FIXTURE, config, doc_name="MinerUSlim", engine_mode="mineru_only")

    output_dir = Path(result["output_dir"])
    assert (output_dir / "Slide_01.md").exists()
    assert (output_dir / "MinerUSlim_FULL.md").exists()
    assert (output_dir / "run_report.json").exists()
    assert not (output_dir / "ir").exists()
    assert not (output_dir / "mineru_raw").exists()
    assert list((output_dir / "assets" / "crops").iterdir())
    report = read_json(output_dir / "run_report.json")
    assert report["output_retention"]["mode"] == "slim"


def test_mineru_hybrid_pipeline_records_enrichment_without_markdown_noise(tmp_path):
    config = AppConfig(output_folder=str(tmp_path), engine_mode="hybrid")

    def vision_backend(page_ir, block, image_path, config):
        if block.get("type") in {"figure_note", "image_ref"}:
            return {
                "success": True,
                "description": "图示 crop 已由视觉模型复核，保留原图作为证据。",
                "usage": {"prompt_tokens": 1, "completion_tokens": 2},
                "request_id": "vision-mock",
            }
        return {"success": True, "content": block.get("text") or "", "usage": {"prompt_tokens": 1, "completion_tokens": 1}}

    def brain_backend(page_ir, context_pages, config):
        return {
            "success": True,
            "ops": [],
            "usage": {"prompt_tokens": 3, "completion_tokens": 1},
            "request_id": "brain-mock",
            "reasoning": "hidden reasoning",
        }

    result = process_mineru_artifact_task(
        FIXTURE,
        config,
        doc_name="HybridFixture",
        engine_mode="hybrid",
        vision_backend=vision_backend,
        brain_backend=brain_backend,
    )

    output_dir = Path(result["output_dir"])
    slide_1 = (output_dir / "Slide_01.md").read_text(encoding="utf-8")
    report = read_json(output_dir / "run_report.json")

    assert report["engine_mode"] == "hybrid"
    assert report["hybrid_enrichment"]["enabled"] is True
    assert report["summary"]["markdown_source_counts"]["hybrid_enriched_ir"] == 1
    assert report["summary"]["content_inventory"]["unaccounted_count"] == 0
    assert report["cost"]["actual_tokens"]["total_tokens"] > 0
    assert report["pages"][0]["vision"]["status"] in {"ok", "partial", "skipped"}
    assert report["pages"][0]["brain"]["status"] == "ok"
    assert "<summary>图示识别内容</summary>" in slide_1
    assert "hidden reasoning" not in slide_1
    assert "hidden reasoning" not in str(report)
