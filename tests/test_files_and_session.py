from docpage2md_app.files import merge_markdowns, natural_sort_key, read_json, write_json
from docpage2md_app.session import parse_range_string


def test_parse_range_string():
    assert parse_range_string("", 10) == (0, 10)
    assert parse_range_string("2-4", 10) == (1, 4)
    assert parse_range_string("3-end", 10) == (2, 10)
    assert parse_range_string("bad", 10) == (0, 10)


def test_natural_sort_key_orders_slide_names():
    names = ["Slide_10.md", "Slide_2.md", "Slide_01.md"]

    assert sorted(names, key=natural_sort_key) == ["Slide_01.md", "Slide_2.md", "Slide_10.md"]


def test_write_json_is_readable(tmp_path):
    path = tmp_path / "data.json"

    write_json(path, {"ok": True})

    assert read_json(path) == {"ok": True}
    assert not list(tmp_path.glob("*.tmp"))


def test_merge_markdowns_uses_exact_slide_names_and_ok_meta(tmp_path):
    (tmp_path / "Slide_01.md").write_text("# Slide 1\n\nok\n", encoding="utf-8")
    write_json(tmp_path / "Slide_01.meta.json", {"status": "ok"})
    (tmp_path / "Slide_02.md").write_text("# Slide 2\n\nfallback\n", encoding="utf-8")
    write_json(tmp_path / "Slide_02.meta.json", {"status": "fail_open"})
    (tmp_path / "Slide_04.md").write_text("# Slide 4\n\nfailed\n", encoding="utf-8")
    write_json(tmp_path / "Slide_04.meta.json", {"status": "failed"})
    (tmp_path / "Slide_03.failed.md").write_text("# Slide 3\n\nbad\n", encoding="utf-8")

    merge_markdowns(tmp_path, "Deck", allowed_slide_numbers=[1, 2, 3, 4])

    merged = (tmp_path / "Deck_FULL.md").read_text(encoding="utf-8")
    assert merged.startswith("# Deck\n\n")
    assert "汇总笔记" not in merged.splitlines()[0]
    assert "# Slide 1" in merged
    assert "# Slide 2" in merged
    assert "# Slide 3" not in merged
    assert "# Slide 4" not in merged
