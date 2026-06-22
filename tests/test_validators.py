from ppt2md_app.ir import build_page_ir
from ppt2md_app.renderer import render_page_ir_to_markdown
from ppt2md_app.validators import is_api_error_text, validate_slide_markdown


def test_valid_slide_markdown_passes():
    result = validate_slide_markdown("# Slide 1\n\n文本 $v$。\n\n$$E=mc^2$$\n", 1, target_raw="文本 v")

    assert result.ok
    assert result.errors == []


def test_api_error_text_blocks_normal_slide_write():
    result = validate_slide_markdown(
        "# Slide 1\n\nDeepSeek HTTP Error: 429 rate limit\n",
        1,
        raw_response="DeepSeek HTTP Error: 429 rate limit",
    )

    assert not result.ok
    assert result.errors[0].code == "api_error_text"
    assert is_api_error_text("Brain Error: 500")


def test_heading_mismatch_and_ctx_leak_are_errors():
    result = validate_slide_markdown("# Slide 2\n\n[P-1] 前一页内容\n<CTX>x</CTX>\n", 1)

    codes = {issue.code for issue in result.errors}
    assert "heading_missing_or_mismatch" in codes
    assert "ctx_marker_leak" in codes


def test_unbalanced_display_math_is_error():
    result = validate_slide_markdown("# Slide 1\n\n$$E=mc^2\n", 1)

    assert not result.ok
    assert {issue.code for issue in result.errors} == {"display_math_unbalanced"}


def test_unbalanced_inline_math_is_error():
    result = validate_slide_markdown("# Slide 1\n\n速度为 $v，质量为 $m$。\n", 1)

    assert not result.ok
    assert {issue.code for issue in result.errors} == {"inline_math_unbalanced"}


def test_formula_brace_warning_does_not_block_slide():
    result = validate_slide_markdown("# Slide 1\n\n$$\\frac{a}{b$$\n", 1)

    assert result.ok
    assert [issue.code for issue in result.warnings] == ["formula_brace_unbalanced"]


def test_valid_complex_formula_is_not_warned():
    result = validate_slide_markdown("# Slide 1\n\n$$\\int_0^1 \\frac{x^2}{1+x}\\,dx$$\n", 1)

    assert result.ok
    assert result.warnings == []


def test_formula_markup_inside_aligned_warns_for_normalization():
    result = validate_slide_markdown(
        "# Slide 1\n\n"
        "$$\n"
        "\\begin{aligned}\n"
        "S &= k(\\ln Z+\\beta U) \\\\\n"
        "&= \\frac{3}{2}Nk\\ln T \\tag{5}\n"
        "\\end{aligned}\n"
        "$$\n",
        1,
    )

    assert result.ok
    assert "formula_markup_needs_normalize" in {issue.code for issue in result.warnings}


def test_ragged_markdown_table_warns():
    result = validate_slide_markdown("# Slide 1\n\n| A | B |\n| --- | --- |\n| 1 | 2 | 3 |\n", 1)

    assert result.ok
    assert [issue.code for issue in result.warnings] == ["table_structure_warning"]


def test_degraded_table_warning_block_is_not_reflagged_as_live_table():
    markdown = render_page_ir_to_markdown(
        build_page_ir("### Table Analysis\n| A | B |\n| --- | --- |\n| 1 | 2 | 3 |", 21)
    )

    result = validate_slide_markdown(markdown, 21)

    assert "table_structure_warning" not in {issue.code for issue in result.warnings}


def test_figure_analysis_is_warning_not_error():
    result = validate_slide_markdown("# Slide 1\n\n### Figure Analysis\n左侧是 A。\n", 1)

    assert result.ok
    assert [issue.code for issue in result.warnings] == ["unrendered_figure_analysis"]


def test_neighbor_unique_long_snippet_warns_only():
    result = validate_slide_markdown(
        "# Slide 2\n\n这是邻页独有的一段非常长的结论文字。\n",
        2,
        target_raw="当前页正文。",
        neighbor_raw={3: "这是邻页独有的一段非常长的结论文字。"},
    )

    assert result.ok
    assert [issue.code for issue in result.warnings] == ["possible_neighbor_leak"]


def test_figure_analysis_without_note_warns():
    result = validate_slide_markdown(
        "# Slide 1\n\n图中左侧是 A。\n",
        1,
        target_raw="### Figure Analysis\n图中左侧是 A。",
    )

    assert result.ok
    assert [issue.code for issue in result.warnings] == ["figure_note_missing"]


def test_chinese_figure_note_satisfies_figure_analysis():
    result = validate_slide_markdown(
        "# Slide 1\n\n> [!NOTE] 图示说明\n> 图中左侧是 A。\n",
        1,
        target_raw="### Figure Analysis\n图中左侧是 A。",
    )

    assert result.ok
    assert result.warnings == []


def test_figure_note_satisfies_figure_analysis():
    result = validate_slide_markdown(
        "# Slide 1\n\n> [!NOTE] 图示说明\n> 图中左侧区域被遮挡。\n",
        1,
        target_raw="### Figure Analysis\n图中左侧区域被遮挡。",
    )

    assert result.ok
    assert result.warnings == []


