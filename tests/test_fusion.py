from copy import deepcopy

from docpage2md_app.fusion import apply_fusion_ops, build_candidate_groups, fuse_document_irs
from docpage2md_app.fusion_prompt import build_fusion_decision_prompt
from docpage2md_app.renderer import render_page_ir_to_markdown


def _block(block_id, block_type, text, bbox, *, source_page=1, confidence=0.8, image_ref=None):
    block = {
        "id": block_id,
        "type": block_type,
        "text": text,
        "source_page": source_page,
        "confidence": confidence,
        "origin": "vision_formula" if block_type == "formula_block" else "vision_description" if block_type in {"figure_note", "image_ref"} else "vision_ocr",
        "evidence": {"raw_text": text or image_ref or "", "provider": "fixture"},
        "bbox": bbox,
        "source_engine": "fixture",
    }
    if block_type == "formula_block":
        block["latex"] = text
    if image_ref:
        block["image_ref"] = image_ref
        block["path"] = image_ref
    return block


def _page(page_no, blocks):
    return {
        "schema_version": 11,
        "source_page": page_no,
        "page_image_ref": f"assets/pages/page_{page_no:03d}.png",
        "raw_text": "\n\n".join(block.get("text") or "" for block in blocks),
        "raw_text_sha256": "fixture",
        "blocks": blocks,
    }


def _document(pages, *, engine):
    return {
        "schema_version": "docpage2md-docir-v1",
        "adapter_version": "fixture",
        "engine_mode": engine,
        "source": {"input_path": "sample.pdf", "input_hash": "hash", "input_type": "pdf", "artifact_root": f"{engine}_artifact"},
        "pages": pages,
        "assets": [],
        "metadata": {"page_count": len(pages)},
    }


def test_candidate_grouping_uses_bbox_and_text_similarity():
    mineru = _page(1, [_block("p0001-b001", "paragraph", "令 G 为群", [10, 10, 200, 40])])
    paddle = _page(1, [_block("p0001-b001", "paragraph", "令G为群", [11, 12, 198, 42])])

    groups = build_candidate_groups(mineru, paddle, page_no=1)

    assert len(groups) == 1
    assert groups[0]["match_reason"] == "bbox_overlap"
    assert {item["source"] for item in groups[0]["_candidates"]} == {"mineru", "paddleocr"}


def test_candidate_grouping_preserves_unmatched_blocks_from_both_engines():
    mineru = _page(1, [_block("p0001-b001", "paragraph", "MinerU only", [10, 10, 100, 30])])
    paddle = _page(1, [_block("p0001-b001", "paragraph", "Paddle only", [10, 300, 100, 330])])

    groups = build_candidate_groups(mineru, paddle, page_no=1)

    assert [group["match_reason"] for group in groups] == ["unmatched_from_mineru", "unmatched_from_paddleocr"]


def test_fuse_document_irs_preserves_paddleocr_only_page():
    mineru_ir = _document([_page(1, [_block("p0001-b001", "paragraph", "page one", [0, 0, 100, 20])])], engine="mineru")
    paddle_ir = _document(
        [
            _page(1, [_block("p0001-b001", "paragraph", "page one", [0, 0, 100, 20])]),
            _page(2, [_block("p0002-b001", "paragraph", "paddle page two", [0, 0, 100, 20], source_page=2)]),
        ],
        engine="paddleocr",
    )

    result = fuse_document_irs(mineru_ir, paddle_ir)

    assert [page["source_page"] for page in result.document_ir["pages"]] == [1, 2]
    assert result.document_ir["pages"][1]["blocks"][0]["text"] == "paddle page two"
    assert result.report["summary"]["pages"] == 2


def test_apply_fusion_ops_can_choose_better_formula_candidate():
    mineru = _page(1, [_block("p0001-b001", "paragraph", "φ→θ", [10, 10, 200, 40], confidence=0.45)])
    paddle = _page(1, [_block("p0001-b001", "formula_block", r"\phi \to \theta", [10, 10, 200, 40], confidence=0.9)])
    groups = build_candidate_groups(mineru, paddle, page_no=1)

    page_ir, report = apply_fusion_ops(
        mineru,
        paddle,
        groups,
        [{"action": "replace_formula", "target_group": groups[0]["group_id"], "source": "paddleocr"}],
        page_no=1,
    )

    assert page_ir["blocks"][0]["type"] == "formula_block"
    assert page_ir["blocks"][0]["latex"] == r"\phi \to \theta"
    assert report["decisions"][0]["action"] == "replace_formula"


def test_default_fusion_prefers_richer_similar_candidate():
    mineru = _page(
        1,
        [_block("p0001-b001", "formula_inline", r"(2)结合体： $\forall \alpha,\beta,\gamma$", [10, 10, 300, 50], confidence=0.75)],
    )
    paddle = _page(
        1,
        [
            _block(
                "p0001-b001",
                "paragraph",
                r"(2)结合律： $\forall\alpha,\beta,\gamma$，恒有 $(g(\alpha)g(\beta))g(\gamma)=g(\alpha)(g(\beta)g(\gamma))$",
                [10, 10, 320, 70],
                confidence=0.82,
            )
        ],
    )

    result = fuse_document_irs(_document([mineru], engine="mineru"), _document([paddle], engine="paddleocr"))

    page = result.document_ir["pages"][0]
    assert "结合律" in page["blocks"][0]["text"]
    assert page["blocks"][0]["source_engine"] == "paddleocr"


