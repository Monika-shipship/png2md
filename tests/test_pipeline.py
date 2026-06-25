from docpage2md_app.config import AppConfig
from docpage2md_app.artifacts import build_slide_meta
from docpage2md_app.files import read_json, write_json
from docpage2md_app.ir import build_page_ir
from docpage2md_app.reporting import build_run_report
from docpage2md_app import pipeline


class DummyQueue:
    def __init__(self):
        self.items = []

    def put(self, item):
        self.items.append(item)


FORBIDDEN_USER_MARKDOWN_FRAGMENTS = (
    "> [!WARNING]",
    "Stage 2 重组失败",
    "原因：",
    "质量警告",
    "原始识别：",
    "原始识别已按纯文本保留",
    "原文勘误",
    "思考过程",
    "错误过程",
    "注：手写看似",
    "OCR 正文覆盖率",
    "覆盖率偏低",
)


def assert_clean_user_markdown(markdown: str):
    for fragment in FORBIDDEN_USER_MARKDOWN_FRAGMENTS:
        assert fragment not in markdown


def test_vision_stage_rejects_legacy_cache_and_rewrites_v1(monkeypatch, tmp_path):
    image = tmp_path / "page.png"
    image.write_bytes(b"fake image")
    temp_dir = tmp_path / "temp_raw_vision"
    temp_dir.mkdir()
    write_json(temp_dir / "Raw_01.json", {"success": True, "slide_no": 1, "raw_text": "legacy"})
    config = AppConfig(vision_batch_workers=1)
    report, page_reports = build_run_report("Deck", [str(image)], 0, config)

    calls = {"count": 0}

    def fake_stage1(img_path, slide_no, doc_name, msg_queue, config):
        calls["count"] += 1
        return {"success": True, "slide_no": slide_no, "raw_text": "fresh raw"}

    monkeypatch.setattr(pipeline, "run_stage_1_vision", fake_stage1)

    raw_data, blocks_by_slide = pipeline._run_vision_stage("Deck", [str(image)], 0, temp_dir, 1, DummyQueue(), config, page_reports)

    assert calls["count"] == 1
    assert raw_data == {1: "fresh raw"}
    assert blocks_by_slide[1]
    rewritten = read_json(temp_dir / "Raw_01.json")
    assert rewritten["schema_version"] == 1
    assert page_reports[1]["stage1"]["cache"] == "legacy_miss"
    assert report["pages"][0]["stage1"]["status"] == "ok"


def test_brain_stage_error_does_not_write_normal_markdown(monkeypatch, tmp_path):
    config = AppConfig(brain_batch_workers=1)
    report, page_reports = build_run_report("Deck", [str(tmp_path / "page.png")], 0, config)
    page_reports[1]["stage1"]["status"] = "ok"
    raw_data_map = {1: "raw text"}

    monkeypatch.setattr(
        pipeline,
        "run_stage_2_brain_parallel",
        lambda slide_no, raw_data_map, config: {
            "success": False,
            "slide_no": slide_no,
            "error": "Brain Error: 500",
            "error_code": "Brain Error",
            "raw_response": "Brain Error: 500",
        },
    )

    ok_slides = pipeline._run_brain_stage("Deck", 1, 0, tmp_path, raw_data_map, 1, DummyQueue(), config, page_reports)

    assert ok_slides == []
    assert not (tmp_path / "Slide_01.md").exists()
    assert (tmp_path / "Slide_01.error.json").exists()
    assert read_json(tmp_path / "Slide_01.meta.json")["status"] == "failed"
    assert page_reports[1]["final"]["status"] == "failed"
    assert page_reports[1]["suspects"][0]["code"] == "Brain Error"
    assert page_reports[1]["suspects"][0]["op_hint"] == "mark_failed_page"


def test_brain_stage_error_writes_markdown_fail_open_when_stage1_blocks_exist(monkeypatch, tmp_path):
    config = AppConfig(brain_batch_workers=1)
    report, page_reports = build_run_report("Deck", [str(tmp_path / "page.png")], 0, config)
    page_reports[1]["stage1"]["status"] = "ok"
    raw_data_map = {1: "热力学第一定律描述内能、热量和功之间的关系。"}
    target_blocks = {
        1: [
            {
                "id": "p0001-b001",
                "type": "paragraph",
                "text": raw_data_map[1],
                "source_page": 1,
                "confidence": 0.8,
                "origin": "vision_ocr",
                "evidence": {"raw_text": raw_data_map[1]},
                "bbox": None,
            }
        ]
    }

    monkeypatch.setattr(
        pipeline,
        "run_stage_2_brain_parallel",
        lambda slide_no, raw_data_map, config: {
            "success": False,
            "slide_no": slide_no,
            "error": "Brain Error: 500",
            "error_code": "Brain Error",
            "raw_response": "Brain Error: 500",
        },
    )

    ok_slides = pipeline._run_brain_stage(
        "Deck",
        1,
        0,
        tmp_path,
        raw_data_map,
        1,
        DummyQueue(),
        config,
        page_reports,
        target_blocks_by_slide=target_blocks,
    )

    assert ok_slides == [1]
    markdown = (tmp_path / "Slide_01.md").read_text(encoding="utf-8")
    assert markdown.startswith("# Slide 1\n\n热力学第一定律")
    assert_clean_user_markdown(markdown)
    assert "热力学第一定律" in markdown
    meta = read_json(tmp_path / "Slide_01.meta.json")
    assert meta["status"] == "fail_open"
    assert meta["fallback"]["source"] == "stage1_page_ir"
    assert page_reports[1]["final"]["status"] == "fail_open"
    assert page_reports[1]["stage2"]["status"] == "failed"
    assert page_reports[1]["stage2"]["fallback"] == "stage1_page_ir"


