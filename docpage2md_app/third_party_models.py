import json
import math
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .aliyun_catalog import ModelRecord, infer_family
from .config import AppConfig
from .files import write_json
from .model_catalog import ROLE_BRAIN, ROLE_VISION

ROLE_BOTH = "both"
REGISTRY_SCHEMA_VERSION = 1
SUPPORTED_PROVIDERS = {
    "dashscope",
    "dashscope_openai",
    "deepseek",
    "openai_compatible",
}
SUPPORTED_ROLES = {ROLE_VISION, ROLE_BRAIN, ROLE_BOTH}


def load_third_party_models(config: AppConfig) -> List[Dict]:
    records, error = _read_registry_records(config)
    if error:
        return []
    items = []
    for item in records:
        if not isinstance(item, dict):
            continue
        normalized = _normalize_registry_item(item, preserve_timestamps=True)
        if normalized["model_id"]:
            items.append(normalized)
    return items


def save_third_party_models(config: AppConfig, models: List[Dict]):
    config.log_path.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": REGISTRY_SCHEMA_VERSION,
        "updated_at": _now_iso(),
        "models": [_normalize_registry_item(item, preserve_timestamps=True) for item in models if item.get("model_id")],
    }
    write_json(config.third_party_models_path, payload)


def upsert_third_party_model(config: AppConfig, item: Dict) -> Dict:
    _, error = _read_registry_records(config)
    if error:
        raise ValueError(f"第三方模型注册表无法读取，已拒绝覆盖: {error}")

    models = load_third_party_models(config)
    normalized = _normalize_registry_item(item)
    if not normalized["model_id"]:
        raise ValueError("model_id 不能为空。")
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


def update_third_party_model_verification(
    config: AppConfig,
    item_id: str,
    role: str,
    status: str,
    error: str = "",
) -> Dict:
    _, read_error = _read_registry_records(config)
    if read_error:
        raise ValueError(f"第三方模型注册表无法读取，已拒绝覆盖: {read_error}")

    models = load_third_party_models(config)
    verification_key = "vision" if role == ROLE_VISION else "text"
    normalized_status = "ok" if status == "ok" else "failed"
    for index, item in enumerate(models):
        if item.get("id") != item_id:
            continue
        updated = dict(item)
        verification = dict(updated.get("verification") or {})
        verification[verification_key] = normalized_status
        verification[f"{verification_key}_raw_status"] = status
        if error:
            verification[f"{verification_key}_error"] = error[:500]
        else:
            verification.pop(f"{verification_key}_error", None)
        verification[f"{verification_key}_checked_at"] = _now_iso()
        updated["verification"] = verification
        updated["updated_at"] = _now_iso()
        models[index] = updated
        save_third_party_models(config, models)
        return load_third_party_models(config)[index]
    raise ValueError(f"未找到第三方模型: {item_id}")


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
                    normalized = _normalize_registry_item(merged)
                    if normalized["model_id"]:
                        items.append(normalized)
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
        normalized = _normalize_registry_item(item)
        if normalized["model_id"]:
            items.append(normalized)
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


def _read_registry_records(config: AppConfig):
    path = config.third_party_models_path
    if not path.exists():
        return [], None
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        return [], str(exc)

    if isinstance(data, list):
        return data, None

    if not isinstance(data, dict):
        return [], "registry root must be an object or legacy list"

    version = data.get("version", REGISTRY_SCHEMA_VERSION)
    if version != REGISTRY_SCHEMA_VERSION:
        return [], f"unsupported registry schema version {version}"

    records = data.get("models")
    if not isinstance(records, list):
        return [], "registry models must be a list"
    return records, None


def _normalize_registry_item(item: Dict, preserve_timestamps: bool = False) -> Dict:
    now = _now_iso()
    roles = _parse_roles(item.get("roles"))
    provider = (item.get("provider") or "openai_compatible").strip()
    if provider not in SUPPORTED_PROVIDERS:
        provider = "openai_compatible"
    return {
        "id": item.get("id") or str(uuid.uuid4()),
        "name": (item.get("name") or item.get("display_name") or item.get("model_id") or "未命名模型").strip(),
        "provider": provider,
        "base_url": _canonical_base_url(item.get("base_url") or ""),
        "api_key_env": _canonical_api_key_env(item.get("api_key_env") or "OPENAI_API_KEY"),
        "model_id": (item.get("model_id") or "").strip(),
        "roles": roles,
        "supports_vision": _coerce_optional_bool(item.get("supports_vision")),
        "supports_thinking": _coerce_optional_bool(item.get("supports_thinking")),
        "input_price": _safe_float(item.get("input_price")),
        "output_price": _safe_float(item.get("output_price")),
        "price_source": (item.get("price_source") or "manual").strip(),
        "note": (item.get("note") or "").strip(),
        "verification": item.get("verification") or {},
        "created_at": item.get("created_at") or now,
        "updated_at": item.get("updated_at") if preserve_timestamps and item.get("updated_at") else now,
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
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number < 0:
        return None
    return number


def _dedupe_key(item: Dict):
    return (
        (item.get("provider") or "").strip().lower(),
        _canonical_base_url(item.get("base_url") or "").lower(),
        _canonical_api_key_env(item.get("api_key_env") or ""),
        (item.get("model_id") or "").strip().lower(),
    )


def _canonical_base_url(base_url: str) -> str:
    return (base_url or "").strip().rstrip("/")


def _canonical_api_key_env(env_name: str) -> str:
    return (env_name or "OPENAI_API_KEY").strip().upper()


def _coerce_optional_bool(value):
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in ("true", "yes", "y", "1"):
            return True
        if normalized in ("false", "no", "n", "0"):
            return False
    return None


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