def test_default_fusion_formula_conflict_renders_one_formula_candidate():
    mineru = _page(
        2,
        [
            _block(
                "p0002-b001",
                "formula_block",
                r"\mathrm{如} SO(2) \quad 0, 2\pi, 4\pi, -2\pi, \dots \mathrm{都可}",
                [10, 10, 320, 60],
                source_page=2,
                confidence=0.7,
            )
        ],
    )
    paddle = _page(
        2,
        [
            _block(
                "p0002-b001",
                "paragraph",
                r"即 f(d,d)=f(d,d)=\alpha_0。",
                [10, 10, 320, 60],
                source_page=2,
                confidence=0.86,
            )
        ],
    )

    result = fuse_document_irs(_document([mineru], engine="mineru"), _document([paddle], engine="paddleocr"))
    page = result.document_ir["pages"][0]
    markdown = render_page_ir_to_markdown(page, 2)

    assert page["blocks"][0]["type"] == "formula_block"
    assert page["blocks"][0]["source_engine"] == "mineru"
    assert r"\mathrm{如} SO(2)" in markdown
    assert "$$" in markdown
    assert "[mineru]" not in markdown.lower()
    assert "[paddleocr]" not in markdown.lower()


def test_mark_uncertain_keeps_candidate_comparison_out_of_markdown():
    mineru = _page(1, [_block("p0001-b001", "paragraph", "第一种解释保留为正文。", [10, 10, 200, 40], confidence=0.8)])
    paddle = _page(1, [_block("p0001-b001", "paragraph", "另一份识别结果差异很大。", [10, 10, 200, 40], confidence=0.8)])
    groups = build_candidate_groups(mineru, paddle, page_no=1)

    page_ir, report = apply_fusion_ops(
        mineru,
        paddle,
        groups,
        [{"action": "mark_uncertain", "target_group": groups[0]["group_id"], "reason": "fixture_conflict"}],
        page_no=1,
    )
    markdown = render_page_ir_to_markdown(page_ir, 1)

    assert report["decisions"][0]["action"] == "mark_uncertain"
    assert page_ir["blocks"][0]["text"] in markdown
    assert "[mineru]" not in markdown.lower()
    assert "[paddleocr]" not in markdown.lower()
    assert page_ir["blocks"][0]["evidence"]["uncertain_resolution"]["candidate_ids"]


def test_apply_fusion_ops_rejects_bad_action_and_keeps_candidates():
    mineru = _page(1, [_block("p0001-b001", "paragraph", "MinerU text", [10, 10, 200, 40])])
    paddle = _page(1, [_block("p0001-b001", "paragraph", "Paddle text", [10, 10, 200, 40])])
    groups = build_candidate_groups(mineru, paddle, page_no=1)

    page_ir, report = apply_fusion_ops(
        mineru,
        paddle,
        groups,
        [{"action": "delete_everything", "target_group": groups[0]["group_id"]}],
        page_no=1,
    )

    assert report["rejected_ops"][0]["reason"] == "unknown_or_unsafe_action"
    assert [block["text"] for block in page_ir["blocks"]] == ["MinerU text", "Paddle text"]


def test_backend_ops_are_checked_and_reported():
    mineru_ir = _document([_page(1, [_block("p0001-b001", "paragraph", "bad", [0, 0, 100, 20])])], engine="mineru")
    paddle_ir = _document([_page(1, [_block("p0001-b001", "paragraph", "good", [0, 0, 100, 20])])], engine="paddleocr")

    def backend(page_context, groups, documents):
        return {"ops": [{"action": "choose_block", "target_group": groups[0]["group_id"], "source": "paddleocr"}], "warnings": ["fixture"]}

    result = fuse_document_irs(mineru_ir, paddle_ir, decision_backend=backend)

    page = result.document_ir["pages"][0]
    assert page["blocks"][0]["text"] == "good"
    assert page["fusion"]["backend"] == "custom"
    assert page["fusion"]["backend_warnings"] == ["fixture"]


def test_build_fusion_prompt_exposes_only_public_candidate_fields():
    mineru = _page(1, [_block("p0001-b001", "paragraph", "A", [0, 0, 100, 20])])
    paddle = _page(1, [_block("p0001-b001", "paragraph", "A", [0, 0, 100, 20])])
    groups = deepcopy(build_candidate_groups(mineru, paddle, page_no=1))

    prompt = build_fusion_decision_prompt(groups, document_type="手写群论笔记")

    assert "choose_block" in prompt
    assert "手写群论笔记" in prompt
    assert '"block":' not in prompt
