from pathlib import Path

from ppt2md_app.ir import build_page_ir, render_blocks_to_markdown, render_page_ir_to_markdown, render_page_record_to_markdown
from ppt2md_app.reporting import summarize_blocks


def test_build_page_ir_creates_stable_blocks():
    raw = "标题:\n\n- a\n- b\n\n### Figure Analysis\n左侧是 A。\n"
    ir = build_page_ir(raw, 3)

    assert ir["schema_version"] == 7
    assert ir["raw_text"] == raw
    assert [block["id"] for block in ir["blocks"]] == ["p0003-b001", "p0003-b002", "p0003-b003"]
    assert [block["type"] for block in ir["blocks"]] == ["heading", "list", "figure_note"]
    assert [block["text"] for block in ir["blocks"]] == ["标题:", "- a\n- b", "左侧是 A。"]
    assert all(block["source_page"] == 3 for block in ir["blocks"])
    assert [block["origin"] for block in ir["blocks"]] == ["vision_ocr", "vision_ocr", "vision_description"]
    assert ir["blocks"][2]["evidence"]["raw_text"].startswith("### Figure Analysis")
    assert ir["blocks"][2]["figure_type"] == "unknown"
    assert ir["blocks"][2]["description"] == "左侧是 A。"
    assert ir["blocks"][2]["unrecognizable"] is False


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


def test_renderer_provenance_comments_are_opt_in():
    ir = build_page_ir("标题:\n\n正文。", 12)

    default_markdown = render_page_ir_to_markdown(ir)
    debug_markdown = render_page_ir_to_markdown(ir, include_provenance_comments=True)

    assert "png2md-provenance" not in default_markdown
    assert "<!-- png2md-provenance id=p0012-b001 type=heading origin=vision_ocr source_page=12" in debug_markdown
    assert "<!-- png2md-provenance id=p0012-b002 type=paragraph origin=vision_ocr source_page=12" in debug_markdown


def test_figure_analysis_extracts_structured_fields():
    raw = (
        "### Figure Analysis\n"
        "类型：流程图。\n"
        "节点：A、B、C。\n"
        "连接：A 指向 B，B 指向 C。\n"
        "正文关联：对应当前页的实验步骤。"
    )

    block = build_page_ir(raw, 6)["blocks"][0]

    assert block["type"] == "figure_note"
    assert block["figure_type"] == "flowchart"
    assert block["description"].startswith("类型：流程图")
    assert block["labels"][:3] == ["A", "B", "C"]
    assert block["relations"] == ["连接：A 指向 B，B 指向 C。"]
    assert block["origin"] == "vision_description"


def test_unrecognizable_figure_renders_as_warning_block():
    raw = "### Figure Analysis\n图示被遮挡，无法确定节点和箭头方向。"

    ir = build_page_ir(raw, 10)
    markdown = render_page_ir_to_markdown(ir)

    assert ir["blocks"][0]["unrecognizable"] is True
    assert ir["blocks"][0]["confidence"] == 0.25
    assert markdown == (
        "# Slide 10\n\n"
        "> [!WARNING] 图示识别不确定\n"
        "> 图示被遮挡，无法确定节点和箭头方向。\n"
    )


def test_figure_with_image_path_renders_markdown_image_reference():
    markdown = render_blocks_to_markdown(
        [
            {
                "type": "figure_note",
                "description": "坐标图：横轴为 t，纵轴为 v。",
                "image_path": "assets/figures/page-1-figure-1.png",
                "alt": "page 1 figure 1",
                "unrecognizable": False,
            }
        ],
        11,
    )

    assert markdown == (
        "# Slide 11\n\n"
        "![page 1 figure 1](assets/figures/page-1-figure-1.png)\n\n"
        "> [!NOTE] 图示说明\n"
        "> 坐标图：横轴为 t，纵轴为 v。\n"
    )


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
    assert ir["blocks"][0]["latex"] == "F = ma"
    assert ir["blocks"][0]["formula_quality"]["ok"] is True


