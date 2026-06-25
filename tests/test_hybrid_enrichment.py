import json
import threading
import time
from pathlib import Path

from docpage2md_app.artifacts import sha256_text
from docpage2md_app.config import AppConfig
from docpage2md_app import hybrid_enrichment
from docpage2md_app.hybrid_enrichment import _brain_ops_prompt, default_brain_backend, enrich_mineru_document_ir
from docpage2md_app.ir import PAGE_IR_SCHEMA_VERSION
from docpage2md_app.renderer import render_page_ir_to_markdown


def test_hybrid_enrichment_applies_crop_vision_and_checked_brain_ops(tmp_path):
    output_root = tmp_path / "HybridDoc"
    crop_dir = output_root / "assets" / "crops"
    crop_dir.mkdir(parents=True)
    (crop_dir / "figure.jpg").write_bytes(b"fake figure")
    (crop_dir / "formula.jpg").write_bytes(b"fake formula")

    document_ir = _document_ir(
        [
            _block("p0001-b001", "paragraph", "配分函教为 Z。", origin="vision_ocr"),
            _block("p0001-b002", "figure_note", "", crop_ref="assets/crops/figure.jpg", origin="vision_description"),
            _block(
                "p0001-b003",
                "formula_block",
                "\\begin{aligned}\nS &= k(\\ln Z+\\beta U) \\tag{5}\n\\end{aligned}",
                crop_ref="assets/crops/formula.jpg",
                origin="vision_formula",
            ),
        ]
    )

    def vision_backend(page_ir, block, image_path: Path | None, config):
        assert image_path and image_path.exists()
        if block["type"] == "figure_note":
            return {
                "success": True,
                "description": "手绘坐标图，横轴为 t，纵轴为 x，曲线随时间上升。",
                "figure_type": "coordinate_plot",
                "labels": ["t", "x"],
                "usage": {"prompt_tokens": 3, "completion_tokens": 5},
                "request_id": "vision-1",
            }
        return {
            "success": True,
            "latex": "\\begin{aligned}\nS &= k(\\ln Z+\\beta U) \\tag{5}\n\\end{aligned}",
            "usage": {"prompt_tokens": 2, "completion_tokens": 4},
        }

    def brain_backend(page_ir, context_pages, config):
        return {
            "success": True,
            "ops": [
                {
                    "op": "replace_text_span_checked",
                    "id": "p0001-b001",
                    "old_text": "配分函教",
                    "new_text": "配分函数",
                    "field": "text",
                    "reason": "上下文显示为配分函数。",
                }
            ],
            "usage": {"prompt_tokens": 11, "completion_tokens": 7},
            "request_id": "brain-1",
            "reasoning": "this private reasoning must not be persisted",
        }

    result = enrich_mineru_document_ir(
        document_ir,
        AppConfig(engine_mode="hybrid"),
        output_root=output_root,
        vision_backend=vision_backend,
        brain_backend=brain_backend,
    )

    page = result["document_ir"]["pages"][0]
    markdown = render_page_ir_to_markdown(page, 1)

    assert page["blocks"][0]["text"] == "配分函数为 Z。"
    assert page["blocks"][0]["origin"] == "brain_refine"
    assert page["blocks"][1]["figure"]["figure_type"] == "coordinate_plot"
    assert "横轴为 t" in markdown
    assert "\\tag{5}\n\\end{aligned}" not in markdown
    assert "\\end{aligned}\n\\tag{5}" in markdown
    assert result["pages"][1]["brain"]["ops_applied"] == 1
    assert result["pages"][1]["op_audit"][0]["op"] == "replace_text_span_checked"
    assert "private reasoning" not in json.dumps(result, ensure_ascii=False)


def test_default_brain_backend_retries_empty_or_invalid_json(monkeypatch):
    page = _document_ir([_block("p0001-b001", "paragraph", "正文。", origin="vision_ocr")])["pages"][0]
    calls = iter(
        [
            {"content": "not json", "reasoning": "hidden first reasoning"},
            {"content": '{"ops": [], "warnings": []}', "usage": {"prompt_tokens": 2, "completion_tokens": 1}},
        ]
    )

    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setattr(hybrid_enrichment, "_call_brain_model", lambda prompt, config: next(calls))

    result = default_brain_backend(page, [page], AppConfig(engine_mode="hybrid"))

    assert result["success"] is True
    assert result["retry_count"] == 1
    assert result["ops"] == []
    assert "hidden first reasoning" not in json.dumps(result, ensure_ascii=False)


