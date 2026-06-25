import json

from docpage2md_app.aliyun_catalog import ModelRecord
from docpage2md_app.official_catalog import (
    diff_model_records,
    fetch_openai_compatible_model_ids,
    merge_markdown_pricing,
    parse_deepseek_pricing_text,
    parse_simple_markdown_prices,
    refresh_official_catalog,
)


def test_parse_deepseek_pricing_text_from_local_style_table():
    text = """
    | 模型 | deepseek-v4-flash | deepseek-v4-pro |
    | 缓存命中 | ¥0.02 | ¥0.2 |
    | 缓存未命中 | ¥1 | ¥4 |
    | 输出 | ¥2 | ¥12 |
    | 并发限制 | 100 | 20 |
    """

    prices = parse_deepseek_pricing_text(text, source="fixture")

    assert prices["deepseek-v4-flash"]["input_price"] == 1.0
    assert prices["deepseek-v4-flash"]["output_price"] == 2.0
    assert prices["deepseek-v4-flash"]["cached_input_price"] == 0.02
    assert prices["deepseek-v4-pro"]["input_price"] == 4.0
    assert prices["deepseek-v4-pro"]["output_price"] == 12.0
    assert prices["deepseek-v4-pro"]["price_source"] == "fixture"


def test_parse_simple_markdown_prices_and_merge_records():
    text = "| model | input | output | cached |\n| deepseek-v4-flash | 1 | 2 | 0.02 |\n"
    records = [ModelRecord(model_id="deepseek-v4-flash", provider="deepseek")]

    merged = merge_markdown_pricing(records, text, source="paste")

    record = merged[0]
    assert record.input_price == 1.0
    assert record.output_price == 2.0
    assert record.cached_input_price == 0.02
    assert record.price_source == "paste"


def test_openai_compatible_models_uses_models_endpoint(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "token")

    def fake_urlopen(req, timeout=10):
        assert req.full_url == "https://provider.test/v1/models"
        assert req.headers["Authorization"] == "Bearer token"
        return _Response({"data": [{"id": "b-model"}, {"id": "a-model"}]})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    assert fetch_openai_compatible_model_ids("https://provider.test/v1") == ["a-model", "b-model"]


def test_diff_model_records_detects_added_removed_price_changed():
    old = [
        ModelRecord(model_id="old", provider="deepseek"),
        ModelRecord(model_id="same", provider="deepseek", input_price=1, output_price=2),
    ]
    new = [
        ModelRecord(model_id="new", provider="deepseek"),
        ModelRecord(model_id="same", provider="deepseek", input_price=1, output_price=3),
    ]

    diff = diff_model_records(old, new)

    assert diff["added"] == ["deepseek:new"]
    assert diff["removed"] == ["deepseek:old"]
    assert diff["price_changed"][0]["model"] == "deepseek:same"


def test_refresh_official_catalog_falls_back_to_static_on_provider_failure(monkeypatch, tmp_path):
    monkeypatch.setattr("docpage2md_app.official_catalog.fetch_deepseek_official_records", lambda: (_ for _ in ()).throw(RuntimeError("boom")))

    result = refresh_official_catalog(providers=["deepseek"], cache_path=str(tmp_path / "models.json"))

    assert result.errors[0]["provider"] == "deepseek"
    assert result.records
    assert result.cache_data["schema_version"] == 2
    assert (tmp_path / "models.json").exists()


class _Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")
