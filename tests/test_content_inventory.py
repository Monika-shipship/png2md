from docpage2md_app.content_inventory import build_content_inventory
from docpage2md_app.ir import build_page_ir
from docpage2md_app.renderer import render_page_ir_to_markdown


def test_content_inventory_accounts_rendered_and_degraded_blocks():
    page_ir = build_page_ir("标题\n\n### Figure Analysis\n坐标轴 x-y。\n\n| A | B |\n| 1 |\n", 1)
    page_ir["blocks"][1]["crop_ref"] = "assets/crops/figure.jpg"
    page_ir["blocks"][2]["crop_ref"] = "assets/crops/table.jpg"
    page_ir["blocks"][2]["table_format"] = "uncertain"
    page_ir["blocks"][2]["table_render_mode"] = "degraded_warning"
    markdown = render_page_ir_to_markdown(page_ir, 1)

    inventory = build_content_inventory(page_ir, markdown)

    assert inventory["summary"]["source_block_count"] == 3
    assert inventory["summary"]["rendered_count"] == 3
    assert inventory["summary"]["degraded_count"] == 1
    assert inventory["summary"]["unaccounted_count"] == 0
    assert inventory["summary"]["missing_visual_evidence_count"] == 0
    assert [entry["status"] for entry in inventory["entries"]] == ["rendered", "rendered", "degraded"]


def test_content_inventory_marks_unaudited_empty_block_as_unrendered():
    page_ir = {
        "source_page": 2,
        "blocks": [
            {
                "id": "p0002-b001",
                "type": "paragraph",
                "text": "",
                "source_engine": "mineru",
            }
        ],
    }

    inventory = build_content_inventory(page_ir, "# Slide 2\n")

    assert inventory["entries"][0]["status"] == "unrendered"
    assert inventory["summary"]["unaccounted_count"] == 1


def test_content_inventory_uses_op_audit_for_intentional_drop():
    page_ir = {
        "source_page": 3,
        "blocks": [
            {
                "id": "p0003-b001",
                "type": "paragraph",
                "text": "页码 3",
                "source_engine": "mineru",
            }
        ],
    }

    inventory = build_content_inventory(
        page_ir,
        "# Slide 3\n",
        op_audit=[{"op": "drop_page_number", "target_block_ids": ["p0003-b001"], "status": "applied"}],
    )

    assert inventory["entries"][0]["status"] == "dropped"
    assert inventory["summary"]["accounted_count"] == 1
    assert inventory["summary"]["unaccounted_count"] == 0


def test_content_inventory_does_not_attribute_global_before_after_ids_to_all_blocks():
    page_ir = {
        "source_page": 1,
        "blocks": [
            {
                "id": "p0001-b001",
                "type": "paragraph",
                "text": "修正后的正文",
                "source_engine": "brain",
            },
            {
                "id": "p0001-b002",
                "type": "paragraph",
                "text": "未修改的正文",
                "source_engine": "mineru",
            },
        ],
    }
    markdown = "# Slide 1\n\n修正后的正文\n\n未修改的正文\n"

    inventory = build_content_inventory(
        page_ir,
        markdown,
        op_audit=[
            {
                "op": "replace_text_span_checked",
                "status": "applied",
                "target_block_ids": ["p0001-b001"],
                "before_block_ids": ["p0001-b001", "p0001-b002"],
                "after_block_ids": ["p0001-b001", "p0001-b002"],
            }
        ],
    )

    assert [entry["status"] for entry in inventory["entries"]] == ["replaced", "rendered"]
    assert inventory["entries"][0]["audit_ops"] == ["replace_text_span_checked"]
    assert inventory["entries"][1]["audit_ops"] == []


def test_content_inventory_ignores_rejected_ops_for_status():
    page_ir = {
        "source_page": 1,
        "blocks": [
            {
                "id": "p0001-b001",
                "type": "paragraph",
                "text": "原始正文",
                "source_engine": "mineru",
            }
        ],
    }
    markdown = "# Slide 1\n\n原始正文\n"

    inventory = build_content_inventory(
        page_ir,
        markdown,
        op_audit=[
            {
                "op": "replace_text_span_checked",
                "status": "rejected",
                "target_block_ids": ["p0001-b001"],
            }
        ],
    )

    assert inventory["entries"][0]["status"] == "rendered"


def test_content_inventory_matches_normalized_markdown_text():
    page_ir = {
        "source_page": 1,
        "blocks": [
            {
                "id": "p0001-b001",
                "type": "formula_inline",
                "text": "参数  $\\alpha$ 可在有限或无限范围内连续变化.",
                "source_engine": "mineru",
            }
        ],
    }
    markdown = "# Slide 1\n\n参数 $\\alpha$ 可在有限或无限范围内连续变化.\n"

    inventory = build_content_inventory(page_ir, markdown)

    assert inventory["entries"][0]["status"] == "rendered"
    assert inventory["summary"]["unaccounted_count"] == 0


def test_content_inventory_matches_unicode_math_source_to_latex_markdown():
    page_ir = {
        "source_page": 1,
        "blocks": [
            {
                "id": "p0001-b001",
                "type": "paragraph",
                "text": "令 φ, θ, ω 为三个角，满足 α+β=γ。",
                "source_engine": "mineru",
            }
        ],
    }
    markdown = "# Slide 1\n\n令 $\\phi, \\theta, \\omega$ 为三个角，满足 $\\alpha + \\beta = \\gamma$。\n"

    inventory = build_content_inventory(page_ir, markdown)

    assert inventory["entries"][0]["status"] == "rendered"
    assert inventory["summary"]["unaccounted_count"] == 0