def test_brain_stage_low_ocr_coverage_uses_markdown_fail_open(monkeypatch, tmp_path):
    config = AppConfig(brain_batch_workers=1)
    report, page_reports = build_run_report("Deck", [str(tmp_path / "page.png")], 0, config)
    page_reports[1]["stage1"]["status"] = "ok"
    raw_data_map = {
        1: "热力学第一定律描述内能、热量和功之间的关系。孤立系统的总能量保持守恒，系统状态变化时需要同时考虑做功和吸热。"
    }
    target_blocks = {
        1: [
            {
                "id": "p0001-b001",
                "type": "paragraph",
                "text": raw_data_map[1],
                "source_page": 1,
                "confidence": 0.8,
                "origin": "vision_ocr",
                "evidence": {"raw_text": raw_data_map[1]},
                "bbox": None,
            }
        ]
    }

    monkeypatch.setattr(
        pipeline,
        "run_stage_2_brain_parallel",
        lambda slide_no, raw_data_map, config: {
            "success": True,
            "slide_no": slide_no,
            "markdown": "# Slide 1\n\n简短摘要。\n",
            "raw_response": "# Slide 1\n\n简短摘要。\n",
        },
    )

    ok_slides = pipeline._run_brain_stage(
        "Deck",
        1,
        0,
        tmp_path,
        raw_data_map,
        1,
        DummyQueue(),
        config,
        page_reports,
        target_blocks_by_slide=target_blocks,
    )

    assert ok_slides == [1]
    markdown = (tmp_path / "Slide_01.md").read_text(encoding="utf-8")
    meta = read_json(tmp_path / "Slide_01.meta.json")
    assert_clean_user_markdown(markdown)
    assert "热力学第一定律" in markdown
    assert "简短摘要" not in markdown
    assert meta["status"] == "fail_open"
    assert meta["error"]["code"] == "ocr_coverage_low"
    assert page_reports[1]["final"]["status"] == "fail_open"
    assert page_reports[1]["stage2"]["error_code"] == "ocr_coverage_low"


def test_brain_stage_missing_figure_note_uses_markdown_fail_open(monkeypatch, tmp_path):
    config = AppConfig(brain_batch_workers=1)
    report, page_reports = build_run_report("Deck", [str(tmp_path / "page.png")], 0, config)
    page_reports[1]["stage1"]["status"] = "ok"
    raw_data_map = {1: "### Figure Analysis\n左侧是 A，右侧是 B，中间有箭头连接。"}
    target_blocks = {
        1: [
            {
                "id": "p0001-b001",
                "type": "figure_note",
                "text": "左侧是 A，右侧是 B，中间有箭头连接。",
                "description": "左侧是 A，右侧是 B，中间有箭头连接。",
                "source_page": 1,
                "confidence": 0.72,
                "origin": "vision_description",
                "evidence": {"raw_text": raw_data_map[1]},
                "bbox": None,
                "unrecognizable": False,
            }
        ]
    }

    monkeypatch.setattr(
        pipeline,
        "run_stage_2_brain_parallel",
        lambda slide_no, raw_data_map, config: {
            "success": True,
            "slide_no": slide_no,
            "markdown": "# Slide 1\n\n图中有两个对象。\n",
            "raw_response": "# Slide 1\n\n图中有两个对象。\n",
        },
    )

    ok_slides = pipeline._run_brain_stage(
        "Deck",
        1,
        0,
        tmp_path,
        raw_data_map,
        1,
        DummyQueue(),
        config,
        page_reports,
        target_blocks_by_slide=target_blocks,
    )

    markdown = (tmp_path / "Slide_01.md").read_text(encoding="utf-8")
    meta = read_json(tmp_path / "Slide_01.meta.json")
    assert ok_slides == [1]
    assert meta["status"] == "fail_open"
    assert meta["error"]["code"] == "figure_note_missing"
    assert "<summary>图示识别内容</summary>" in markdown
    assert "左侧是 A，右侧是 B" in markdown


def test_brain_stage_missing_target_figure_block_uses_page_ir_fallback(monkeypatch, tmp_path):
    config = AppConfig(brain_batch_workers=1)
    report, page_reports = build_run_report("Deck", [str(tmp_path / "page.png")], 0, config)
    page_reports[1]["stage1"]["status"] = "ok"
    raw_data_map = {1: "### Figure Analysis\n坐标图中横轴为 t，纵轴为 v，曲线逐渐上升。"}
    target_blocks = {1: build_page_ir(raw_data_map[1], 1)["blocks"]}

    monkeypatch.setattr(
        pipeline,
        "run_stage_2_brain_parallel",
        lambda slide_no, raw_data_map, config: {
            "success": True,
            "slide_no": slide_no,
            "markdown": "# Slide 1\n\n图中有一条曲线。\n",
            "raw_response": "# Slide 1\n\n图中有一条曲线。\n",
        },
    )

    ok_slides = pipeline._run_brain_stage(
        "Deck",
        1,
        0,
        tmp_path,
        raw_data_map,
        1,
        DummyQueue(),
        config,
        page_reports,
        target_blocks_by_slide=target_blocks,
    )

    markdown = (tmp_path / "Slide_01.md").read_text(encoding="utf-8")
    meta = read_json(tmp_path / "Slide_01.meta.json")
    assert ok_slides == [1]
    assert meta["status"] == "fail_open"
    assert meta["error"]["code"] in {"figure_note_missing", "target_figure_block_missing"}
    assert "<summary>图示识别内容</summary>" in markdown
    assert "坐标图中横轴为 t，纵轴为 v，曲线逐渐上升" in markdown


