from ppt2md_app import cli


def test_eval_cli_runs_without_dependency_or_api_checks(monkeypatch, tmp_path, capsys):
    def fail_if_called():
        raise AssertionError("ensure_dependencies should not run for offline eval")

    monkeypatch.setattr(cli, "ensure_dependencies", fail_if_called)

    code = cli.main(
        [
            "--eval-fixtures",
            "tests/fixtures/eval_cases",
            "--eval-output",
            str(tmp_path / "eval_report.json"),
        ]
    )

    captured = capsys.readouterr()
    assert code == 0
    assert "offline eval: 6/6 passed" in captured.out
    assert (tmp_path / "eval_report.json").exists()


def test_cli_build_config_exposes_ocr_confusion_opt_in(tmp_path):
    args = cli.parse_args(["--fix-ocr-confusion", "--output", str(tmp_path)])

    config = cli.build_config(args)

    assert config.fix_ocr_confusion is True
    assert config.output_folder == str(tmp_path.resolve())
