from ppt2md_app.formula_quality import assess_formula_text, normalize_formula_text


def test_formula_quality_normalizes_display_delimiters():
    result = assess_formula_text("$$\nE = mc^2\n$$")

    assert result.ok
    assert result.latex == "E = mc^2"
    assert normalize_formula_text(r"\[ a + b \]") == "a + b"


def test_formula_quality_records_latex_warnings():
    result = assess_formula_text(r"\frac a}{b")

    assert not result.ok
    assert [warning.code for warning in result.warnings] == ["latex_frac_missing_braces"]


def test_formula_quality_records_unbalanced_braces():
    result = assess_formula_text(r"\frac{a}{b")

    assert not result.ok
    assert "formula_brace_unbalanced" in [warning.code for warning in result.warnings]


def test_formula_quality_marks_uncertain_formula():
    result = assess_formula_text("E = [?] mc^2")

    assert result.uncertain
    assert [warning.code for warning in result.warnings] == ["formula_uncertain_marker"]