def test_brain_stage_bad_table_uses_markdown_fail_open(monkeypatch, tmp_path):
    config = AppConfig(brain_batch_workers=1)
    report, page_reports = build_run_report("Deck", [str(tmp_path / "page.png")], 0, config)
    page_reports[1]["stage1"]["status"] = "ok"
    raw_data_map = {1: "### Table Analysis\n| 量 | 值 |\n| --- | --- |\n| 力 | N |"}
    target_blocks = {
        1: [
            {
                "id": "p0001-b001",
                "type": "table",
                "text": "| 量 | 值 |\n| --- | --- |\n| 力 | N |",
                "source_page": 1,
                "confidence": 0.72,
                "origin": "vision_table",
                "evidence": {"raw_text": raw_data_map[1]},
                "bbox": None,
            }
        ]
    }

    monkeypatch.setattr(
        pipeline,
        "run_stage_2_brain_parallel",
        lambda slide_no, raw_data_map, config: {
            "success": True,
            "slide_no": slide_no,
            "markdown": "# Slide 1\n\n| 量 | 值 |\n| --- | --- |\n| 力 | N | extra |\n",
            "raw_response": "# Slide 1\n\n| 量 | 值 |\n| --- | --- |\n| 力 | N | extra |\n",
        },
    )

    ok_slides = pipeline._run_brain_stage(
        "Deck",
        1,
        0,
        tmp_path,
        raw_data_map,
        1,
        DummyQueue(),
        config,
        page_reports,
        target_blocks_by_slide=target_blocks,
    )

    markdown = (tmp_path / "Slide_01.md").read_text(encoding="utf-8")
    meta = read_json(tmp_path / "Slide_01.meta.json")
    assert ok_slides == [1]
    assert meta["status"] == "fail_open"
    assert meta["error"]["code"] == "table_structure_warning"
    assert "| 力 | N |" in markdown
    assert "extra" not in markdown


def test_brain_stage_missing_target_table_block_uses_page_ir_fallback(monkeypatch, tmp_path):
    config = AppConfig(brain_batch_workers=1)
    report, page_reports = build_run_report("Deck", [str(tmp_path / "page.png")], 0, config)
    page_reports[1]["stage1"]["status"] = "ok"
    raw_data_map = {1: "### Table Analysis\n| 量 | 值 |\n| --- | --- |\n| 力 | N |"}
    target_blocks = {1: build_page_ir(raw_data_map[1], 1)["blocks"]}

    monkeypatch.setattr(
        pipeline,
        "run_stage_2_brain_parallel",
        lambda slide_no, raw_data_map, config: {
            "success": True,
            "slide_no": slide_no,
            "markdown": "# Slide 1\n\n本页给出物理量表。\n",
            "raw_response": "# Slide 1\n\n本页给出物理量表。\n",
        },
    )

    ok_slides = pipeline._run_brain_stage(
        "Deck",
        1,
        0,
        tmp_path,
        raw_data_map,
        1,
        DummyQueue(),
        config,
        page_reports,
        target_blocks_by_slide=target_blocks,
    )

    markdown = (tmp_path / "Slide_01.md").read_text(encoding="utf-8")
    meta = read_json(tmp_path / "Slide_01.meta.json")
    assert ok_slides == [1]
    assert meta["status"] == "fail_open"
    assert meta["error"]["code"] == "target_table_block_missing"
    assert "| 量 | 值 |" in markdown
    assert "| 力 | N |" in markdown
    assert "本页给出物理量表" not in markdown


def test_brain_stage_missing_target_uncertain_block_uses_page_ir_fallback(monkeypatch, tmp_path):
    config = AppConfig(brain_batch_workers=1)
    report, page_reports = build_run_report("Deck", [str(tmp_path / "page.png")], 0, config)
    page_reports[1]["stage1"]["status"] = "ok"
    raw_data_map = {1: "### Uncertain\n此处手写文字疑似为配分函数，但无法确定。"}
    target_blocks = {1: build_page_ir(raw_data_map[1], 1)["blocks"]}

    monkeypatch.setattr(
        pipeline,
        "run_stage_2_brain_parallel",
        lambda slide_no, raw_data_map, config: {
            "success": True,
            "slide_no": slide_no,
            "markdown": "# Slide 1\n\n正文整理完成。\n",
            "raw_response": "# Slide 1\n\n正文整理完成。\n",
        },
    )

    ok_slides = pipeline._run_brain_stage(
        "Deck",
        1,
        0,
        tmp_path,
        raw_data_map,
        1,
        DummyQueue(),
        config,
        page_reports,
        target_blocks_by_slide=target_blocks,
    )

    markdown = (tmp_path / "Slide_01.md").read_text(encoding="utf-8")
    meta = read_json(tmp_path / "Slide_01.meta.json")
    assert ok_slides == [1]
    assert meta["status"] == "fail_open"
    assert meta["error"]["code"] == "target_uncertain_block_missing"
    assert_clean_user_markdown(markdown)
    assert "此处手写文字疑似为配分函数" in markdown


