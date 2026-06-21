from ppt2md_app.table_quality import assess_table, assess_table_markdown, normalize_table_text


def test_reliable_markdown_table_passes_quality_gate():
    result = assess_table_markdown("| A | B |\n| --- | --- |\n| 1 | 2 |")

    assert result.reliable
    assert result.errors == []
    assert result.warnings == []


def test_ragged_markdown_table_is_unreliable():
    result = assess_table_markdown("| A | B |\n| --- | --- |\n| 1 | 2 | 3 |")

    assert not result.reliable
    assert [issue.code for issue in result.errors] == ["table_column_mismatch"]


def test_table_shell_is_warning_and_unreliable():
    result = assess_table_markdown("| A | B |\n| --- | --- |")

    assert not result.reliable
    assert [issue.code for issue in result.warnings] == ["table_shell"]


def test_aligned_text_table_normalizes_to_markdown_table():
    text = "Name    Value\nForce   N\nMass    kg"
    result = assess_table(text)

    assert result.reliable
    assert result.table_format == "aligned_text"
    assert normalize_table_text(text) == "| Name | Value |\n| --- | --- |\n| Force | N |\n| Mass | kg |"


def test_html_table_is_supported_as_complex_table():
    text = "<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>"
    result = assess_table(text)

    assert result.reliable
    assert result.table_format == "html"
    assert normalize_table_text(text) == "| A | B |\n| --- | --- |\n| 1 | 2 |"


def test_complex_html_table_keeps_original_html():
    text = "<table><tr><th colspan=\"2\">A</th></tr><tr><td>1</td><td>2</td></tr></table>"
    result = assess_table(text)

    assert result.reliable
    assert result.table_format == "html"
    assert [issue.code for issue in result.warnings] == ["html_table_ragged", "html_table_complex_span"]
    assert normalize_table_text(text) == text


def test_unrecognized_table_is_unreliable():
    result = assess_table("A B C\n1 2")

    assert not result.reliable
    assert [issue.code for issue in result.errors] == ["table_unrecognized_format"]
