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