def test_brain_stage_bad_formula_falls_back_when_page_ir_is_clean(monkeypatch, tmp_path):
    config = AppConfig(brain_batch_workers=1)
    report, page_reports = build_run_report("Deck", [str(tmp_path / "page.png")], 0, config)
    page_reports[1]["stage1"]["status"] = "ok"
    raw_data_map = {1: "### Formula\nE = mc^2"}
    target_blocks = {1: build_page_ir(raw_data_map[1], 1)["blocks"]}

    monkeypatch.setattr(
        pipeline,
        "run_stage_2_brain_parallel",
        lambda slide_no, raw_data_map, config: {
            "success": True,
            "slide_no": slide_no,
            "markdown": "# Slide 1\n\n$$\n\\frac a}{b\n$$\n",
            "raw_response": "# Slide 1\n\n$$\n\\frac a}{b\n$$\n",
        },
    )

    ok_slides = pipeline._run_brain_stage(
        "Deck",
        1,
        0,
        tmp_path,
        raw_data_map,
        1,
        DummyQueue(),
        config,
        page_reports,
        target_blocks_by_slide=target_blocks,
    )

    markdown = (tmp_path / "Slide_01.md").read_text(encoding="utf-8")
    meta = read_json(tmp_path / "Slide_01.meta.json")
    assert ok_slides == [1]
    assert meta["status"] == "fail_open"
    assert meta["error"]["code"] in {"formula_brace_unbalanced", "latex_frac_missing_braces"}
    assert "$$\nE = mc^2\n$$" in markdown
    assert "$$\n\\frac a}{b\n$$" not in markdown


def test_brain_stage_unicode_math_symbols_fall_back_to_latex_page_ir(monkeypatch, tmp_path):
    config = AppConfig(brain_batch_workers=1)
    report, page_reports = build_run_report("Deck", [str(tmp_path / "page.png")], 0, config)
    page_reports[1]["stage1"]["status"] = "ok"
    raw_data_map = {1: "令 φ, θ, ω 为三个角，满足 α+β=γ。"}
    target_blocks = {1: build_page_ir(raw_data_map[1], 1)["blocks"]}

    monkeypatch.setattr(
        pipeline,
        "run_stage_2_brain_parallel",
        lambda slide_no, raw_data_map, config: {
            "success": True,
            "slide_no": slide_no,
            "markdown": "# Slide 1\n\n令 φ, θ, ω 为三个角，满足 α+β=γ。\n",
            "raw_response": "# Slide 1\n\n令 φ, θ, ω 为三个角，满足 α+β=γ。\n",
        },
    )

    ok_slides = pipeline._run_brain_stage(
        "Deck",
        1,
        0,
        tmp_path,
        raw_data_map,
        1,
        DummyQueue(),
        config,
        page_reports,
        target_blocks_by_slide=target_blocks,
    )

    markdown = (tmp_path / "Slide_01.md").read_text(encoding="utf-8")
    meta = read_json(tmp_path / "Slide_01.meta.json")
    assert ok_slides == [1]
    assert meta["status"] == "ok"
    assert "$\\phi, \\theta, \\omega$" in markdown
    assert "$\\alpha + \\beta = \\gamma$" in markdown
    assert "φ" not in markdown
    assert "θ" not in markdown
    assert "ω" not in markdown


def test_stage2_warning_fallback_issue_detects_unicode_math_symbol_warning():
    raw_data_map = {1: "令 φ, θ, ω 为三个角，满足 α+β=γ。"}
    target_blocks = build_page_ir(raw_data_map[1], 1)["blocks"]
    validation = {
        "ok": True,
        "errors": [],
        "warnings": [
            {
                "code": "unicode_math_symbol_outside_latex",
                "message": "最终 Markdown 含裸 Unicode 数学符号。",
            }
        ],
    }

    issue = pipeline._stage2_warning_fallback_issue(
        validation,
        slide_no=1,
        raw_data_map=raw_data_map,
        target_blocks=target_blocks,
    )

    assert issue["code"] == "unicode_math_symbol_outside_latex"


def test_brain_stage_formula_warning_falls_back_to_conservative_formula_warning(monkeypatch, tmp_path):
    config = AppConfig(brain_batch_workers=1)
    report, page_reports = build_run_report("Deck", [str(tmp_path / "page.png")], 0, config)
    page_reports[1]["stage1"]["status"] = "ok"
    raw_data_map = {1: "### Formula\n\\frac a}{b"}
    target_blocks = {1: build_page_ir(raw_data_map[1], 1)["blocks"]}

    monkeypatch.setattr(
        pipeline,
        "run_stage_2_brain_parallel",
        lambda slide_no, raw_data_map, config: {
            "success": True,
            "slide_no": slide_no,
            "markdown": "# Slide 1\n\n$$\n\\frac a}{b\n$$\n",
            "raw_response": "# Slide 1\n\n$$\n\\frac a}{b\n$$\n",
        },
    )

    ok_slides = pipeline._run_brain_stage(
        "Deck",
        1,
        0,
        tmp_path,
        raw_data_map,
        1,
        DummyQueue(),
        config,
        page_reports,
        target_blocks_by_slide=target_blocks,
    )

    markdown = (tmp_path / "Slide_01.md").read_text(encoding="utf-8")
    meta = read_json(tmp_path / "Slide_01.meta.json")
    assert ok_slides == [1]
    assert meta["status"] == "fail_open"
    assert meta["error"]["code"] == "latex_frac_missing_braces"
    assert_clean_user_markdown(markdown)
    assert "\\frac a}{b" in markdown
    assert "$$\n\\frac a}{b\n$$" not in markdown
    assert page_reports[1]["final"]["status"] == "fail_open"


