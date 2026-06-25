import sys
from pathlib import Path

import pytest

from docpage2md_app.gui import (
    DocPage2MdGui,
    describe_input_files,
    effective_mineru_model_version,
    GuiProgressTracker,
    GuiRunOptions,
    SelectedModel,
    build_cli_argv,
    build_process_command,
    count_page_ranges,
    estimate_gui_cost,
    estimate_pdf_pages,
    split_multi_paths,
    translate_log_line,
    missing_model_key_messages,
    validate_selected_models,
)
from docpage2md_app.input_inspection import build_page_chunks


def test_gui_builds_single_file_hybrid_command(tmp_path):
    pdf = tmp_path / "notes.pdf"
    pdf.write_bytes(b"%PDF")
    options = GuiRunOptions(
        document_type="handwritten_notes",
        engine_mode="hybrid",
        model_profile="balanced",
        source_kind="input_file",
        source_value=str(pdf),
        output_folder=str(tmp_path / "out"),
        page_ranges="1 - 5",
    )

    argv = build_cli_argv(options)

    assert argv[argv.index("--engine-mode") + 1] == "hybrid"
    assert argv[argv.index("--document-type") + 1] == "handwritten_notes"
    assert argv[argv.index("--model-profile") + 1] == "balanced"
    assert argv[argv.index("--output") + 1] == str(tmp_path / "out")
    assert argv[argv.index("--page-ranges") + 1] == "1-5"
    assert argv[argv.index("--mineru-model-version") + 1] == "vlm"
    assert argv[argv.index("--mineru-is-ocr") + 1] == "true"
    assert argv[argv.index("--mineru-enable-formula") + 1] == "true"
    assert argv[argv.index("--mineru-enable-table") + 1] == "true"
    assert argv[argv.index("--mineru-language") + 1] == "ch"
    assert argv[argv.index("--vision-workers") + 1] == "60"
    assert argv[argv.index("--brain-workers") + 1] == "60"
    assert argv[-2:] == [
        "--input-file",
        str(pdf),
    ]


def test_gui_builds_dual_hybrid_command(tmp_path):
    pdf = tmp_path / "notes.pdf"
    pdf.write_bytes(b"%PDF")
    options = GuiRunOptions(
        layout_engine="MinerU + PaddleOCR 双引擎融合",
        refine_mode="开启 DocPage2MD 精修",
        source_kind="input_file",
        source_value=str(pdf),
        output_folder=str(tmp_path / "out"),
    )

    argv = build_cli_argv(options)

    assert argv[argv.index("--engine-mode") + 1] == "dual_hybrid"
    assert argv[argv.index("--layout-engine") + 1] == "dual"
    assert argv[argv.index("--refine-mode") + 1] == "docpage2md"
    assert argv[-2:] == ["--input-file", str(pdf)]


def test_gui_builds_multi_file_command(tmp_path):
    first = tmp_path / "a.pdf"
    second = tmp_path / "b.pptx"
    options = GuiRunOptions(
        engine_mode="mineru_only",
        source_kind="input_files",
        source_value=f'"{first}"; {second}',
        output_folder=str(tmp_path / "out"),
    )

    argv = build_cli_argv(options)

    assert argv[-3:] == ["--input-files", str(first), str(second)]


def test_gui_accepts_display_labels_for_document_and_source(tmp_path):
    first = tmp_path / "a.pdf"
    second = tmp_path / "b.pdf"
    options = GuiRunOptions(
        document_type="手写矢量笔记",
        source_kind="本地多个文件",
        source_value=f"{first};{second}",
        output_folder=str(tmp_path / "out"),
    )

    argv = build_cli_argv(options)

    assert argv[argv.index("--document-type") + 1] == "handwritten_notes"
    assert argv[-3:] == ["--input-files", str(first), str(second)]


def test_gui_accepts_chinese_engine_and_profile_labels(tmp_path):
    pdf = tmp_path / "notes.pdf"
    pdf.write_bytes(b"%PDF")
    options = GuiRunOptions(
        document_type="手写矢量笔记",
        engine_mode="混合精修（推荐）",
        model_profile="均衡（推荐）",
        source_kind="本地单个文件",
        source_value=str(pdf),
        output_folder=str(tmp_path / "out"),
    )

    argv = build_cli_argv(options)

    assert argv[argv.index("--engine-mode") + 1] == "hybrid"
    assert argv[argv.index("--model-profile") + 1] == "balanced"


def test_gui_builds_recursive_folder_command(tmp_path):
    options = GuiRunOptions(
        source_kind="input_folder",
        source_value=str(tmp_path),
        output_folder=str(tmp_path / "out"),
        recursive=True,
    )

    argv = build_cli_argv(options)

    assert argv[-3:] == ["--input-folder", str(tmp_path), "--recursive"]


