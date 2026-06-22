import json

import pytest

from ppt2md_app.eval import load_eval_case, load_eval_cases, run_offline_eval


def test_eval_loader_reads_fixture_cases():
    cases = load_eval_cases("tests/fixtures/eval_cases")

    assert len(cases) == 6
    assert {case.name for case in cases} == {
        "plain_text_handwritten",
        "formula_derivation_uncertain",
        "figure_coordinate_plot",
        "table_reliable",
        "table_degraded_with_image",
        "mixed_notes_page",
    }
    assert all(case.raw_text.strip() for case in cases)
    assert all(case.expected_markdown.startswith("# Slide ") for case in cases)


def test_eval_loader_rejects_missing_required_case_field(tmp_path):
    case_dir = tmp_path / "bad_case"
    case_dir.mkdir()
    (case_dir / "case.json").write_text(json.dumps({"name": "bad"}), encoding="utf-8")
    (case_dir / "raw_stage1.txt").write_text("raw", encoding="utf-8")
    (case_dir / "expected.md").write_text("# Slide 1\n\nraw\n", encoding="utf-8")

    with pytest.raises(ValueError, match="missing fields"):
        load_eval_case(case_dir)


def test_run_offline_eval_passes_builtin_fixtures(tmp_path):
    report = run_offline_eval("tests/fixtures/eval_cases", tmp_path / "eval_report.json")

    assert report["summary"]["cases_total"] == 6
    assert report["summary"]["cases_passed"] == 6
    assert report["summary"]["cases_failed"] == 0
    assert report["summary"]["validation_errors"] == 0
    assert report["summary"]["actual_tokens"] is None
    assert report["summary"]["block_counts"]["formula_block"] >= 1
    assert report["summary"]["block_counts"]["figure_note"] >= 1
    assert report["summary"]["block_counts"]["table"] >= 1
    assert all(result["provenance"]["schema_version"] == 3 for result in report["cases"])