def test_brain_stage_missing_short_text_block_uses_page_ir_fallback(monkeypatch, tmp_path):
    config = AppConfig(brain_batch_workers=1)
    report, page_reports = build_run_report("Deck", [str(tmp_path / "page.png")], 0, config)
    page_reports[1]["stage1"]["status"] = "ok"
    raw_data_map = {1: "关键结论保持不变"}
    target_blocks = {1: build_page_ir(raw_data_map[1], 1)["blocks"]}

    monkeypatch.setattr(
        pipeline,
        "run_stage_2_brain_parallel",
        lambda slide_no, raw_data_map, config: {
            "success": True,
            "slide_no": slide_no,
            "markdown": "# Slide 1\n\n其他结论。\n",
            "raw_response": "# Slide 1\n\n其他结论。\n",
        },
    )

    ok_slides = pipeline._run_brain_stage(
        "Deck",
        1,
        0,
        tmp_path,
        raw_data_map,
        1,
        DummyQueue(),
        config,
        page_reports,
        target_blocks_by_slide=target_blocks,
    )

    markdown = (tmp_path / "Slide_01.md").read_text(encoding="utf-8")
    meta = read_json(tmp_path / "Slide_01.meta.json")
    assert ok_slides == [1]
    assert meta["status"] == "fail_open"
    assert meta["error"]["code"] == "target_text_block_missing"
    assert "关键结论保持不变" in markdown
    assert "其他结论" not in markdown


def test_brain_stage_cached_missing_target_text_block_uses_page_ir_fallback(monkeypatch, tmp_path):
    config = AppConfig(brain_batch_workers=1)
    report, page_reports = build_run_report("Deck", [str(tmp_path / "page.png")], 0, config)
    page_reports[1]["stage1"]["status"] = "ok"
    raw_data_map = {1: "关键结论保持不变"}
    target_blocks = {1: build_page_ir(raw_data_map[1], 1)["blocks"]}
    cached_markdown = "# Slide 1\n\n其他结论。\n"
    (tmp_path / "Slide_01.md").write_text(cached_markdown, encoding="utf-8")
    write_json(
        tmp_path / "Slide_01.meta.json",
        build_slide_meta(
            1,
            cached_markdown,
            {"ok": True, "errors": [], "warnings": []},
            raw_data_map,
            config,
        ),
    )

    def fail_if_called(slide_no, raw_data_map, config):
        raise AssertionError("valid stage2 cache should be checked and handled without calling the model")

    monkeypatch.setattr(pipeline, "run_stage_2_brain_parallel", fail_if_called)

    ok_slides = pipeline._run_brain_stage(
        "Deck",
        1,
        0,
        tmp_path,
        raw_data_map,
        1,
        DummyQueue(),
        config,
        page_reports,
        target_blocks_by_slide=target_blocks,
    )

    markdown = (tmp_path / "Slide_01.md").read_text(encoding="utf-8")
    meta = read_json(tmp_path / "Slide_01.meta.json")
    assert ok_slides == [1]
    assert meta["status"] == "fail_open"
    assert meta["error"]["code"] == "target_text_block_missing"
    assert "关键结论保持不变" in markdown
    assert "其他结论" not in markdown
    assert page_reports[1]["stage2"]["cache"] == "hit"
    assert page_reports[1]["final"]["status"] == "fail_open"


def test_brain_stage_missing_target_formula_block_uses_page_ir_fallback(monkeypatch, tmp_path):
    config = AppConfig(brain_batch_workers=1)
    report, page_reports = build_run_report("Deck", [str(tmp_path / "page.png")], 0, config)
    page_reports[1]["stage1"]["status"] = "ok"
    raw_data_map = {
        1: (
            "### Formula\n"
            "\\begin{aligned}\n"
            "S &= k\\left(\\ln Z-\\beta \\frac{\\partial}{\\partial \\beta} \\ln Z\\right) \\\\\n"
            "&= k(\\ln Z+\\beta U) \\\\\n"
            "&= \\frac{3}{2} N k \\ln T+N k \\ln \\frac{V}{N}+N k\\left[\\ln \\left(\\frac{2 \\pi m k}{h^{2}}\\right)^{\\frac{3}{2}}+\\frac{5}{2}\\right].\n"
            "\\end{aligned}\n"
            "\\tag{5}\n\n"
            "上述式(3)、式(4)和式(5)分别与热力学中式(1.3.11)、式(1.7.4)和式(1.15.4)相当。"
        )
    }
    target_blocks = {1: build_page_ir(raw_data_map[1], 1)["blocks"]}

    monkeypatch.setattr(
        pipeline,
        "run_stage_2_brain_parallel",
        lambda slide_no, raw_data_map, config: {
            "success": True,
            "slide_no": slide_no,
            "markdown": (
                "# Slide 1\n\n"
                "上述式(3)、式(4)和式(5)分别与热力学中式(1.3.11)、式(1.7.4)和式(1.15.4)相当。\n"
            ),
            "raw_response": (
                "# Slide 1\n\n"
                "上述式(3)、式(4)和式(5)分别与热力学中式(1.3.11)、式(1.7.4)和式(1.15.4)相当。\n"
            ),
        },
    )

    ok_slides = pipeline._run_brain_stage(
        "Deck",
        1,
        0,
        tmp_path,
        raw_data_map,
        1,
        DummyQueue(),
        config,
        page_reports,
        target_blocks_by_slide=target_blocks,
    )

    markdown = (tmp_path / "Slide_01.md").read_text(encoding="utf-8")
    meta = read_json(tmp_path / "Slide_01.meta.json")
    assert ok_slides == [1]
    assert meta["status"] == "fail_open"
    assert meta["error"]["code"] == "target_formula_block_missing"
    assert_clean_user_markdown(markdown)
    assert "\\begin{aligned}" in markdown
    assert "\\frac{3}{2} N k \\ln T" in markdown
    assert page_reports[1]["final"]["status"] == "fail_open"