def test_gui_builds_artifact_command(tmp_path):
    options = GuiRunOptions(
        source_kind="mineru_artifact_dir",
        source_value=str(tmp_path),
        output_folder=str(tmp_path / "out"),
    )

    argv = build_cli_argv(options)

    assert argv[-2:] == ["--mineru-artifact-dir", str(tmp_path)]


def test_gui_builds_url_command(tmp_path):
    options = GuiRunOptions(
        source_kind="mineru_url",
        source_value="https://example.com/notes.pdf",
        output_folder=str(tmp_path / "out"),
    )

    argv = build_cli_argv(options)

    assert argv[-2:] == ["--mineru-url", "https://example.com/notes.pdf"]


def test_gui_rejects_bad_page_range(tmp_path):
    options = GuiRunOptions(source_kind="mineru_url", source_value="https://example.com/a.pdf", page_ranges="1--")

    with pytest.raises(ValueError, match="页码范围"):
        build_cli_argv(options)


def test_gui_rejects_vision_only_for_subprocess_flow():
    options = GuiRunOptions(engine_mode="vision_only", source_value="notes.pdf")

    with pytest.raises(ValueError, match="vision_only"):
        build_cli_argv(options)


def test_gui_adds_model_override_args(tmp_path):
    options = GuiRunOptions(
        source_value="https://example.com/notes.pdf",
        source_kind="mineru_url",
        output_folder=str(tmp_path / "out"),
        vision=SelectedModel("openai_compatible", "vision-model", "https://vision.example/v1", "VISION_KEY"),
        brain=SelectedModel("deepseek", "deepseek-v4-pro", "https://api.deepseek.com", "DEEPSEEK_API_KEY"),
    )

    argv = build_cli_argv(options)

    assert "--vision-provider" in argv
    assert argv[argv.index("--vision-model") + 1] == "vision-model"
    assert argv[argv.index("--brain-model") + 1] == "deepseek-v4-pro"


def test_gui_adds_worker_override_args(tmp_path):
    options = GuiRunOptions(
        source_value="https://example.com/notes.pdf",
        source_kind="mineru_url",
        output_folder=str(tmp_path / "out"),
        vision_workers="70",
        brain_workers=65,
    )

    argv = build_cli_argv(options)

    assert argv[argv.index("--vision-workers") + 1] == "70"
    assert argv[argv.index("--brain-workers") + 1] == "65"


def test_gui_adds_mineru_advanced_args(tmp_path):
    options = GuiRunOptions(
        source_value="https://example.com/notes.pdf",
        source_kind="mineru_url",
        output_folder=str(tmp_path / "out"),
        mineru_is_ocr=False,
        mineru_enable_formula=True,
        mineru_enable_table=False,
        mineru_language="en",
        mineru_page_chunk_size="150",
    )

    argv = build_cli_argv(options)

    assert argv[argv.index("--mineru-is-ocr") + 1] == "false"
    assert argv[argv.index("--mineru-enable-formula") + 1] == "true"
    assert argv[argv.index("--mineru-enable-table") + 1] == "false"
    assert argv[argv.index("--mineru-language") + 1] == "en"
    assert argv[argv.index("--mineru-page-chunk-size") + 1] == "150"


def test_gui_html_input_auto_uses_mineru_html(tmp_path):
    html = tmp_path / "page.html"
    html.write_text("<html></html>", encoding="utf-8")
    options = GuiRunOptions(source_kind="input_file", source_value=str(html), output_folder=str(tmp_path / "out"))

    assert effective_mineru_model_version(options) == "MinerU-HTML"
    argv = build_cli_argv(options)
    assert argv[argv.index("--mineru-model-version") + 1] == "MinerU-HTML"


def test_gui_rejects_non_html_with_mineru_html(tmp_path):
    pdf = tmp_path / "notes.pdf"
    pdf.write_bytes(b"%PDF")
    options = GuiRunOptions(
        source_kind="input_file",
        source_value=str(pdf),
        mineru_model_version="MinerU-HTML",
        output_folder=str(tmp_path / "out"),
    )

    with pytest.raises(ValueError, match="MinerU-HTML"):
        build_cli_argv(options)


def test_gui_page_chunk_ranges_for_401_pages():
    chunks = build_page_chunks(401, chunk_size=200)

    assert [chunk.page_ranges for chunk in chunks] == ["1-200", "201-400", "401-401"]
    assert [chunk.page_count for chunk in chunks] == [200, 200, 1]


def test_gui_input_description_marks_over_limit_pdf(tmp_path):
    pdf = tmp_path / "big.pdf"
    pdf.write_bytes(b"%PDF\n" + b"\n".join([b"<< /Type /Page >>"] * 201))

    infos = describe_input_files([pdf])

    assert infos[0].pages == 201
    assert "分" in infos[0].limit_status


