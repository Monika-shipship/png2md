from ppt2md_app.ir import build_page_ir
from ppt2md_app.provenance import build_page_provenance, merge_provenance_summaries
from ppt2md_app.refiner import refine_page_ir


def test_build_page_provenance_tracks_origins_and_generated_descriptions():
    page_ir = build_page_ir("标题:\n\n### Figure Analysis\n左侧是 A。", 1)

    provenance = build_page_provenance(page_ir)

    assert provenance["schema_version"] == 1
    assert [entry["origin"] for entry in provenance["entries"]] == ["vision_ocr", "vision_description"]
    assert provenance["entries"][1]["generated_description"] is True
    assert provenance["summary"]["generated_description_count"] == 1
    assert provenance["summary"]["renderer_template_count"] == 1


def test_merge_provenance_summaries_counts_refiner_ops():
    refined = refine_page_ir(build_page_ir("### Formula\n$$\nE = mc^2\n$$", 2), slide_no=2).page_ir
    provenance = build_page_provenance(refined)

    merged = merge_provenance_summaries([{"provenance": provenance}])

    assert merged["origin_counts"]["refiner_op"] == 1
    assert merged["refiner_op_count"] == 1
    assert merged["type_counts"]["formula_block"] == 1
