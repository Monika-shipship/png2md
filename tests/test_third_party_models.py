import pytest

from docpage2md_app.config import AppConfig
from docpage2md_app.model_catalog import ROLE_BRAIN, ROLE_VISION
from docpage2md_app.third_party_models import (
    delete_third_party_model,
    filter_registry_models,
    load_third_party_models,
    parse_bulk_models_text,
    update_third_party_model_verification,
    upsert_third_party_model,
)


def test_upsert_dedupes_by_canonical_identity(tmp_path):
    config = AppConfig(log_folder=str(tmp_path))

    first = upsert_third_party_model(
        config,
        {
            "model_id": "vendor/model-a",
            "name": "A",
            "provider": "openai_compatible",
            "base_url": "https://example.com/v1/",
            "api_key_env": "openai_api_key",
            "roles": "brain",
        },
    )
    second = upsert_third_party_model(
        config,
        {
            "model_id": "VENDOR/MODEL-A",
            "name": "A2",
            "provider": "openai_compatible",
            "base_url": "https://example.com/v1",
            "api_key_env": "OPENAI_API_KEY",
            "roles": "brain",
        },
    )

    models = load_third_party_models(config)
    assert len(models) == 1
    assert second["id"] == first["id"]
    assert models[0]["name"] == "A2"
    assert models[0]["api_key_env"] == "OPENAI_API_KEY"


def test_malformed_registry_is_not_overwritten_by_upsert(tmp_path):
    config = AppConfig(log_folder=str(tmp_path))
    config.log_path.mkdir(parents=True, exist_ok=True)
    config.third_party_models_path.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(ValueError):
        upsert_third_party_model(config, {"model_id": "model-a"})

    assert config.third_party_models_path.read_text(encoding="utf-8") == "{not valid json"


def test_parse_bulk_models_text_and_role_filtering():
    items = parse_bulk_models_text(
        "model-a, A, both, 1.5, 2\n# comment\nmodel-b, B, vision\n",
        defaults={"provider": "openai_compatible", "base_url": "https://example.com/v1"},
    )

    assert len(items) == 2
    assert filter_registry_models(items, ROLE_BRAIN)[0]["model_id"] == "model-a"
    assert [item["model_id"] for item in filter_registry_models(items, ROLE_VISION)] == ["model-a", "model-b"]


def test_delete_third_party_model(tmp_path):
    config = AppConfig(log_folder=str(tmp_path))
    saved = upsert_third_party_model(config, {"model_id": "model-a"})

    assert delete_third_party_model(config, saved["id"]) is True
    assert delete_third_party_model(config, saved["id"]) is False
    assert load_third_party_models(config) == []


def test_third_party_registry_stores_env_name_not_secret(tmp_path):
    config = AppConfig(log_folder=str(tmp_path))
    upsert_third_party_model(
        config,
        {
            "model_id": "vendor/model-a",
            "api_key_env": "VENDOR_API_KEY",
            "note": "ordinary note",
        },
    )

    raw = config.third_party_models_path.read_text(encoding="utf-8")

    assert "VENDOR_API_KEY" in raw
    assert "ordinary note" in raw
    assert "sk-" not in raw


def test_update_third_party_model_verification_persists_status_without_secret(tmp_path):
    config = AppConfig(log_folder=str(tmp_path))
    saved = upsert_third_party_model(
        config,
        {
            "model_id": "vendor/model-a",
            "api_key_env": "VENDOR_API_KEY",
            "roles": "vision",
        },
    )

    updated = update_third_party_model_verification(config, saved["id"], ROLE_VISION, "ok", "")
    raw = config.third_party_models_path.read_text(encoding="utf-8")

    assert updated["verification"]["vision"] == "ok"
    assert updated["verification"]["vision_raw_status"] == "ok"
    assert "vision_checked_at" in updated["verification"]
    assert "VENDOR_API_KEY" in raw
    assert "sk-" not in raw


def test_update_verification_does_not_overwrite_bad_registry(tmp_path):
    config = AppConfig(log_folder=str(tmp_path))
    config.log_path.mkdir(parents=True, exist_ok=True)
    config.third_party_models_path.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(ValueError):
        update_third_party_model_verification(config, "missing", ROLE_BRAIN, "ok")

    assert config.third_party_models_path.read_text(encoding="utf-8") == "{not valid json"
