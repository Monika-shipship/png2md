from ppt2md_app.ir import build_page_ir, render_page_ir_to_markdown
from ppt2md_app.refiner import (
    BLOCK_KNOWN_OPS,
    KNOWN_OPS,
    SAFE_OPS,
    apply_block_op_checked,
    apply_op_checked,
    detect_markdown_suspects,
    refine_page_ir,
    refine_slide_markdown,
)


def test_refiner_detects_and_applies_safe_heading_fix():
    result = refine_slide_markdown("正文\n", 4)

    assert result.changed
    assert result.markdown.startswith("# Slide 4")
    assert result.validation["ok"] is True
    assert result.applied_ops[0]["op"] == "fix_heading"


def test_refiner_strips_chatter_without_free_rewrite():
    result = refine_slide_markdown("以下是整理结果：\n# Slide 1\n\n正文\n", 1)

    assert result.markdown == "# Slide 1\n\n正文\n"
    assert [op["op"] for op in result.applied_ops] == ["strip_chatter"]


def test_apply_op_checked_does_not_rewrite_api_error_text():
    suspect = detect_markdown_suspects("DeepSeek HTTP Error: 429\n", 1)[0]
    markdown, applied, detail = apply_op_checked(
        "DeepSeek HTTP Error: 429\n",
        suspect,
        1,
        raw_response="DeepSeek HTTP Error: 429",
    )

    assert markdown == "DeepSeek HTTP Error: 429\n"
    assert applied is False
    assert detail["reason"] == "unsafe_or_error_text"


def test_refiner_known_ops_include_failure_and_line_merge_ids():
    assert {"strip_chatter", "fix_heading", "drop_empty", "merge_broken_line", "mark_failed_page"} <= KNOWN_OPS
    assert "mark_failed_page" not in SAFE_OPS


def test_refiner_can_merge_broken_hyphenated_line():
    result = refine_slide_markdown("# Slide 1\n\ninter-\nnal energy\n", 1)

    assert result.changed
    assert "internal energy" in result.markdown
    assert result.validation["ok"] is True


def test_block_refiner_known_ops_are_block_id_based():
    assert {
        "merge_block",
        "drop_block",
        "promote_heading",
        "demote_heading",
        "convert_figure_note",
        "mark_uncertain",
        "normalize_formula",
    } <= BLOCK_KNOWN_OPS


def test_apply_block_op_checked_merges_adjacent_blocks_with_audit():
    page_ir = build_page_ir("inter-\n\nnal energy", 1)

    refined, applied, detail = apply_block_op_checked(
        page_ir,
        {"op": "merge_block", "a": "p0001-b001", "b": "p0001-b002"},
        slide_no=1,
    )

    assert applied is True
    assert [block["id"] for block in refined["blocks"]] == ["p0001-b001"]
    assert refined["blocks"][0]["text"] == "internal energy"
    assert refined["blocks"][0]["origin"] == "refiner_op"
    assert detail["before_block_ids"] == ["p0001-b001", "p0001-b002"]
    assert detail["after_block_ids"] == ["p0001-b001"]
    assert render_page_ir_to_markdown(refined) == "# Slide 1\n\ninternal energy\n"


def test_block_refiner_normalizes_formula_and_is_idempotent():
    page_ir = build_page_ir("### Formula\n$$\nE = mc^2\n$$", 2)

    first = refine_page_ir(page_ir, slide_no=2)
    second = refine_page_ir(first.page_ir, slide_no=2)

    assert first.changed is True
    assert first.applied_ops[0]["op"]["op"] == "normalize_formula"
    assert first.page_ir["blocks"][0]["text"] == "E = mc^2"
    assert first.page_ir["blocks"][0]["latex"] == "E = mc^2"
    assert first.page_ir["blocks"][0]["formula_quality"]["ok"] is True
    assert render_page_ir_to_markdown(first.page_ir) == "# Slide 2\n\n$$\nE = mc^2\n$$\n"
    assert second.changed is False
    assert second.applied_ops == []


def test_block_refiner_promotes_heading_and_marks_uncertain_without_markdown_patch():
    page_ir = {
        "schema_version": 4,
        "source_page": 3,
        "blocks": [
            {
                "id": "p0003-b001",
                "type": "paragraph",
                "text": "定义:",
                "source_page": 3,
                "origin": "vision_ocr",
                "confidence": 0.55,
                "evidence": {"raw_text": "定义:"},
                "bbox": None,
            },
            {
                "id": "p0003-b002",
                "type": "paragraph",
                "text": "右下角有 [?] 看不清。",
                "source_page": 3,
                "origin": "vision_ocr",
                "confidence": 0.55,
                "evidence": {"raw_text": "右下角有 [?] 看不清。"},
                "bbox": None,
            },
        ],
    }

    result = refine_page_ir(page_ir, slide_no=3)

    assert [op["op"]["op"] for op in result.applied_ops] == ["promote_heading", "mark_uncertain"]
    assert [block["type"] for block in result.page_ir["blocks"]] == ["heading", "uncertain"]
    assert result.page_ir["blocks"][0]["origin"] == "refiner_op"
    assert render_page_ir_to_markdown(result.page_ir).startswith("# Slide 3\n\n## 定义")


def test_block_op_checked_rejects_contract_breaking_drop():
    page_ir = build_page_ir("正文。", 5)

    refined, applied, detail = apply_block_op_checked(
        page_ir,
        {"op": "drop_block", "id": "p0005-b001", "reason": "unsafe_delete"},
        slide_no=5,
    )

    assert applied is False
    assert refined == page_ir
    assert detail["reason"] == "no_change"