def test_brain_stage_normalizes_formula_tag_markup_before_write(monkeypatch, tmp_path):
    config = AppConfig(brain_batch_workers=1)
    report, page_reports = build_run_report("Deck", [str(tmp_path / "page.png")], 0, config)
    page_reports[1]["stage1"]["status"] = "ok"
    raw_data_map = {
        1: (
            "### Formula\n"
            "\\begin{aligned}\n"
            "S &= k(\\ln Z+\\beta U) \\\\\n"
            "&= \\frac{3}{2}Nk\\ln T\n"
            "\\end{aligned}\n"
            "\\tag{5}"
        )
    }
    target_blocks = {1: build_page_ir(raw_data_map[1], 1)["blocks"]}

    monkeypatch.setattr(
        pipeline,
        "run_stage_2_brain_parallel",
        lambda slide_no, raw_data_map, config: {
            "success": True,
            "slide_no": slide_no,
            "markdown": (
                "# Slide 1\n\n"
                "$$\n"
                "\\begin{align}\n"
                "S &= k(\\ln Z+\\beta U) \\\\\n"
                "&= \\frac{3}{2}Nk\\ln T \\tag{5}\n"
                "\\end{align}\n"
                "$$\n"
            ),
            "raw_response": (
                "# Slide 1\n\n"
                "$$\n"
                "\\begin{align}\n"
                "S &= k(\\ln Z+\\beta U) \\\\\n"
                "&= \\frac{3}{2}Nk\\ln T \\tag{5}\n"
                "\\end{align}\n"
                "$$\n"
            ),
        },
    )

    ok_slides = pipeline._run_brain_stage(
        "Deck",
        1,
        0,
        tmp_path,
        raw_data_map,
        1,
        DummyQueue(),
        config,
        page_reports,
        target_blocks_by_slide=target_blocks,
    )

    markdown = (tmp_path / "Slide_01.md").read_text(encoding="utf-8")
    meta = read_json(tmp_path / "Slide_01.meta.json")
    assert ok_slides == [1]
    assert meta["status"] == "ok"
    assert meta["markdown_source"]["kind"] == "brain_refine"
    assert meta["refiner"]["applied_ops"][0]["op"] == "normalize_formula"
    assert "\\begin{align}" not in markdown
    assert "\\tag{5}\n\\end{aligned}" not in markdown
    assert "\\begin{aligned}\nS &= k(\\ln Z+\\beta U) \\\\\n&= \\frac{3}{2}Nk\\ln T\n\\end{aligned}\n\\tag{5}" in markdown
    assert "formula_markup_needs_normalize" not in {issue["code"] for issue in meta["validation"]["warnings"]}


def test_brain_stage_records_checked_refiner_ops(monkeypatch, tmp_path):
    config = AppConfig(brain_batch_workers=1)
    report, page_reports = build_run_report("Deck", [str(tmp_path / "page.png")], 0, config)
    page_reports[1]["stage1"]["status"] = "ok"

    monkeypatch.setattr(
        pipeline,
        "run_stage_2_brain_parallel",
        lambda slide_no, raw_data_map, config: {
            "success": True,
            "slide_no": slide_no,
            "markdown": "正文\n",
            "raw_response": "正文",
        },
    )

    ok_slides = pipeline._run_brain_stage("Deck", 1, 0, tmp_path, {1: "raw"}, 1, DummyQueue(), config, page_reports)

    assert ok_slides == [1]
    assert (tmp_path / "Slide_01.md").read_text(encoding="utf-8").startswith("# Slide 1")
    meta = read_json(tmp_path / "Slide_01.meta.json")
    assert meta["refiner"]["changed"] is True
    assert meta["refiner"]["applied_ops"][0]["op"] == "fix_heading"