def test_gui_model_validation_rejects_incomplete_vision_model():
    issues = validate_selected_models(
        vision=SelectedModel("deepseek", "", "", ""),
        brain=SelectedModel("deepseek", "deepseek-v4-flash", "https://api.deepseek.com", "DEEPSEEK_API_KEY"),
    )

    assert any("Vision 模型 ID" in issue for issue in issues)
    assert any("Vision Key 环境变量名" in issue for issue in issues)
    assert any("Vision 不能使用 DeepSeek" in issue for issue in issues)


def test_gui_model_validation_accepts_complete_manual_models():
    issues = validate_selected_models(
        vision=SelectedModel("openai_compatible", "vendor/vision", "https://vendor.example/v1", "VISION_KEY"),
        brain=SelectedModel("openai_compatible", "vendor/brain", "https://vendor.example/v1", "BRAIN_KEY"),
    )

    assert issues == []


def test_gui_missing_model_key_messages_dedupes_env_names(monkeypatch):
    monkeypatch.delenv("SAME_KEY", raising=False)

    messages = missing_model_key_messages(
        vision=SelectedModel("openai_compatible", "vendor/vision", "https://vendor.example/v1", "SAME_KEY"),
        brain=SelectedModel("openai_compatible", "vendor/brain", "https://vendor.example/v1", "SAME_KEY"),
    )

    assert messages == ["Vision 需要环境变量 SAME_KEY，当前未检测到。"]


def test_gui_rejects_bad_worker_count():
    options = GuiRunOptions(source_kind="mineru_url", source_value="https://example.com/a.pdf", vision_workers="0")

    with pytest.raises(ValueError, match="Vision 并发数"):
        build_cli_argv(options)


def test_gui_build_process_command_uses_repo_script(tmp_path):
    options = GuiRunOptions(source_value="https://example.com/notes.pdf", source_kind="mineru_url")

    command = build_process_command(options, tmp_path)

    assert command[:2] == [sys.executable, str(Path(tmp_path) / "docpage2md.py")]
    assert command[-2:] == ["--mineru-url", "https://example.com/notes.pdf"]


def test_split_multi_paths_trims_quotes():
    assert split_multi_paths('"a.pdf"; b.docx; ') == ["a.pdf", "b.docx"]


def test_count_page_ranges_respects_total_pages():
    assert count_page_ranges("", 12) == 12
    assert count_page_ranges("1-3, 3, 10-20", 12) == 6
    assert count_page_ranges("5-3", 12) is None


def test_estimate_pdf_pages_from_pdf_markers(tmp_path):
    pdf = tmp_path / "sample.pdf"
    pdf.write_bytes(b"%PDF\n1 0 obj << /Type /Page >>\n2 0 obj << /Type /Pages >>\n3 0 obj << /Type /Page >>")

    assert estimate_pdf_pages(pdf) == 2


def test_gui_cost_estimate_for_local_pdf_is_visible(tmp_path):
    pdf = tmp_path / "sample.pdf"
    pdf.write_bytes(
        b"%PDF\n"
        b"1 0 obj << /Type /Page >>\n"
        b"2 0 obj << /Type /Page >>\n"
        b"3 0 obj << /Type /Pages >>"
    )
    options = GuiRunOptions(
        source_kind="input_file",
        source_value=str(pdf),
        output_folder=str(tmp_path / "out"),
    )

    summary = estimate_gui_cost(options)

    assert summary.total_pages == 2
    assert summary.total_input_tokens > 0
    assert summary.total_output_tokens > 0
    assert summary.total_cost is not None
    assert summary.confidence == "中"
    assert "MinerU 解析前" in summary.rows[0].note


def test_gui_cost_estimate_for_local_image_uses_real_dimensions(tmp_path):
    pytest.importorskip("PIL")
    from PIL import Image

    image = tmp_path / "page.png"
    Image.new("RGB", (100, 100), "white").save(image)
    options = GuiRunOptions(
        source_kind="input_file",
        source_value=str(image),
        output_folder=str(tmp_path / "out"),
    )

    summary = estimate_gui_cost(options)

    assert summary.total_pages == 1
    assert summary.rows[0].crop_blocks == 1
    assert summary.rows[0].input_tokens >= 11
    assert "原图尺寸" in summary.rows[0].note


def test_gui_cost_estimate_for_artifact_mentions_deepseek_tokenizer():
    fixture = Path(__file__).parent / "fixtures" / "mineru_public" / "minimal_artifact"
    options = GuiRunOptions(
        source_kind="mineru_artifact_dir",
        source_value=str(fixture),
        output_folder="unused",
    )

    summary = estimate_gui_cost(options)

    assert summary.confidence == "高"
    assert summary.rows[0].input_tokens > 0
    assert "DeepSeek 输入 token 使用内置 tokenizer" in summary.rows[0].note


