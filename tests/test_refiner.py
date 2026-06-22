from ppt2md_app.ir import PAGE_IR_SCHEMA_VERSION, build_page_ir, render_page_ir_to_markdown
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
    assert first.page_ir["raw_text"] == page_ir["raw_text"]
    assert first.page_ir["raw_text_sha256"] == page_ir["raw_text_sha256"]
    assert render_page_ir_to_markdown(first.page_ir) == "# Slide 2\n\n$$\nE = mc^2\n$$\n"
    assert second.changed is False
    assert second.applied_ops == []


def test_block_refiner_promotes_heading_and_marks_uncertain_without_markdown_patch():
    page_ir = {
        "schema_version": PAGE_IR_SCHEMA_VERSION,
        "source_page": 3,
        "raw_text": "定义:\n\n右下角有 [?] 看不清。",
        "raw_text_sha256": "d5c1a1a38f821cf9d2d0f73ef5a19334ff1a3ec474e46c7b7002a3edada5a203",
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


def test_block_op_checked_rejects_unknown_block_origin():
    page_ir = {
        "schema_version": PAGE_IR_SCHEMA_VERSION,
        "source_page": 6,
        "raw_text": "定义:\n\n正文。",
        "blocks": [
            {
                "id": "p0006-b001",
                "type": "paragraph",
                "text": "定义:",
                "source_page": 6,
                "origin": "vision_ocr",
                "confidence": 0.55,
                "evidence": {"raw_text": "定义:"},
                "bbox": None,
            },
            {
                "id": "p0006-b002",
                "type": "paragraph",
                "text": "正文。",
                "source_page": 6,
                "origin": "unknown_model_output",
                "confidence": 0.55,
                "evidence": {"raw_text": "正文。"},
                "bbox": None,
            },
        ],
    }

    refined, applied, detail = apply_block_op_checked(
        page_ir,
        {"op": "promote_heading", "id": "p0006-b001"},
        slide_no=6,
    )

    assert applied is False
    assert refined == page_ir
    assert detail["reason"] == "page_ir_contract_failed"
    assert "block_1_unknown_origin" in detail["errors"]


def test_block_op_checked_rejects_unknown_block_type():
    page_ir = {
        "schema_version": PAGE_IR_SCHEMA_VERSION,
        "source_page": 7,
        "raw_text": "标题:\n\n正文。",
        "blocks": [
            {
                "id": "p0007-b001",
                "type": "paragraph",
                "text": "标题:",
                "source_page": 7,
                "origin": "vision_ocr",
                "confidence": 0.55,
                "evidence": {"raw_text": "标题:"},
                "bbox": None,
            },
            {
                "id": "p0007-b002",
                "type": "freeform_markdown",
                "text": "正文。",
                "source_page": 7,
                "origin": "vision_ocr",
                "confidence": 0.55,
                "evidence": {"raw_text": "正文。"},
                "bbox": None,
            },
        ],
    }

    refined, applied, detail = apply_block_op_checked(
        page_ir,
        {"op": "promote_heading", "id": "p0007-b001"},
        slide_no=7,
    )

    assert applied is False
    assert refined == page_ir
    assert detail["reason"] == "page_ir_contract_failed"
    assert "block_1_unknown_type" in detail["errors"]


def test_block_op_checked_rejects_missing_bbox_field():
    page_ir = build_page_ir("普通正文\n\n后续正文。", 8)
    del page_ir["blocks"][1]["bbox"]

    refined, applied, detail = apply_block_op_checked(
        page_ir,
        {"op": "promote_heading", "id": "p0008-b001"},
        slide_no=8,
    )

    assert applied is False
    assert refined == page_ir
    assert detail["reason"] == "page_ir_contract_failed"
    assert "block_1_missing_bbox" in detail["errors"]


def test_block_op_checked_rejects_invalid_bbox_shape():
    page_ir = build_page_ir("普通正文\n\n后续正文。", 9)
    page_ir["blocks"][1]["bbox"] = [0, 1, 2]

    refined, applied, detail = apply_block_op_checked(
        page_ir,
        {"op": "promote_heading", "id": "p0009-b001"},
        slide_no=9,
    )

    assert applied is False
    assert refined == page_ir
    assert detail["reason"] == "page_ir_contract_failed"
    assert "block_1_invalid_bbox" in detail["errors"]


def test_block_op_checked_rejects_missing_confidence_field():
    page_ir = build_page_ir("普通正文\n\n后续正文。", 10)
    del page_ir["blocks"][1]["confidence"]

    refined, applied, detail = apply_block_op_checked(
        page_ir,
        {"op": "promote_heading", "id": "p0010-b001"},
        slide_no=10,
    )

    assert applied is False
    assert refined == page_ir
    assert detail["reason"] == "page_ir_contract_failed"
    assert "block_1_missing_confidence" in detail["errors"]


def test_block_op_checked_rejects_invalid_confidence_value():
    page_ir = build_page_ir("普通正文\n\n后续正文。", 11)
    page_ir["blocks"][1]["confidence"] = 1.5

    refined, applied, detail = apply_block_op_checked(
        page_ir,
        {"op": "promote_heading", "id": "p0011-b001"},
        slide_no=11,
    )

    assert applied is False
    assert refined == page_ir
    assert detail["reason"] == "page_ir_contract_failed"
    assert "block_1_invalid_confidence" in detail["errors"]


def test_block_op_checked_rejects_non_dict_evidence():
    page_ir = build_page_ir("普通正文\n\n后续正文。", 12)
    page_ir["blocks"][1]["evidence"] = "raw text"

    refined, applied, detail = apply_block_op_checked(
        page_ir,
        {"op": "promote_heading", "id": "p0012-b001"},
        slide_no=12,
    )

    assert applied is False
    assert refined == page_ir
    assert detail["reason"] == "page_ir_contract_failed"
    assert "block_1_invalid_evidence" in detail["errors"]


def test_block_op_checked_rejects_vision_block_without_raw_text_evidence():
    page_ir = build_page_ir("普通正文\n\n后续正文。", 13)
    page_ir["blocks"][1]["evidence"] = {}

    refined, applied, detail = apply_block_op_checked(
        page_ir,
        {"op": "promote_heading", "id": "p0013-b001"},
        slide_no=13,
    )

    assert applied is False
    assert refined == page_ir
    assert detail["reason"] == "page_ir_contract_failed"
    assert "block_1_missing_raw_text_evidence" in detail["errors"]


def test_block_op_checked_rejects_refiner_block_without_refiner_op_evidence():
    page_ir = build_page_ir("普通正文\n\n后续正文。", 14)
    page_ir["blocks"][1]["origin"] = "refiner_op"
    page_ir["blocks"][1]["evidence"] = {"raw_text": "后续正文。"}

    refined, applied, detail = apply_block_op_checked(
        page_ir,
        {"op": "promote_heading", "id": "p0014-b001"},
        slide_no=14,
    )

    assert applied is False
    assert refined == page_ir
    assert detail["reason"] == "page_ir_contract_failed"
    assert "block_1_missing_refiner_op_evidence" in detail["errors"]


def test_block_op_checked_rejects_page_ir_missing_raw_text():
    page_ir = build_page_ir("普通正文\n\n后续正文。", 15)
    del page_ir["raw_text"]

    refined, applied, detail = apply_block_op_checked(
        page_ir,
        {"op": "promote_heading", "id": "p0015-b001"},
        slide_no=15,
    )

    assert applied is False
    assert refined == page_ir
    assert detail["reason"] == "page_ir_contract_failed"
    assert "raw_text_missing" in detail["errors"]


def test_block_op_checked_rejects_page_ir_missing_raw_text_hash():
    page_ir = build_page_ir("普通正文\n\n后续正文。", 16)
    del page_ir["raw_text_sha256"]

    refined, applied, detail = apply_block_op_checked(
        page_ir,
        {"op": "promote_heading", "id": "p0016-b001"},
        slide_no=16,
    )

    assert applied is False
    assert refined == page_ir
    assert detail["reason"] == "page_ir_contract_failed"
    assert "raw_text_sha256_missing" in detail["errors"]


def test_block_op_checked_rejects_page_ir_raw_text_hash_mismatch():
    page_ir = build_page_ir("普通正文\n\n后续正文。", 17)
    page_ir["raw_text_sha256"] = "bad"

    refined, applied, detail = apply_block_op_checked(
        page_ir,
        {"op": "promote_heading", "id": "p0017-b001"},
        slide_no=17,
    )

    assert applied is False
    assert refined == page_ir
    assert detail["reason"] == "page_ir_contract_failed"
    assert "raw_text_sha256_mismatch" in detail["errors"]


def test_block_op_checked_rejects_invalid_block_id_format():
    page_ir = build_page_ir("普通正文\n\n后续正文。", 18)
    page_ir["blocks"][1]["id"] = "block-2"

    refined, applied, detail = apply_block_op_checked(
        page_ir,
        {"op": "promote_heading", "id": "p0018-b001"},
        slide_no=18,
    )

    assert applied is False
    assert refined == page_ir
    assert detail["reason"] == "page_ir_contract_failed"
    assert "block_1_invalid_id" in detail["errors"]


def test_block_op_checked_rejects_cross_page_block_id_prefix():
    page_ir = build_page_ir("普通正文\n\n后续正文。", 19)
    page_ir["blocks"][1]["id"] = "p0020-b002"

    refined, applied, detail = apply_block_op_checked(
        page_ir,
        {"op": "promote_heading", "id": "p0019-b001"},
        slide_no=19,
    )

    assert applied is False
    assert refined == page_ir
    assert detail["reason"] == "page_ir_contract_failed"
    assert "block_1_invalid_id" in detail["errors"]


def test_block_op_checked_rejects_page_ir_missing_source_page():
    page_ir = build_page_ir("普通正文\n\n后续正文。", 20)
    del page_ir["source_page"]

    refined, applied, detail = apply_block_op_checked(
        page_ir,
        {"op": "promote_heading", "id": "p0020-b001"},
        slide_no=20,
    )

    assert applied is False
    assert refined == page_ir
    assert detail["reason"] == "page_ir_contract_failed"
    assert "source_page_missing" in detail["errors"]


def test_block_op_checked_rejects_invalid_source_page_value():
    page_ir = build_page_ir("普通正文\n\n后续正文。", 21)
    page_ir["source_page"] = "21"

    refined, applied, detail = apply_block_op_checked(
        page_ir,
        {"op": "promote_heading", "id": "p0021-b001"},
        slide_no=21,
    )

    assert applied is False
    assert refined == page_ir
    assert detail["reason"] == "page_ir_contract_failed"
    assert "source_page_not_positive_int" in detail["errors"]


def test_block_op_checked_rejects_source_page_slide_mismatch():
    page_ir = build_page_ir("普通正文\n\n后续正文。", 22)
    page_ir["source_page"] = 23
    page_ir["blocks"][0]["source_page"] = 23
    page_ir["blocks"][1]["source_page"] = 23
    page_ir["blocks"][0]["id"] = "p0023-b001"
    page_ir["blocks"][1]["id"] = "p0023-b002"

    refined, applied, detail = apply_block_op_checked(
        page_ir,
        {"op": "promote_heading", "id": "p0023-b001"},
        slide_no=22,
    )

    assert applied is False
    assert refined == page_ir
    assert detail["reason"] == "page_ir_contract_failed"
    assert "source_page_mismatch" in detail["errors"]


def test_block_op_checked_rejects_page_ir_missing_schema_version():
    page_ir = build_page_ir("普通正文\n\n后续正文。", 23)
    del page_ir["schema_version"]

    refined, applied, detail = apply_block_op_checked(
        page_ir,
        {"op": "promote_heading", "id": "p0023-b001"},
        slide_no=23,
    )

    assert applied is False
    assert refined == page_ir
    assert detail["reason"] == "page_ir_contract_failed"
    assert "schema_version_missing" in detail["errors"]


def test_block_op_checked_rejects_non_int_schema_version():
    page_ir = build_page_ir("普通正文\n\n后续正文。", 24)
    page_ir["schema_version"] = "9"

    refined, applied, detail = apply_block_op_checked(
        page_ir,
        {"op": "promote_heading", "id": "p0024-b001"},
        slide_no=24,
    )

    assert applied is False
    assert refined == page_ir
    assert detail["reason"] == "page_ir_contract_failed"
    assert "schema_version_not_int" in detail["errors"]


def test_block_op_checked_rejects_old_schema_version():
    page_ir = build_page_ir("普通正文\n\n后续正文。", 25)
    page_ir["schema_version"] = PAGE_IR_SCHEMA_VERSION - 1

    refined, applied, detail = apply_block_op_checked(
        page_ir,
        {"op": "promote_heading", "id": "p0025-b001"},
        slide_no=25,
    )

    assert applied is False
    assert refined == page_ir
    assert detail["reason"] == "page_ir_contract_failed"
    assert "schema_version_mismatch" in detail["errors"]