def test_semantic_sections_render_as_readable_markdown_labels():
    ir = build_page_ir(
        "### Definition\n"
        "线性空间是对加法和数乘封闭的集合。\n\n"
        "### Proof\n"
        "由封闭性和结合律可得结论。\n\n"
        "### Example\n"
        "1. R^n 是线性空间。\n"
        "2. 多项式集合也是线性空间。",
        16,
    )

    assert [block["semantic_role"] for block in ir["blocks"]] == ["definition", "proof", "example"]
    assert [block["semantic_role_source"] for block in ir["blocks"]] == ["section", "section", "section"]
    assert [block["type"] for block in ir["blocks"]] == ["paragraph", "paragraph", "list"]
    assert summarize_blocks(ir["blocks"])["semantic_role_counts"] == {"definition": 1, "proof": 1, "example": 1}
    assert render_page_ir_to_markdown(ir) == (
        "# Slide 16\n\n"
        "**定义：**\n\n"
        "线性空间是对加法和数乘封闭的集合。\n\n"
        "**证明：**\n\n"
        "由封闭性和结合律可得结论。\n\n"
        "**例题：**\n\n"
        "1. R^n 是线性空间。\n"
        "2. 多项式集合也是线性空间。\n"
    )


def test_inline_semantic_role_keeps_original_markdown_text():
    ir = build_page_ir("证明：由 $a=b$ 可得 $a+c=b+c$。", 17)

    assert ir["blocks"][0]["semantic_role"] == "proof"
    assert ir["blocks"][0]["semantic_role_source"] == "inline"
    assert render_page_ir_to_markdown(ir) == "# Slide 17\n\n证明：由 $a=b$ 可得 $a+c=b+c$。\n"


def test_compact_chinese_semantic_section_heading_is_recognized():
    ir = build_page_ir("### 例1\n计算 $\\int_0^1 x dx$。", 18)

    assert ir["blocks"][0]["semantic_role"] == "example"
    assert ir["blocks"][0]["semantic_role_source"] == "section"
    assert render_page_ir_to_markdown(ir) == "# Slide 18\n\n**例题：**\n\n计算 $\\int_0^1 x dx$。\n"


def test_uncertain_formula_renders_as_warning_block():
    ir = build_page_ir("### Formula\nE = [?] mc^2", 8)
    markdown = render_page_ir_to_markdown(ir)

    assert ir["blocks"][0]["formula_quality"]["warnings"][0]["code"] == "formula_uncertain_marker"
    assert markdown == (
        "# Slide 8\n\n"
        "> [!WARNING] 公式识别不确定\n"
        "> 原始识别：\n"
        "> E = [?] mc^2\n"
    )


def test_unreliable_table_degrades_to_warning_block():
    raw = "### Table Analysis\n| A | B |\n| --- | --- |\n| 1 | 2 | 3 |"

    markdown = render_page_ir_to_markdown(build_page_ir(raw, 9))

    assert markdown.startswith("# Slide 9\n\n> [!WARNING] 表格识别不确定\n")
    assert "Markdown 表格行列数不一致" in markdown
    assert "> | 1 | 2 | 3 |" in markdown


def test_unreliable_table_with_image_path_keeps_markdown_image_reference():
    markdown = render_blocks_to_markdown(
        [
            {
                "type": "table",
                "text": "| A | B |\n| --- | --- |\n| 1 | 2 | 3 |",
                "table_image_path": "assets/tables/page-9-table-1.png",
                "alt": "page 9 table 1",
            }
        ],
        9,
    )

    assert markdown.startswith("# Slide 9\n\n![page 9 table 1](assets/tables/page-9-table-1.png)\n\n")
    assert "> [!WARNING] 表格识别不确定" in markdown
    assert "> 已保留表格截图引用。" in markdown
    assert "> 原始识别：" in markdown


def test_aligned_text_table_renders_as_markdown_table():
    ir = build_page_ir("Name    Value\nForce   N\nMass    kg", 13)

    markdown = render_page_ir_to_markdown(ir)

    assert ir["blocks"][0]["type"] == "table"
    assert markdown == (
        "# Slide 13\n\n"
        "| Name | Value |\n"
        "| --- | --- |\n"
        "| Force | N |\n"
        "| Mass | kg |\n"
    )


def test_simple_html_table_renders_as_markdown_table():
    raw = "<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>"
    markdown = render_page_ir_to_markdown(build_page_ir(raw, 14))

    assert markdown == "# Slide 14\n\n| A | B |\n| --- | --- |\n| 1 | 2 |\n"


def test_complex_html_table_is_preserved_inside_markdown():
    raw = "<table><tr><th colspan=\"2\">A</th></tr><tr><td>1</td><td>2</td></tr></table>"
    markdown = render_page_ir_to_markdown(build_page_ir(raw, 15))

    assert markdown == f"# Slide 15\n\n{raw}\n"


def test_render_page_record_falls_back_to_raw_text_when_blocks_missing():
    markdown = render_page_record_to_markdown({"slide_no": 5, "raw_text": "只有 raw。"})

    assert markdown == "# Slide 5\n\n只有 raw。\n"