def test_low_ocr_coverage_warns_but_does_not_block():
    result = validate_slide_markdown(
        "# Slide 1\n\n热力学第一定律。\n",
        1,
        target_blocks=[
            {
                "type": "paragraph",
                "origin": "vision_ocr",
                "text": "热力学第一定律描述内能、热量和功之间的关系。孤立系统的总能量保持守恒。",
            }
        ],
    )

    assert result.ok
    assert [issue.code for issue in result.warnings] == ["ocr_coverage_low"]


def test_ocr_coverage_does_not_count_figure_description_as_missing_text():
    result = validate_slide_markdown(
        "# Slide 1\n\n正文完整。\n",
        1,
        target_blocks=[
            {"type": "paragraph", "origin": "vision_ocr", "text": "正文完整。"},
            {
                "type": "figure_note",
                "origin": "vision_description",
                "text": "坐标图中横轴为 t，纵轴为 v，曲线逐渐上升。",
            },
        ],
    )

    assert result.ok
    codes = {issue.code for issue in result.warnings}
    assert "ocr_coverage_low" not in codes
    assert codes == {"target_figure_block_missing"}


def test_present_target_figure_block_satisfies_block_coverage():
    blocks = [
        {
            "id": "p0001-b002",
            "type": "figure_note",
            "origin": "vision_description",
            "text": "坐标图中横轴为 t，纵轴为 v，曲线逐渐上升。",
        }
    ]

    result = validate_slide_markdown(
        "# Slide 1\n\n> [!NOTE] 图示说明\n> 坐标图中横轴为 t，纵轴为 v，曲线逐渐上升。\n",
        1,
        target_blocks=blocks,
    )

    assert "target_figure_block_missing" not in {issue.code for issue in result.warnings}


def test_missing_short_target_text_block_warns_even_when_ocr_coverage_is_not_checked():
    result = validate_slide_markdown(
        "# Slide 1\n\n其他内容。\n",
        1,
        target_blocks=[
            {
                "id": "p0001-b001",
                "type": "paragraph",
                "origin": "vision_ocr",
                "text": "关键结论保持不变",
            }
        ],
    )

    codes = {issue.code for issue in result.warnings}
    assert "ocr_coverage_low" not in codes
    assert "target_text_block_missing" in codes


def test_missing_target_table_block_warns():
    blocks = build_page_ir("### Table Analysis\n| 量 | 值 |\n| --- | --- |\n| 力 | N |", 5)["blocks"]

    result = validate_slide_markdown("# Slide 5\n\n这里讨论物理量。\n", 5, target_blocks=blocks)

    assert "target_table_block_missing" in {issue.code for issue in result.warnings}


def test_present_target_table_block_satisfies_block_coverage():
    raw = "### Table Analysis\n| 量 | 值 |\n| --- | --- |\n| 力 | N |"
    blocks = build_page_ir(raw, 5)["blocks"]

    result = validate_slide_markdown(render_page_ir_to_markdown(build_page_ir(raw, 5)), 5, target_blocks=blocks)

    assert "target_table_block_missing" not in {issue.code for issue in result.warnings}


def test_missing_target_uncertain_block_warns():
    blocks = build_page_ir("### Uncertain\n此处手写文字疑似为配分函数，但无法确定。", 6)["blocks"]

    result = validate_slide_markdown("# Slide 6\n\n正文。\n", 6, target_blocks=blocks)

    assert "target_uncertain_block_missing" in {issue.code for issue in result.warnings}


def test_present_target_uncertain_block_satisfies_block_coverage():
    raw = "### Uncertain\n此处手写文字疑似为配分函数，但无法确定。"
    blocks = build_page_ir(raw, 6)["blocks"]

    result = validate_slide_markdown(render_page_ir_to_markdown(build_page_ir(raw, 6)), 6, target_blocks=blocks)

    assert "target_uncertain_block_missing" not in {issue.code for issue in result.warnings}


def test_missing_target_formula_block_warns_even_when_page_text_is_present():
    target_blocks = build_page_ir(
        "### Formula\n"
        "\\begin{aligned}\n"
        "S &= k\\left(\\ln Z-\\beta \\frac{\\partial}{\\partial \\beta} \\ln Z\\right) \\\\\n"
        "&= k(\\ln Z+\\beta U) \\\\\n"
        "&= \\frac{3}{2} N k \\ln T+N k \\ln \\frac{V}{N}+N k\\left[\\ln \\left(\\frac{2 \\pi m k}{h^{2}}\\right)^{\\frac{3}{2}}+\\frac{5}{2}\\right].\n"
        "\\end{aligned}\n"
        "\\tag{5}\n\n"
        "上述式(3)、式(4)和式(5)分别与热力学中式(1.3.11)、式(1.7.4)和式(1.15.4)相当。",
        3,
    )["blocks"]
    markdown_missing_formula = (
        "# Slide 3\n\n"
        "上述式(3)、式(4)和式(5)分别与热力学中式(1.3.11)、式(1.7.4)和式(1.15.4)相当。\n"
    )

    result = validate_slide_markdown(markdown_missing_formula, 3, target_blocks=target_blocks)

    assert result.ok
    assert "target_formula_block_missing" in {issue.code for issue in result.warnings}


def test_present_target_formula_block_satisfies_formula_coverage():
    raw = "### Formula\nE = mc^2\n\n正文。"
    blocks = build_page_ir(raw, 4)["blocks"]

    result = validate_slide_markdown("# Slide 4\n\n$$\nE = mc^2\n$$\n\n正文。\n", 4, target_blocks=blocks)

    assert "target_formula_block_missing" not in {issue.code for issue in result.warnings}