def test_gui_cost_estimate_for_mineru_only_is_zero(tmp_path):
    pdf = tmp_path / "sample.pdf"
    pdf.write_bytes(b"%PDF\n1 0 obj << /Type /Page >>")
    options = GuiRunOptions(
        engine_mode="仅 MinerU 解析（最快）",
        source_kind="input_file",
        source_value=str(pdf),
        output_folder=str(tmp_path / "out"),
    )

    summary = estimate_gui_cost(options)

    assert summary.total_cost == 0
    assert summary.total_input_tokens == 0
    assert "不会调用 Vision/Brain" in summary.note


def test_gui_log_translation_uses_chinese_progress_text():
    line = "2026-06-24 18:44:04 +   24.6s | Hybrid crop vision batch start: blocks=12, workers=6\n"

    translated = translate_log_line(line)

    assert "开始并行识别裁剪块" in translated
    assert "裁剪块=12" in translated
    assert "workers" not in translated


def test_gui_log_translation_covers_mineru_chunking():
    line = "2026-06-24 18:44:04 +   24.6s | MinerU chunk 2/3 submit: page_ranges=201-400, pages=200\n"

    translated = translate_log_line(line)

    assert "正在提交 MinerU 分段" in translated
    assert "页码=201-400" in translated


def test_progress_tracker_updates_from_hybrid_log_lines(tmp_path):
    first = tmp_path / "a.pdf"
    second = tmp_path / "b.pdf"
    first.write_bytes(b"%PDF\n1 0 obj << /Type /Page >>\n2 0 obj << /Type /Page >>")
    second.write_bytes(b"%PDF\n1 0 obj << /Type /Page >>")
    options = GuiRunOptions(
        source_kind="input_files",
        source_value=f"{first};{second}",
        output_folder=str(tmp_path / "out"),
    )
    tracker = GuiProgressTracker()

    snapshot = tracker.reset(options)
    assert snapshot.percent == 0
    assert "3 页" in snapshot.detail

    tracker.observe_line("2026-06-24 18:44:04 +   24.6s | DocumentIR ready: pages=2, blocks=10")
    tracker.observe_line("2026-06-24 18:44:04 +   24.8s | Hybrid page 1/2 start: slide=1, blocks=5")
    tracker.observe_line("2026-06-24 18:45:04 +   84.8s | Hybrid page 1 refiner done: changed=False, applied=0, dismissed=0")
    snapshot = tracker.observe_line("2026-06-24 18:45:04 +   84.9s | Hybrid page 2/2 start: slide=2, blocks=5")

    assert snapshot.percent == pytest.approx(100 / 3)
    assert snapshot.eta.startswith("剩余 ")
    assert snapshot.eta != "剩余 --"


def test_progress_tracker_updates_from_chinese_log_lines(tmp_path):
    pdf = tmp_path / "a.pdf"
    pdf.write_bytes(b"%PDF\n1 0 obj << /Type /Page >>\n2 0 obj << /Type /Page >>")
    options = GuiRunOptions(
        source_kind="input_file",
        source_value=str(pdf),
        output_folder=str(tmp_path / "out"),
    )
    tracker = GuiProgressTracker()
    tracker.reset(options)

    tracker.observe_line("2026-06-24 18:44:04 +   10.0s | 文档结构已就绪：共 2 页，块数=10")
    tracker.observe_line("2026-06-24 18:44:05 +   11.0s | 准备第 1/2 页精修：slide=1, blocks=5")
    snapshot = tracker.observe_line("2026-06-24 18:45:05 +   71.0s | 校验器完成第 1 页：是否改动=否，应用=0，拒绝=0")

    assert snapshot.percent == pytest.approx(50.0)
    assert snapshot.stage == "第 1/2 页完成"
    assert snapshot.eta.startswith("剩余 ")


def test_progress_tracker_finish_sets_complete_percent():
    tracker = GuiProgressTracker()
    tracker.reset(GuiRunOptions(source_kind="mineru_url", source_value="https://example.com/a.pdf"))

    snapshot = tracker.finish(True)

    assert snapshot.percent == 100
    assert snapshot.stage == "完成"
    assert snapshot.eta == "剩余 00:00"


def test_gui_constructs_and_destroy_cancels_after_callbacks():
    try:
        app = DocPage2MdGui()
    except Exception as exc:
        if exc.__class__.__name__ == "TclError":
            pytest.skip(f"Tkinter display unavailable: {exc}")
        raise
    try:
        app.root.withdraw()
        app.root.update_idletasks()
        assert app.run_canvas.winfo_exists()
        assert app.command_preview_entry.cget("xscrollcommand")
        assert app.cost_tree.cget("xscrollcommand")
    finally:
        app.destroy()
    assert app._drain_after_id is None
