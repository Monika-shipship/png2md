import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .aliyun_catalog import ModelRecord, infer_family
from .config import AppConfig
from .model_catalog import ROLE_BRAIN, ROLE_VISION

ROLE_BOTH = "both"
SUPPORTED_PROVIDERS = {
    "dashscope",
    "dashscope_openai",
    "deepseek",
    "openai_compatible",
}
SUPPORTED_ROLES = {ROLE_VISION, ROLE_BRAIN, ROLE_BOTH}


def load_third_party_models(config: AppConfig) -> List[Dict]:
    path = config.third_party_models_path
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return []

    records = data.get("models") if isinstance(data, dict) else data
    if not isinstance(records, list):
        return []
    return [_normalize_registry_item(item) for item in records if isinstance(item, dict)]


def save_third_party_models(config: AppConfig, models: List[Dict]):
    config.log_path.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "updated_at": _now_iso(),
        "models": [_normalize_registry_item(item) for item in models],
    }
    with config.third_party_models_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def upsert_third_party_model(config: AppConfig, item: Dict) -> Dict:
    models = load_third_party_models(config)
    normalized = _normalize_registry_item(item)
    normalized_key = _dedupe_key(normalized)
    for index, existing in enumerate(models):
        if existing["id"] == normalized["id"] or _dedupe_key(existing) == normalized_key:
            normalized["id"] = existing.get("id") or normalized["id"]
            normalized["created_at"] = existing.get("created_at") or normalized["created_at"]
            models[index] = normalized
            save_third_party_models(config, models)
            return normalized
    models.append(normalized)
    save_third_party_models(config, models)
    return normalized


def delete_third_party_model(config: AppConfig, item_id: str) -> bool:
    models = load_third_party_models(config)
    kept = [item for item in models if item.get("id") != item_id]
    if len(kept) == len(models):
        return False
    save_third_party_models(config, kept)
    return True


def registry_item_to_model_record(item: Dict) -> ModelRecord:
    roles = _roles_to_stage_suitable(item.get("roles") or [])
    supports_vision = item.get("supports_vision")
    provider = item.get("provider") or "openai_compatible"
    model_id = item.get("model_id") or ""
    record = ModelRecord(
        model_id=model_id,
        provider=provider,
        family=infer_family(model_id),
        stage_suitable=roles,
        supports_vision=supports_vision,
        supports_openai_chat=(provider in SUPPORTED_PROVIDERS),
        supports_dashscope_native=(provider == "dashscope"),
        input_price=item.get("input_price"),
        output_price=item.get("output_price"),
        price_source=item.get("price_source") or "third_party",
        note=_build_note(item),
    )
    verification = item.get("verification") or {}
    if verification.get("text"):
        record.openai_text_status = verification["text"]
    if verification.get("vision"):
        record.openai_vision_status = verification["vision"]
    if verification.get("dashscope"):
        record.dashscope_multimodal_status = verification["dashscope"]
    record.verified_at = item.get("updated_at")
    return record


def filter_registry_models(models: List[Dict], role: str) -> List[Dict]:
    return [item for item in models if _role_matches(item.get("roles") or [], role)]


def parse_bulk_models_text(raw_text: str, defaults: Optional[Dict] = None) -> List[Dict]:
    defaults = defaults or {}
    text = (raw_text or "").strip()
    if not text:
        return []

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            parsed = [parsed]
        if isinstance(parsed, list):
            items = []
            for obj in parsed:
                if isinstance(obj, dict):
                    merged = dict(defaults)
                    merged.update(obj)
                    items.append(_normalize_registry_item(merged))
            return items
    except Exception:
        pass

    items = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split(",") if part.strip()]
        if not parts:
            continue
        item = dict(defaults)
        item["model_id"] = parts[0]
        if len(parts) > 1:
            item["name"] = parts[1]
        if len(parts) > 2:
            item["roles"] = _parse_roles(parts[2])
        if len(parts) > 3:
            item["input_price"] = _safe_float(parts[3])
        if len(parts) > 4:
            item["output_price"] = _safe_float(parts[4])
        items.append(_normalize_registry_item(item))
    return items