def test_hybrid_enrichment_runs_vision_and_brain_in_parallel(tmp_path):
    output_root = tmp_path / "HybridDoc"
    crop_dir = output_root / "assets" / "crops"
    crop_dir.mkdir(parents=True)
    for index in range(1, 5):
        (crop_dir / f"formula-{index}.jpg").write_bytes(b"fake formula")

    document_ir = _document_ir_pages(
        [
            [_block("p0001-b001", "formula_block", "x_1", crop_ref="assets/crops/formula-1.jpg", origin="vision_formula")],
            [_block("p0002-b001", "formula_block", "x_2", crop_ref="assets/crops/formula-2.jpg", origin="vision_formula", source_page=2)],
            [_block("p0003-b001", "formula_block", "x_3", crop_ref="assets/crops/formula-3.jpg", origin="vision_formula", source_page=3)],
            [_block("p0004-b001", "formula_block", "x_4", crop_ref="assets/crops/formula-4.jpg", origin="vision_formula", source_page=4)],
        ]
    )
    vision_counter = _ConcurrencyCounter()
    brain_counter = _ConcurrencyCounter()

    def vision_backend(page_ir, block, image_path: Path | None, config):
        with vision_counter:
            time.sleep(0.02)
            return {"success": True, "latex": block["text"]}

    def brain_backend(page_ir, context_pages, config):
        assert len(context_pages) >= 3
        with brain_counter:
            time.sleep(0.02)
            return {"success": True, "ops": []}

    result = enrich_mineru_document_ir(
        document_ir,
        AppConfig(engine_mode="hybrid", vision_batch_workers=4, brain_batch_workers=4),
        output_root=output_root,
        vision_backend=vision_backend,
        brain_backend=brain_backend,
    )

    assert vision_counter.max_active > 1
    assert brain_counter.max_active > 1
    assert result["summary"]["pages"]["page_count"] == 4


def test_brain_prompt_keeps_target_detail_and_compresses_neighbors():
    long_neighbor = "邻页上下文" * 300
    long_target = "目标页正文" * 300
    document_ir = _document_ir_pages(
        [
            [_block("p0001-b001", "paragraph", long_neighbor, origin="vision_ocr")],
            [_block("p0002-b001", "paragraph", long_target, origin="vision_ocr", source_page=2)],
            [_block("p0003-b001", "paragraph", long_neighbor, origin="vision_ocr", source_page=3)],
        ]
    )

    prompt = _brain_ops_prompt(document_ir["pages"][1], document_ir["pages"])

    assert '"role": "target"' in prompt
    assert '"role": "neighbor"' in prompt
    assert long_target[:400] in prompt
    assert long_neighbor not in prompt


def _document_ir(blocks):
    return _document_ir_pages([blocks])


def _document_ir_pages(pages_blocks):
    pages = []
    for page_index, blocks in enumerate(pages_blocks, start=1):
        raw_text = "\n\n".join(block.get("text") or block.get("description") or "" for block in blocks)
        for block in blocks:
            block["source_page"] = page_index
        pages.append(
            {
                "schema_version": PAGE_IR_SCHEMA_VERSION,
                "source_page": page_index,
                "page_image_ref": None,
                "raw_text": raw_text,
                "raw_text_sha256": sha256_text(raw_text),
                "blocks": blocks,
                "mineru": {"page_idx": page_index - 1, "page_size": [100, 100], "artifact_refs": {}},
            }
        )
    return {
        "schema_version": "docpage2md-docir-v1",
        "engine_mode": "hybrid",
        "source": {"input_path": "notes.pdf", "input_type": "pdf"},
        "pages": pages,
        "assets": [],
        "metadata": {},
    }


def _block(block_id, block_type, text, *, crop_ref=None, origin, source_page=1):
    block = {
        "id": block_id,
        "type": block_type,
        "text": text,
        "source_page": source_page,
        "confidence": 0.75,
        "origin": origin,
        "source_engine": "mineru",
        "evidence": {"raw_text": text, "provider": "mineru"},
        "bbox": None,
    }
    if crop_ref:
        block["crop_ref"] = crop_ref
        block["image_ref"] = crop_ref
    if block_type == "formula_block":
        block["latex"] = text
        block["raw_text"] = text
    return block


class _ConcurrencyCounter:
    def __init__(self):
        self.lock = threading.Lock()
        self.active = 0
        self.max_active = 0

    def __enter__(self):
        with self.lock:
            self.active += 1
            self.max_active = max(self.max_active, self.active)

    def __exit__(self, *_exc):
        with self.lock:
            self.active -= 1
