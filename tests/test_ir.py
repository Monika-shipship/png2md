from pathlib import Path

from ppt2md_app.ir import build_page_ir, render_page_ir_to_markdown, render_page_record_to_markdown


def test_build_page_ir_creates_stable_blocks():
    ir = build_page_ir("标题:\n\n- a\n- b\n\n### Figure Analysis\n左侧是 A。\n", 3)

    assert ir["schema_version"] == 2
    assert [block["id"] for block in ir["blocks"]] == ["p0003-b001", "p0003-b002", "p0003-b003"]
    assert [block["type"] for block in ir["blocks"]] == ["heading", "list", "figure_note"]
    assert [block["text"] for block in ir["blocks"]] == ["标题:", "- a\n- b", "左侧是 A。"]
    assert all(block["source_page"] == 3 for block in ir["blocks"])
    assert [block["origin"] for block in ir["blocks"]] == ["vision_ocr", "vision_ocr", "vision_description"]
    assert ir["blocks"][2]["evidence"]["raw_text"].startswith("### Figure Analysis")


def test_render_page_ir_to_markdown_is_deterministic():
    ir = build_page_ir("标题:\n\n正文 $E=mc^2$\n\n### Figure Analysis\n左侧是 A。\n右侧是 B。", 2)

    markdown = render_page_ir_to_markdown(ir)

    assert markdown == (
        "# Slide 2\n\n"
        "## 标题\n\n"
        "正文 $E=mc^2$\n\n"
        "> [!NOTE] 图示说明\n"
        "> 左侧是 A。\n"
        "> 右侧是 B。\n"
    )


def test_golden_renderer_fixture():
    fixtures = Path(__file__).parent / "fixtures"
    raw = (fixtures / "golden_raw_stage1.txt").read_text(encoding="utf-8")
    expected = (fixtures / "golden_rendered.md").read_text(encoding="utf-8")

    assert render_page_ir_to_markdown(build_page_ir(raw, 7)) == expected


def test_handwritten_sections_become_renderable_block_types():
    ir = build_page_ir(
        "### Formula\n"
        "F = ma\n\n"
        "### Table Analysis\n"
        "| 量 | 值 |\n"
        "| --- | --- |\n"
        "| a | 1 |\n\n"
        "### Uncertain\n"
        "右下角被涂改。",
        4,
    )

    assert [block["type"] for block in ir["blocks"]] == ["formula_block", "table", "uncertain"]
    assert [block["origin"] for block in ir["blocks"]] == ["vision_formula", "vision_table", "vision_uncertain"]
    assert [block["text"] for block in ir["blocks"]] == [
        "F = ma",
        "| 量 | 值 |\n| --- | --- |\n| a | 1 |",
        "右下角被涂改。",
    ]


def test_render_page_record_falls_back_to_raw_text_when_blocks_missing():
    markdown = render_page_record_to_markdown({"slide_no": 5, "raw_text": "只有 raw。"})

    assert markdown == "# Slide 5\n\n只有 raw。\n"