def discover_openai_compatible_models(base_url: str, api_key: str, timeout: int = 15) -> List[Dict]:
    import urllib.request

    endpoint = f"{base_url.rstrip('/')}/models"
    req = urllib.request.Request(
        endpoint,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read().decode("utf-8", errors="replace"))

    data = body.get("data") if isinstance(body, dict) else None
    if not isinstance(data, list):
        return []

    items = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        model_id = str(entry.get("id") or "").strip()
        if not model_id:
            continue
        supports_vision = _infer_supports_vision_from_model_id(model_id)
        items.append(
            _normalize_registry_item(
                {
                    "provider": "openai_compatible",
                    "base_url": base_url,
                    "api_key_env": "OPENAI_API_KEY",
                    "model_id": model_id,
                    "name": model_id,
                    "roles": [ROLE_VISION, ROLE_BRAIN] if supports_vision else [ROLE_BRAIN],
                    "supports_vision": supports_vision,
                    "supports_thinking": None,
                    "price_source": "discovered:/models",
                }
            )
        )
    return items


def _normalize_registry_item(item: Dict) -> Dict:
    now = _now_iso()
    roles = _parse_roles(item.get("roles"))
    return {
        "id": item.get("id") or str(uuid.uuid4()),
        "name": (item.get("name") or item.get("display_name") or item.get("model_id") or "未命名模型").strip(),
        "provider": (item.get("provider") or "openai_compatible").strip(),
        "base_url": (item.get("base_url") or "").strip(),
        "api_key_env": (item.get("api_key_env") or "OPENAI_API_KEY").strip(),
        "model_id": (item.get("model_id") or "").strip(),
        "roles": roles,
        "supports_vision": item.get("supports_vision"),
        "supports_thinking": item.get("supports_thinking"),
        "input_price": _safe_float(item.get("input_price")),
        "output_price": _safe_float(item.get("output_price")),
        "price_source": (item.get("price_source") or "manual").strip(),
        "note": (item.get("note") or "").strip(),
        "verification": item.get("verification") or {},
        "created_at": item.get("created_at") or now,
        "updated_at": now,
    }


def _parse_roles(value) -> List[str]:
    if isinstance(value, str):
        raw_roles = [segment.strip().lower() for segment in value.replace("/", ",").split(",")]
    elif isinstance(value, list):
        raw_roles = [str(segment).strip().lower() for segment in value]
    else:
        raw_roles = []

    roles = []
    for role in raw_roles:
        if role in SUPPORTED_ROLES and role not in roles:
            roles.append(role)
    if not roles:
        roles = [ROLE_BRAIN]
    if ROLE_BOTH in roles:
        return [ROLE_VISION, ROLE_BRAIN]
    return roles


def _roles_to_stage_suitable(roles: List[str]) -> List[str]:
    normalized = _parse_roles(roles)
    result = []
    if ROLE_VISION in normalized:
        result.append(ROLE_VISION)
    if ROLE_BRAIN in normalized:
        result.append(ROLE_BRAIN)
    return result


def _role_matches(roles: List[str], role: str) -> bool:
    normalized = _parse_roles(roles)
    return role in normalized


def _safe_float(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _dedupe_key(item: Dict):
    return (
        (item.get("provider") or "").strip().lower(),
        (item.get("base_url") or "").strip().rstrip("/").lower(),
        (item.get("api_key_env") or "").strip(),
        (item.get("model_id") or "").strip().lower(),
    )


def _build_note(item: Dict) -> str:
    segments = []
    if item.get("name") and item.get("name") != item.get("model_id"):
        segments.append(f"别名: {item['name']}")
    if item.get("note"):
        segments.append(item["note"])
    return " | ".join(segments)


def _infer_supports_vision_from_model_id(model_id: str) -> Optional[bool]:
    lid = model_id.lower()
    keywords = ("vision", "vl", "omni", "image", "multimodal")
    return True if any(keyword in lid for keyword in keywords) else None


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
