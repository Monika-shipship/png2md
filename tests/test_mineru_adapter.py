from collections import Counter
from pathlib import Path

from docpage2md_app.invariant import page_ir_contract_errors
from docpage2md_app.mineru_adapter import DOCUMENT_IR_SCHEMA_VERSION, load_mineru_document_ir
from docpage2md_app.mineru_artifacts import discover_mineru_artifacts, resolve_artifact_image


FIXTURE = Path("tests/fixtures/mineru_public/minimal_artifact")


def test_mineru_fixture_discovers_client_artifacts():
    artifacts = discover_mineru_artifacts(FIXTURE)

    assert artifacts.full_md and artifacts.full_md.name == "full.md"
    assert artifacts.layout_json and artifacts.layout_json.name == "layout.json"
    assert artifacts.block_list_json and artifacts.block_list_json.name == "block_list.json"
    assert artifacts.content_list_v2_json and artifacts.content_list_v2_json.name.endswith("_content_list_v2.json")
    assert artifacts.model_json and artifacts.model_json.name.endswith("_model.json")
    assert artifacts.images_dir and artifacts.images_dir.name == "images"
    assert resolve_artifact_image(artifacts, "/sample_fig.svg")


def test_mineru_fixture_adapts_to_page_ir_contract():
    document_ir = load_mineru_document_ir(FIXTURE, engine_mode="hybrid")

    assert document_ir["schema_version"] == DOCUMENT_IR_SCHEMA_VERSION
    assert document_ir["engine_mode"] == "hybrid"
    assert len(document_ir["pages"]) == 1

    block_counts = Counter()
    for page in document_ir["pages"]:
        assert page_ir_contract_errors(page, expected_slide_no=page["source_page"]) == []
        block_counts.update(block["type"] for block in page["blocks"])
        assert page["raw_text_sha256"]

    assert block_counts["heading"] == 1
    assert block_counts["paragraph"] == 1
    assert block_counts["formula_block"] == 1
    assert block_counts["figure_note"] == 1

    first_page = document_ir["pages"][0]
    assert first_page["blocks"][0]["type"] == "heading"
    assert "Sample Document" in first_page["blocks"][0]["text"]
    assert any(block.get("crop_ref", "").startswith("images/") for block in first_page["blocks"])
    figure_blocks = [block for block in first_page["blocks"] if block["type"] == "figure_note"]
    assert figure_blocks
    assert "sample_fig.svg" in figure_blocks[0]["crop_ref"]


def test_mineru_adapter_normalizes_unicode_math_in_text_blocks(tmp_path):
    artifact = tmp_path / "artifact"
    artifact.mkdir()
    write_json = artifact / "sample_content_list_v2.json"
    write_json.write_text(
        '[{"page_idx":0,"type":"paragraph","content":{"paragraph_content":[{"type":"text","content":"令 φ, θ, ω 满足 α+β=γ。"}]}}]',
        encoding="utf-8",
    )

    document_ir = load_mineru_document_ir(artifact, engine_mode="mineru_only")
    text = document_ir["pages"][0]["blocks"][0]["text"]

    assert "$\\phi, \\theta, \\omega$" in text
    assert "$\\alpha + \\beta = \\gamma$" in text
    assert "φ" not in text
    assert "θ" not in text
    assert "ω" not in text
