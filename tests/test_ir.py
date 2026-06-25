from pathlib import Path

from docpage2md_app.ir import (
    PAGE_IR_SCHEMA_VERSION,
    attach_page_image_evidence,
    build_page_ir,
    render_blocks_to_markdown,
    render_page_ir_to_markdown,
    render_page_record_to_markdown,
)
from docpage2md_app.reporting import summarize_blocks


def test_build_page_ir_creates_stable_blocks():
    raw = "标题:\n\n- a\n- b\n\n### Figure Analysis\n左侧是 A。\n"
    ir = build_page_ir(raw, 3)

    assert ir["schema_version"] == PAGE_IR_SCHEMA_VERSION
    assert ir["raw_text"] == raw
    assert ir["page_image_ref"] is None
    assert [block["id"] for block in ir["blocks"]] == ["p0003-b001", "p0003-b002", "p0003-b003"]
    assert [block["type"] for block in ir["blocks"]] == ["heading", "list", "figure_note"]
    assert [block["text"] for block in ir["blocks"]] == ["标题:", "- a\n- b", "左侧是 A。"]
    assert all(block["source_page"] == 3 for block in ir["blocks"])
    assert [block["origin"] for block in ir["blocks"]] == ["vision_ocr", "vision_ocr", "vision_description"]
    assert ir["blocks"][2]["evidence"]["raw_text"].startswith("### Figure Analysis")
    assert ir["blocks"][2]["figure_type"] == "unknown"
    assert ir["blocks"][2]["description"] == "左侧是 A。"
    assert ir["blocks"][2]["unrecognizable"] is False


def test_attach_page_image_evidence_sets_page_and_block_refs():
    ir = build_page_ir("### Formula\nE = [?] mc^2\n\n### Table Analysis\n| A | B |\n| --- | --- |\n| 1 | 2 |", 3)

    attached = attach_page_image_evidence(ir, "assets/pages/page-3.png")

    assert attached["page_image_ref"] == "assets/pages/page-3.png"
    assert all(block["page_image_ref"] == "assets/pages/page-3.png" for block in attached["blocks"])
    assert attached["blocks"][0]["crop_ref"] == "assets/pages/page-3.png"
    assert attached["blocks"][0]["crop_ref_is_page"] is True
    assert attached["blocks"][1]["crop_ref"] == "assets/pages/page-3.png"
    assert attached["blocks"][1]["crop_ref_is_page"] is True


def test_render_page_ir_to_markdown_is_deterministic():
    ir = build_page_ir("标题:\n\n正文 $E=mc^2$\n\n### Figure Analysis\n左侧是 A。\n右侧是 B。", 2)

    markdown = render_page_ir_to_markdown(ir)

    assert markdown == (
        "# Slide 2\n\n"
        "## 标题\n\n"
        "正文 $E=mc^2$\n\n"
        "<details>\n"
        "<summary>图示识别内容</summary>\n\n"
        "- 说明：\n"
        "  - 左侧是 A。\n"
        "  - 右侧是 B。\n"
        "- 可见标签：A，B\n\n"
        "</details>\n"
    )
    assert "<details open" not in markdown


def test_renderer_normalizes_unicode_math_inside_text_blocks():
    markdown = render_blocks_to_markdown(
        [
            {"type": "paragraph", "text": "令 φ, θ, ω 为三个角。"},
            {"type": "formula_inline", "text": "α+β=γ"},
            {"type": "figure_note", "description": "坐标轴标注为 θ 和 φ。"},
        ],
        22,
    )

    assert "$\\phi, \\theta, \\omega$" in markdown
    assert "$\\alpha + \\beta = \\gamma$" in markdown
    assert "$\\theta$" in markdown
    assert "$\\phi$" in markdown
    assert "φ" not in markdown
    assert "θ" not in markdown
    assert "ω" not in markdown


def test_golden_renderer_fixture():
    fixtures = Path(__file__).parent / "fixtures"
    raw = (fixtures / "golden_raw_stage1.txt").read_text(encoding="utf-8")
    expected = (fixtures / "golden_rendered.md").read_text(encoding="utf-8")

    assert render_page_ir_to_markdown(build_page_ir(raw, 7)) == expected