def test_process_single_docpage_task_writes_report_and_full_markdown(monkeypatch, tmp_path):
    image = tmp_path / "page.png"
    image.write_bytes(b"fake image")
    output = tmp_path / "out"
    config = AppConfig(output_folder=str(output), vision_batch_workers=1, brain_batch_workers=1)

    monkeypatch.setattr(pipeline, "set_dashscope_api_key", lambda config: None)
    monkeypatch.setattr(
        pipeline,
        "run_stage_1_vision",
        lambda img_path, slide_no, doc_name, msg_queue, config: {
            "success": True,
            "slide_no": slide_no,
            "raw_text": (
                "热力学第一定律描述内能、热量和功之间的关系。孤立系统的总能量保持守恒。\n\n"
                "### Formula\n"
                "$$\n"
                "E = mc^2\n"
                "$$\n\n"
                "### Table Analysis\n"
                "| A | B |\n"
                "| --- | --- |\n"
                "| 1 | 2 | 3 |\n\n"
                "### Figure Analysis\n"
                "图示被遮挡，无法确定节点和箭头方向。"
            ),
        },
    )
    monkeypatch.setattr(
        pipeline,
        "run_stage_2_brain_parallel",
        lambda slide_no, raw_data_map, config: {
            "success": True,
            "slide_no": slide_no,
            "markdown": (
                "# Slide 1\n\n"
                "热力学第一定律描述内能、热量和功之间的关系。孤立系统的总能量保持守恒。\n\n"
                "$$\nE = mc^2\n$$\n\n"
                "```text\n"
                "| A | B |\n"
                "| --- | --- |\n"
                "| 1 | 2 | 3 |\n"
                "```\n\n"
                "<details>\n"
                "<summary>图示识别内容</summary>\n\n"
                "- 说明：图示被遮挡，无法确定节点和箭头方向。\n\n"
                "</details>\n"
            ),
            "raw_response": (
                "# Slide 1\n\n"
                "热力学第一定律描述内能、热量和功之间的关系。孤立系统的总能量保持守恒。\n\n"
                "$$\nE = mc^2\n$$\n\n"
                "```text\n"
                "| A | B |\n"
                "| --- | --- |\n"
                "| 1 | 2 | 3 |\n"
                "```\n\n"
                "<details>\n"
                "<summary>图示识别内容</summary>\n\n"
                "- 说明：图示被遮挡，无法确定节点和箭头方向。\n\n"
                "</details>\n"
            ),
        },
    )

    result = pipeline.process_single_docpage_task(
        "Deck",
        {"images": [str(image)], "range_start": 0, "range_end": 1, "task_id": 1},
        DummyQueue(),
        config,
    )

    assert result == "Deck Done"
    deck_dir = output / "Deck"
    report = read_json(deck_dir / "run_report.json")
    raw = read_json(deck_dir / "temp_raw_vision" / "Raw_01.json")
    assert report["status"] == "ok"
    assert report["summary"]["pages_ok"] == 1
    assert report["summary"]["markdown_source_counts"] == {"brain_refine": 1}
    assert report["pages"][0]["final"]["markdown_source"]["kind"] == "brain_refine"
    assert report["summary"]["block_refiner_changed_pages"] == 1
    assert report["summary"]["block_refiner_applied_ops"] == 1
    assert report["summary"]["block_counts"]["formula_block"] == 1
    assert report["summary"]["provenance"]["origin_counts"]["vision_ocr"] == 1
    assert report["summary"]["provenance"]["origin_counts"]["refiner_op"] == 1
    assert report["summary"]["provenance"]["origin_counts"]["vision_table"] == 1
    assert report["summary"]["provenance"]["origin_counts"]["vision_description"] == 1
    assert report["summary"]["provenance"]["generated_description_count"] == 1
    assert report["summary"]["figure_count"] == 1
    assert report["summary"]["figure_warning_count"] == 1
    assert report["summary"]["formula_warning_count"] == 0
    assert report["summary"]["table_warning_count"] == 1
    assert report["summary"]["ocr_coverage_warning_count"] == 0
    assert report["summary"]["suspects"]["by_code"]["table_quality_warning"] == 1
    assert "latex_frac_missing_braces" not in report["summary"]["suspects"]["by_code"]
    assert report["summary"]["suspects"]["by_op"]["mark_uncertain"] >= 1
    assert report["summary"]["suspects"]["actionable_total"] >= 2
    assert "ocr_coverage_low" not in {issue["code"] for issue in report["pages"][0]["validation"]["warnings"]}
    assert any(suspect.get("block_id") and suspect.get("op") for suspect in report["pages"][0]["suspects"])
    assert report["pages"][0]["stage1"]["blocks_count"] >= 1
    assert report["pages"][0]["block_refiner"]["changed"] is True
    assert report["pages"][0]["block_refiner"]["applied_ops"][0]["op"]["op"] == "normalize_formula"
    formula_warnings = [
        warning
        for warning in report["pages"][0]["quality"]["warnings"]
        if str(warning.get("code") or "").startswith("formula_") or str(warning.get("code") or "").startswith("latex_")
    ]
    assert {warning["code"] for warning in formula_warnings} == set()
    assert report["pages"][0]["quality"]["figure_warning_count"] == 1
    assert report["pages"][0]["quality"]["table_warning_count"] == 1
    assert raw["blocks"]
    assert raw["provenance"]["summary"]["origin_counts"]["refiner_op"] == 1
    assert raw["block_refiner"]["applied_ops"][0]["after_block_ids"]
    slide_markdown = (deck_dir / "Slide_01.md").read_text(encoding="utf-8")
    full_markdown = (deck_dir / "Deck_FULL.md").read_text(encoding="utf-8")
    assert_clean_user_markdown(slide_markdown)
    assert_clean_user_markdown(full_markdown)
    assert "# Slide 1" in full_markdown


