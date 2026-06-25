from pathlib import Path

from docpage2md_app import cli
from docpage2md_app.files import write_json
from docpage2md_app.input_inspection import build_page_chunks


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


def test_cli_build_config_exposes_mineru_multiformat_options(tmp_path):
    args = cli.parse_args(
        [
            "--engine-mode",
            "hybrid",
            "--document-type",
            "handwritten_notes",
            "--model-profile",
            "accurate",
            "--input-file",
            "notes.pdf",
            "--page-ranges",
            "1-5",
            "--output",
            str(tmp_path),
        ]
    )

    config = cli.build_config(args)

    assert config.engine_mode == "hybrid"
    assert config.document_type == "handwritten_notes"
    assert config.model_profile == "accurate"
    assert config.mineru_model_version == "vlm"
    assert config.mineru_page_ranges == "1-5"
    assert config.model_brain == "deepseek-v4-pro"
    assert config.brain_provider == "deepseek"


def test_cli_build_config_exposes_mineru_advanced_options(tmp_path):
    args = cli.parse_args(
        [
            "--input-file",
            "notes.pdf",
            "--mineru-is-ocr",
            "false",
            "--mineru-enable-formula",
            "true",
            "--mineru-enable-table",
            "false",
            "--mineru-language",
            "en",
            "--auto-split-pages",
            "--mineru-page-chunk-size",
            "150",
            "--output",
            str(tmp_path),
        ]
    )

    config = cli.build_config(args)

    assert config.mineru_is_ocr is False
    assert config.mineru_enable_formula is True
    assert config.mineru_enable_table is False
    assert config.mineru_language == "en"
    assert config.mineru_auto_split_pages is True
    assert config.mineru_page_chunk_size == 150


def test_cli_explicit_model_overrides_win_over_profile(tmp_path):
    args = cli.parse_args(
        [
            "--model-profile",
            "balanced",
            "--vision-provider",
            "openai_compatible",
            "--vision-model",
            "custom-vision",
            "--vision-base-url",
            "https://vision.example/v1",
            "--vision-api-key-env",
            "VISION_KEY",
            "--brain-provider",
            "openai_compatible",
            "--brain-model",
            "custom-brain",
            "--brain-base-url",
            "https://brain.example/v1",
            "--brain-api-key-env",
            "BRAIN_KEY",
            "--output",
            str(tmp_path),
        ]
    )

    config = cli.build_config(args)

    assert config.model_profile == "balanced"
    assert config.vision_provider == "openai_compatible"
    assert config.model_vision == "custom-vision"
    assert config.vision_base_url == "https://vision.example/v1"
    assert config.vision_api_key_env == "VISION_KEY"
    assert config.brain_provider == "openai_compatible"
    assert config.model_brain == "custom-brain"
    assert config.brain_base_url == "https://brain.example/v1"
    assert config.brain_api_key_env == "BRAIN_KEY"


def test_cli_manual_profile_accepts_explicit_model_overrides(tmp_path):
    args = cli.parse_args(
        [
            "--model-profile",
            "manual",
            "--vision-provider",
            "dashscope_openai",
            "--vision-model",
            "qwen3.7-plus",
            "--brain-provider",
            "deepseek",
            "--brain-model",
            "deepseek-v4-pro",
            "--output",
            str(tmp_path),
        ]
    )

    config = cli.build_config(args)

    assert config.model_profile == "manual"
    assert config.vision_provider == "dashscope_openai"
    assert config.model_vision == "qwen3.7-plus"
    assert config.brain_provider == "deepseek"
    assert config.model_brain == "deepseek-v4-pro"


def test_mineru_batch_processing_writes_per_document_process_log(monkeypatch, tmp_path):
    artifact = tmp_path / "artifact"
    artifact.mkdir()
    source = tmp_path / "notes.pdf"
    source.write_bytes(b"%PDF fake")
    args = cli.parse_args(["--input-files", str(source), "--output", str(tmp_path / "out")])
    config = cli.build_config(args)

    class FakeClient:
        def download_zip(self, _url, zip_path):
            zip_path.write_bytes(b"zip")

    class FakeResult:
        full_zip_url = "https://example.com/result.zip"
        task_id = "task-1"
        file_name = "notes.pdf"
        data_id = "data-1"

    monkeypatch.setattr("docpage2md_app.mineru_cache.unzip_mineru_result", lambda _zip, dest: dest.mkdir(parents=True, exist_ok=True))
    monkeypatch.setattr("docpage2md_app.mineru_cache.write_task_manifest", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        "docpage2md_app.mineru_pipeline.process_mineru_artifact_task",
        lambda artifact_dir, config, doc_name, engine_mode, source_path, progress: (
            progress("DocumentIR ready: pages=1, blocks=1") or {
                "page_count": 1,
                "output_dir": str(tmp_path / "out" / "notes"),
            }
        ),
    )
    shared_logger = cli.RunLogger(tmp_path / "out" / "mineru_batch" / "process.log", echo=False)

    cli._download_and_process_mineru_result(
        FakeClient(),
        FakeResult(),
        source=str(source),
        config=config,
        args=args,
        mode="hybrid",
        doc_name=None,
        task_ref={"task_id": "task-1", "batch_id": "batch-1"},
        progress=shared_logger,
    )

    per_doc_log = tmp_path / "out" / "notes" / "process.log"
    assert per_doc_log.exists()
    assert "文档结构已就绪：共 1 页" in per_doc_log.read_text(encoding="utf-8")
    assert "文档结构已就绪：共 1 页" in (tmp_path / "out" / "mineru_batch" / "process.log").read_text(encoding="utf-8")