def test_renderer_provenance_comments_are_opt_in():
    ir = build_page_ir("标题:\n\n正文。", 12)

    default_markdown = render_page_ir_to_markdown(ir)
    debug_markdown = render_page_ir_to_markdown(ir, include_provenance_comments=True)

    assert "docpage2md-provenance" not in default_markdown
    assert "<!-- docpage2md-provenance id=p0012-template-slide-heading type=renderer_template origin=renderer_template source_page=12" in debug_markdown
    assert "<!-- docpage2md-provenance id=p0012-b001 type=heading origin=vision_ocr source_page=12" in debug_markdown
    assert "<!-- docpage2md-provenance id=p0012-b002 type=paragraph origin=vision_ocr source_page=12" in debug_markdown


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
    assert block["linked_blocks"] == []
    assert block["figure"]["figure_type"] == "flowchart"
    assert block["figure"]["linked_blocks"] == []
    assert block["origin"] == "vision_description"


def test_figure_link_uncertainty_does_not_mark_whole_figure_unrecognizable():
    raw = (
        "### Figure Analysis\n"
        "类型：坐标图。\n"
        "标签：横轴 t，纵轴 v。\n"
        "关系：曲线随 t 增大上升。\n"
        "正文关联：不确定。"
    )

    block = build_page_ir(raw, 19)["blocks"][0]

    assert block["figure_type"] == "coordinate_plot"
    assert block["unrecognizable"] is False
    assert block["confidence"] == 0.72


def test_figure_links_to_same_page_formula_block():
    raw = (
        "### Formula\n"
        "v(t) = at\n\n"
        "### Figure Analysis\n"
        "类型：坐标图。\n"
        "标签：横轴 t，纵轴 v。\n"
        "关系：曲线随 t 增大上升。\n"
        "正文关联：对应上方公式 v(t)。"
    )

    block = build_page_ir(raw, 20)["blocks"][1]

    assert block["linked_blocks"] == ["p0020-b001"]
    assert block["figure"]["linked_blocks"] == ["p0020-b001"]


def test_unrecognizable_figure_renders_clean_text_without_warning_block():
    raw = "### Figure Analysis\n图示被遮挡，无法确定节点和箭头方向。"

    ir = build_page_ir(raw, 10)
    markdown = render_page_ir_to_markdown(ir)

    assert ir["blocks"][0]["unrecognizable"] is True
    assert ir["blocks"][0]["confidence"] == 0.25
    assert markdown == (
        "# Slide 10\n\n"
        "<details>\n"
        "<summary>图示识别内容</summary>\n\n"
        "- 说明：图示被遮挡，无法确定节点和箭头方向。\n"
        "- 主要关系：图示被遮挡，无法确定节点和箭头方向。\n"
        "- 不确定点：图示不可可靠识别。\n\n"
        "</details>\n"
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
        "<details>\n"
        "<summary>图示识别内容</summary>\n\n"
        "- 说明：坐标图：横轴为 t，纵轴为 v。\n\n"
        "</details>\n"
    )


def test_figure_note_accepts_nested_model_metadata():
    markdown = render_blocks_to_markdown(
        [
            {
                "type": "figure_note",
                "description": "三角形 ABC，边 a、b、c 已标注。",
                "labels": {
                    "vertices": ["A", "B", "C"],
                    "sides": ["a", "b", "c"],
                    "internal_lines": ["altitude from A", "median?"],
                },
                "relations": ["side a opposite A"],
                "uncertainties": {"geometry": ["internal line role unclear"]},
                "unrecognizable": False,
            }
        ],
        21,
    )

    assert "vertices: A, B, C" in markdown
    assert "sides: a, b, c" in markdown
    assert "internal_lines: altitude from A, median?" in markdown
    assert "geometry: internal line role unclear" in markdown


