from ppt2md_app.artifacts import build_raw_cache_record, stage1_fingerprint, validate_raw_cache_record
from ppt2md_app.config import AppConfig


def test_legacy_raw_cache_does_not_hit(tmp_path):
    image = tmp_path / "page.png"
    image.write_bytes(b"fake image")
    fingerprint = stage1_fingerprint(image, AppConfig())

    valid, reason = validate_raw_cache_record({"success": True, "slide_no": 1, "raw_text": "old"}, 1, fingerprint)

    assert not valid
    assert reason == "legacy_miss"


def test_raw_cache_hits_only_when_fingerprint_matches(tmp_path):
    image = tmp_path / "page.png"
    image.write_bytes(b"fake image")
    config = AppConfig(model_vision="qwen3-vl-plus")
    record = build_raw_cache_record({"success": True, "slide_no": 1, "raw_text": "raw text"}, image, config)
    fingerprint = stage1_fingerprint(image, config)

    assert record["page_ir"]["source_page"] == 1
    assert record["blocks"][0]["id"] == "p0001-b001"
    assert record["block_refiner"]["version"].startswith("block-refiner-")
    assert record["block_refiner"]["changed"] is False
    assert record["provenance"]["schema_version"] == 1
    assert record["provenance"]["entries"][0]["id"] == "p0001-b001"
    assert record["provenance"]["entries"][0]["origin"] == "vision_ocr"
    assert record["provenance"]["summary"]["origin_counts"] == {"vision_ocr": 1}

    valid, reason = validate_raw_cache_record(record, 1, fingerprint)
    assert valid
    assert reason == "hit"

    other_fingerprint = stage1_fingerprint(image, AppConfig(model_vision="qwen3-vl-max"))
    valid, reason = validate_raw_cache_record(record, 1, other_fingerprint)
    assert not valid
    assert reason == "invalid"


def test_raw_cache_without_blocks_does_not_hit(tmp_path):
    image = tmp_path / "page.png"
    image.write_bytes(b"fake image")
    config = AppConfig()
    record = build_raw_cache_record({"success": True, "slide_no": 1, "raw_text": "raw text"}, image, config)
    del record["blocks"]

    valid, reason = validate_raw_cache_record(record, 1, stage1_fingerprint(image, config))

    assert not valid
    assert reason == "invalid"


def test_raw_cache_without_block_refiner_does_not_hit(tmp_path):
    image = tmp_path / "page.png"
    image.write_bytes(b"fake image")
    config = AppConfig()
    record = build_raw_cache_record({"success": True, "slide_no": 1, "raw_text": "raw text"}, image, config)
    del record["block_refiner"]

    valid, reason = validate_raw_cache_record(record, 1, stage1_fingerprint(image, config))

    assert not valid
    assert reason == "invalid"


def test_raw_cache_without_provenance_does_not_hit(tmp_path):
    image = tmp_path / "page.png"
    image.write_bytes(b"fake image")
    config = AppConfig()
    record = build_raw_cache_record({"success": True, "slide_no": 1, "raw_text": "raw text"}, image, config)
    del record["provenance"]

    valid, reason = validate_raw_cache_record(record, 1, stage1_fingerprint(image, config))

    assert not valid
    assert reason == "invalid"