def test_cli_chunk_merge_renumbers_relative_slides(tmp_path):
    output_dir = tmp_path / "out" / "Deck"
    chunk_dir = tmp_path / "out" / "Deck__chunk_002"
    (chunk_dir / "assets").mkdir(parents=True)
    (chunk_dir / "assets" / "crop.png").write_bytes(b"png")
    (chunk_dir / "ir").mkdir()
    (chunk_dir / "ir" / "page_001_ir.json").write_text("{}", encoding="utf-8")
    (chunk_dir / "mineru_raw").mkdir()
    (chunk_dir / "mineru_raw" / "layout.json").write_text("{}", encoding="utf-8")
    (chunk_dir / "Slide_01.md").write_text("# Slide 1\n\n![图](assets/crop.png)\n", encoding="utf-8")
    write_json(chunk_dir / "Slide_01.meta.json", {"slide_no": 1, "status": "ok"})
    write_json(
        chunk_dir / "run_report.json",
        {
            "doc_name": "Deck__chunk_002",
            "status": "ok",
            "models": {},
            "cost": {"estimated": None, "actual_tokens": None, "note": ""},
            "mineru": {},
            "pages": [
                {
                    "slide_no": 1,
                    "final": {"status": "ok", "included_in_full": True},
                    "validation": {"warnings": []},
                }
            ],
        },
    )
    chunks = build_page_chunks(401, chunk_size=200)

    cli._merge_chunk_outputs(
        output_dir,
        "Deck",
        [{"index": 2, "output_dir": str(chunk_dir)}],
        chunks,
        progress=None,
    )

    merged_slide = output_dir / "Slide_201.md"
    assert merged_slide.exists()
    text = merged_slide.read_text(encoding="utf-8")
    assert text.startswith("# Slide 201")
    assert "assets/chunk_002/crop.png" in text
    assert (output_dir / "assets" / "chunk_002" / "crop.png").exists()
    report = Path(output_dir / "run_report.json")
    assert report.exists()


def test_cli_resolves_mineru_folder_batch_inputs(tmp_path):
    keep_pdf = tmp_path / "a.pdf"
    keep_docx = tmp_path / "b.docx"
    ignore_txt = tmp_path / "c.txt"
    nested = tmp_path / "nested"
    nested.mkdir()
    nested_pdf = nested / "d.pdf"
    for path in (keep_pdf, keep_docx, ignore_txt, nested_pdf):
        path.write_bytes(b"x")

    non_recursive = cli.parse_args(["--input-folder", str(tmp_path)])
    recursive = cli.parse_args(["--input-folder", str(tmp_path), "--recursive"])

    assert [path.name for path in cli._resolve_mineru_local_files(non_recursive)] == ["a.pdf", "b.docx"]
    assert [path.name for path in cli._resolve_mineru_local_files(recursive)] == ["a.pdf", "b.docx", "d.pdf"]


def test_cli_rejects_unsupported_explicit_mineru_input(tmp_path):
    bad_file = tmp_path / "notes.txt"
    bad_file.write_text("not a MinerU document", encoding="utf-8")
    args = cli.parse_args(["--input-file", str(bad_file)])

    try:
        cli._resolve_mineru_local_files(args)
    except ValueError as exc:
        assert "Unsupported MinerU input file type" in str(exc)
    else:
        raise AssertionError("Expected unsupported explicit input to fail")


def test_cli_missing_mineru_token_returns_clean_error(monkeypatch, tmp_path, capsys):
    pdf = tmp_path / "notes.pdf"
    pdf.write_bytes(b"%PDF fake")
    monkeypatch.setattr("docpage2md_app.mineru_client.get_env_value", lambda _name: "")

    code = cli.main(["--engine-mode", "hybrid", "--input-file", str(pdf), "--output", str(tmp_path / "out")])

    captured = capsys.readouterr()
    assert code == 1
    assert "MinerU API 失败" in captured.out
    assert "MINERU_API_TOKEN" in captured.out
    assert "Traceback" not in captured.out
    assert "Traceback" not in captured.err


def test_cli_missing_paddleocr_artifact_returns_clean_error(tmp_path, capsys):
    missing = tmp_path / "missing_artifact"

    code = cli.main(
        [
            "--engine-mode",
            "paddleocr_only",
            "--paddleocr-artifact-dir",
            str(missing),
            "--output",
            str(tmp_path / "out"),
        ]
    )

    captured = capsys.readouterr()
    assert code == 1
    assert "PaddleOCR artifact 处理失败" in captured.out
    assert "Traceback" not in captured.out
    assert "Traceback" not in captured.err


def test_interactive_default_starts_with_hybrid_mineru_pdf(monkeypatch):
    args = cli.parse_args([])
    responses = iter(["", "", "", "", "notes.pdf", "1-5"])

    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(responses))

    updated = cli._maybe_prompt_initial_mode(args)

    assert updated.document_type == "handwritten_notes"
    assert updated.engine_mode == "hybrid"
    assert updated.model_profile == "balanced"
    assert updated.input_file == "notes.pdf"
    assert updated.page_ranges == "1-5"