def test_image_ref_uses_crop_ref_and_missing_path_stays_silent():
    markdown = render_blocks_to_markdown(
        [
            {"type": "image_ref", "crop_ref": "assets/crops/page-1-img.jpg", "alt": "crop"},
            {"type": "image_ref"},
        ],
        12,
    )

    assert markdown == "# Slide 12\n\n![crop](assets/crops/page-1-img.jpg)\n"
    assert "图片引用缺少路径" not in markdown


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
    assert ir["blocks"][0]["raw_text"] == "F = ma"
    assert ir["blocks"][0]["warnings"] == []
    assert ir["blocks"][1]["table_quality"]["schema_version"] == 1
    assert ir["blocks"][1]["table_reliable"] is True
    assert ir["blocks"][1]["table_render_mode"] == "normalized_markdown"


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


def test_uncertain_formula_renders_clean_raw_text_without_warning_block():
    ir = build_page_ir("### Formula\nE = [?] mc^2", 8)
    markdown = render_page_ir_to_markdown(ir)

    assert ir["blocks"][0]["formula_quality"]["warnings"][0]["code"] == "formula_uncertain_marker"
    assert markdown == "# Slide 8\n\nE = [?] mc^2\n"
    assert "> [!WARNING]" not in markdown
    assert "质量警告" not in markdown


def test_uncertain_formula_with_page_evidence_renders_image_reference():
    ir = attach_page_image_evidence(build_page_ir("### Formula\nE = [?] mc^2", 8), "assets/pages/page-8.png")

    markdown = render_page_ir_to_markdown(ir)

    assert markdown == "# Slide 8\n\n![formula](assets/pages/page-8.png)\n\nE = [?] mc^2\n"
    assert "> [!WARNING]" not in markdown


def test_unreliable_table_degrades_to_clean_raw_text():
    raw = "### Table Analysis\n| A | B |\n| --- | --- |\n| 1 | 2 | 3 |"

    markdown = render_page_ir_to_markdown(build_page_ir(raw, 9))

    assert markdown.startswith("# Slide 9\n\n```text\n")
    assert "> [!WARNING]" not in markdown
    assert "Markdown 表格行列数不一致" not in markdown
    assert "```text\n| A | B |\n| --- | --- |\n| 1 | 2 | 3 |\n```" in markdown


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
    assert "> [!WARNING]" not in markdown
    assert "已保留表格截图引用" not in markdown
    assert "原始识别已按纯文本保留" not in markdown
    assert "```text\n| A | B |\n| --- | --- |\n| 1 | 2 | 3 |\n```" in markdown


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


def test_table_caption_followed_by_reliable_table_renders_without_degrade_warning():
    raw = (
        "### Table Analysis\n"
        "表格位于页面下方，展示了群 $T = C_3 \\otimes D_2$ 的特征标或相关数据。\n"
        "- **表头（列）**：$e$, $3C_2^{(2)}$, $4C_3^{(1)}$, $4(C_3^{(1)})^2$\n"
        "- **行标签**：$D_1, D_2, D_3, D_4$\n"
        "- **数据内容**：\n\n"
        "| | $e$ | $3C_2^{(2)}$ | $4C_3^{(1)}$ | $4(C_3^{(1)})^2$ |\n"
        "| :--- | :---: | :---: | :---: | :---: |\n"
        "| **$D_1$** | 1 | 1 | 1 | 1 |\n"
        "| **$D_2$** | 1 | 1 | $w$ | $w^*$ |\n"
        "| **$D_3$** | 1 | 1 | $w^*$ | $w$ |\n"
        "| **$D_4$** | 3 | -1 | 0 | 0 |"
    )

    markdown = render_page_ir_to_markdown(build_page_ir(raw, 10))

    assert "> [!WARNING] 表格识别不确定" not in markdown
    assert "**$T = C_3 \\otimes D_2$ 特征标表**" in markdown
    assert "- **表头（列）**：$e$, $3C_2^{(2)}$, $4C_3^{(1)}$, $4(C_3^{(1)})^2$" in markdown
    assert "| **$D_4$** | 3 | -1 | 0 | 0 |" in markdown


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