def test_process_single_docpage_task_rejects_dirty_diagnostic_markdown(monkeypatch, tmp_path):
    image = tmp_path / "page.png"
    image.write_bytes(b"fake image")
    output = tmp_path / "out"
    config = AppConfig(output_folder=str(output), vision_batch_workers=1, brain_batch_workers=1)
    raw_text = (
        "热力学第一定律描述内能、热量和功之间的关系。\n\n"
        "### Formula\n"
        "E = [?] mc^2"
    )

    monkeypatch.setattr(pipeline, "set_dashscope_api_key", lambda config: None)
    monkeypatch.setattr(
        pipeline,
        "run_stage_1_vision",
        lambda img_path, slide_no, doc_name, msg_queue, config: {
            "success": True,
            "slide_no": slide_no,
            "raw_text": raw_text,
        },
    )
    dirty_markdown = (
        "# Slide 1\n\n"
        "热力学第一定律描述内能、热量和功之间的关系。\n\n"
        "> [!WARNING] 公式识别不确定\n"
        "> 原始识别：\n"
        "> E = [?] mc^2\n"
        ">\n"
        "> 质量警告：\n"
        "> - 公式中包含不确定识别标记。\n"
    )
    monkeypatch.setattr(
        pipeline,
        "run_stage_2_brain_parallel",
        lambda slide_no, raw_data_map, config: {
            "success": True,
            "slide_no": slide_no,
            "markdown": dirty_markdown,
            "raw_response": dirty_markdown,
        },
    )

    result = pipeline.process_single_docpage_task(
        "Deck",
        {"images": [str(image)], "range_start": 0, "range_end": 1, "task_id": 1},
        DummyQueue(),
        config,
    )

    assert result == "Deck Done"
    deck_dir = output / "Deck"
    slide_markdown = (deck_dir / "Slide_01.md").read_text(encoding="utf-8")
    full_markdown = (deck_dir / "Deck_FULL.md").read_text(encoding="utf-8")
    report = read_json(deck_dir / "run_report.json")
    error = read_json(deck_dir / "Slide_01.error.json")

    assert report["status"] == "fail_open"
    assert report["summary"]["markdown_source_counts"] == {"stage1_page_ir": 1}
    assert report["pages"][0]["final"]["status"] == "fail_open"
    assert read_json(deck_dir / "Slide_01.meta.json")["status"] == "fail_open"
    assert "![page evidence](evidence/Slide_01.png)" in slide_markdown
    assert (deck_dir / "evidence" / "Slide_01.png").exists()
    assert "E = [?] mc^2" in slide_markdown
    assert "E = [?] mc^2" in full_markdown
    assert_clean_user_markdown(slide_markdown)
    assert_clean_user_markdown(full_markdown)
    assert "> [!WARNING] 公式识别不确定" in error["raw_response"]


def test_process_single_docpage_task_reports_fail_open_markdown(monkeypatch, tmp_path):
    image = tmp_path / "page.png"
    image.write_bytes(b"fake image")
    output = tmp_path / "out"
    config = AppConfig(output_folder=str(output), vision_batch_workers=1, brain_batch_workers=1)
    raw_text = "热力学第一定律描述内能、热量和功之间的关系。"

    monkeypatch.setattr(pipeline, "set_dashscope_api_key", lambda config: None)
    monkeypatch.setattr(
        pipeline,
        "run_stage_1_vision",
        lambda img_path, slide_no, doc_name, msg_queue, config: {
            "success": True,
            "slide_no": slide_no,
            "raw_text": raw_text,
        },
    )
    monkeypatch.setattr(
        pipeline,
        "run_stage_2_brain_parallel",
        lambda slide_no, raw_data_map, config: {
            "success": False,
            "slide_no": slide_no,
            "error": "Brain Error: 500",
            "error_code": "Brain Error",
            "raw_response": "Brain Error: 500",
        },
    )

    result = pipeline.process_single_docpage_task(
        "Deck",
        {"images": [str(image)], "range_start": 0, "range_end": 1, "task_id": 1},
        DummyQueue(),
        config,
    )

    assert result == "Deck Done"
    deck_dir = output / "Deck"
    report = read_json(deck_dir / "run_report.json")
    full_markdown = (deck_dir / "Deck_FULL.md").read_text(encoding="utf-8")

    assert report["status"] == "fail_open"
    assert report["summary"]["pages_ok"] == 0
    assert report["summary"]["pages_failed"] == 1
    assert report["summary"]["fail_open_pages"] == 1
    assert report["summary"]["markdown_pages"] == 1
    assert report["summary"]["markdown_source_counts"] == {"stage1_page_ir": 1}
    assert report["pages"][0]["final"]["included_in_full"] is True
    assert report["pages"][0]["final"]["status"] == "fail_open"
    assert report["pages"][0]["final"]["markdown_source"]["kind"] == "stage1_page_ir"
    assert read_json(deck_dir / "Slide_01.meta.json")["status"] == "fail_open"
    assert "# Slide 1" in full_markdown
    assert "![page evidence](evidence/Slide_01.png)" in full_markdown
    assert (deck_dir / "evidence" / "Slide_01.png").exists()
    assert_clean_user_markdown(full_markdown)
    assert "热力学第一定律" in full_markdown
