import json
from dataclasses import replace
from typing import Dict, List

from .config import AppConfig
from .env import get_deepseek_api_key, get_env_value, set_user_env_value
from .model_catalog import (
    ROLE_BRAIN,
    ROLE_VISION,
    ModelPrice,
    load_model_catalog,
)
from .aliyun_catalog import (
    ModelRecord,
    filter_brain_models,
    filter_vision_models,
    verify_openai_chat_model,
    vision_recommendation_tier,
)
from .third_party_models import (
    discover_openai_compatible_models,
    filter_registry_models,
    load_third_party_models,
    parse_bulk_models_text,
    upsert_third_party_model,
    delete_third_party_model,
)


def configure_models(console, config: AppConfig):
    """交互式模型配置入口。使用动态+静态合并目录。"""
    console.print("[dim]正在加载模型目录（缓存优先，不联网）...[/]")
    records = load_model_catalog(
        prefer_cache=True,
        cache_path=config.model_cache_path,
    )
    console.print(f"[dim]已加载 {len(records)} 个官方模型。[/]")

    saved = load_model_settings(config)
    if saved:
        saved_config = apply_model_settings(config, saved)
        console.print(
            "[bold cyan]模型配置[/]: "
            f"Vision={saved_config.model_vision} | "
            f"Brain={saved_config.brain_provider}:{saved_config.model_brain}"
        )
        choice = input("👉 是否沿用上次模型配置？(y/n) [默认为 y]: ").strip().lower()
        if choice != "n":
            _ensure_api_keys_for_config(console, saved_config)
            return saved_config

    vision_config = choose_model(
        console=console,
        config=config,
        records=records,
        role=ROLE_VISION,
        title="Step 1 视觉模型",
        default_provider=config.vision_provider,
        default_model=config.model_vision,
    )
    final_config = choose_model(
        console=console,
        config=vision_config,
        records=records,
        role=ROLE_BRAIN,
        title="Step 2 Brain 模型",
        default_provider="deepseek" if get_deepseek_api_key() else config.brain_provider,
        default_model="deepseek-v4-flash" if get_deepseek_api_key() else config.model_brain,
    )

    if final_config.brain_provider == "deepseek" and not get_env_value(final_config.brain_api_key_env):
        console.print("[bold yellow]未检测到 DEEPSEEK_API_KEY，DeepSeek Brain 会失败。[/]")
        save_key = input("👉 是否现在粘贴并保存 DeepSeek API Key？(y/n) [默认为 y]: ").strip().lower()
        if save_key != "n":
            _prompt_and_save_api_key(console, final_config.brain_api_key_env)

    if final_config.brain_provider == "deepseek" and not get_env_value(final_config.brain_api_key_env):
        fallback = input("👉 改用 qwen-plus 吗？(y/n) [默认为 y]: ").strip().lower()
        if fallback != "n":
            final_config = replace(
                final_config,
                brain_provider="dashscope",
                model_brain="qwen-plus",
                brain_input_price_per_million=None,
                brain_output_price_per_million=None,
            )

    _ensure_api_keys_for_config(console, final_config)
    save_model_settings(config, final_config)
    return final_config


def choose_model(
    console,
    config: AppConfig,
    records: List[ModelRecord],
    role: str,
    title: str,
    default_provider: str,
    default_model: str,
):
    """模型选择：官方目录 + 第三方模型管理。"""
    if role == ROLE_VISION:
        candidates = filter_vision_models(records)
        candidates.sort(key=lambda r: (vision_recommendation_tier(r), r.model_id))
        _print_vision_candidates(console, candidates, title, default_provider, default_model)
    else:
        candidates = [
            r for r in filter_brain_models(records)
            if ROLE_BRAIN in getattr(r, "stage_suitable", []) or r.openai_text_status == "ok"
        ]
        _print_brain_candidates(console, candidates, title, default_provider, default_model)

    third_party_items = filter_registry_models(load_third_party_models(config), role)
    _print_third_party_candidates(console, third_party_items, role)

    display = candidates[:80]
    default_index = _find_record_index(display, default_provider, default_model)

    while True:
        selected = input(
            f">> 选择 [默认 {default_index}, t=第三方模型, c=新增第三方模型, m=管理第三方模型]: "
        ).strip().lower()
        if not selected:
            selected = str(default_index)

        if selected == "c":
            created = _create_third_party_model_wizard(console, config, role)
            if created:
                return _apply_registry_item(config, role, created)
            _print_third_party_candidates(console, filter_registry_models(load_third_party_models(config), role), role)
            continue

        if selected == "m":
            chosen = _manage_third_party_models(console, config, role)
            if chosen:
                return _apply_registry_item(config, role, chosen)
            _print_third_party_candidates(console, filter_registry_models(load_third_party_models(config), role), role)
            continue

        if selected == "t":
            chosen = _select_third_party_model(console, config, role)
            if chosen:
                return _apply_registry_item(config, role, chosen)
            continue

        try:
            index = int(selected)
        except ValueError:
            index = default_index
        if not 1 <= index <= len(display):
            index = default_index
        return _apply_record(config, role, display[index - 1])


def _print_vision_candidates(console, candidates, title, default_provider, default_model):
    """紧凑版 Vision 模型列表。"""
    tier_labels = {0: "REC", 1: "CAN", 2: "FAIL"}
    console.print(f"\n[bold cyan]{title}[/] [dim](REC=已验证推荐 CAN=候选 FAIL=验证失败)[/]")
    console.print(f"[dim]{'':>3} {'Tier':4} {'Model ID':30} {'Vision':8} {'Price(in/out)/M':18} {'Source':10}[/]")
    console.print("[dim]" + "-" * 86 + "[/]")

    default_index = _find_record_index(candidates, default_provider, default_model)

    for i, rec in enumerate(candidates[:80], start=1):
        marker = "*" if i == default_index else " "
        tier = vision_recommendation_tier(rec)
        tier_label = tier_labels.get(tier, "   ")

        ov = _cap_icon(rec.openai_vision_status)
        dm = _cap_icon(rec.dashscope_multimodal_status)
        vis_status = f"{ov}/{dm}"

        inp = f"{rec.input_price:.3g}" if rec.input_price is not None else "?"
        out = f"{rec.output_price:.3g}" if rec.output_price is not None else "?"
        price = f"{inp}/{out}"
        src = (rec.price_source or "-")[:10]

        line = f"{marker}{i:>2d}  {tier_label:4} {rec.model_id:30} {vis_status:8} {price:18} {src:10}"
        style = ""
        if tier == 0:
            style = "green"
        elif tier == 2:
            style = "red"
        elif tier == 1:
            style = "dim"

        if style:
            console.print(f"[{style}]{line}[/]")
        else:
            console.print(line)

    console.print(f"[dim]{'t':>3}  {'3P':4} {'已保存第三方模型':30}[/]")
    console.print(f"[dim]{'c':>3}  {'ADD':4} {'新增第三方模型':30}[/]")
    console.print(f"[dim]{'m':>3}  {'MGR':4} {'管理第三方模型':30}[/]")
    console.print()


def _print_brain_candidates(console, candidates, title, default_provider, default_model):
    """紧凑版 Brain 模型列表。"""
    console.print(f"\n[bold cyan]{title}[/] [dim](文本模型 + 多模态，多模态用于 Brain 成本可能更高)[/]")
    console.print(f"[dim]{'':>3} {'':4} {'Model ID':30} {'Text':6} {'Price(in/out)/M':18} {'Source':10} {'Provider':10}[/]")
    console.print("[dim]" + "-" * 86 + "[/]")

    default_index = _find_record_index(candidates, default_provider, default_model)

    for i, rec in enumerate(candidates[:80], start=1):
        marker = "*" if i == default_index else " "
        txt = _cap_icon(rec.openai_text_status)

        inp = f"{rec.input_price:.3g}" if rec.input_price is not None else "?"
        out = f"{rec.output_price:.3g}" if rec.output_price is not None else "?"
        price = f"{inp}/{out}"
        src = (rec.price_source or "-")[:10]
        prov = rec.provider[:10]

        style = "green" if rec.openai_text_status == "ok" else ""
        line = f"{marker}{i:>2d}  {'':4} {rec.model_id:30} {txt:6} {price:18} {src:10} {prov:10}"
        if style:
            console.print(f"[{style}]{line}[/]")
        else:
            console.print(line)

    console.print(f"[dim]{'t':>3}  {'3P':4} {'已保存第三方模型':30}[/]")
    console.print(f"[dim]{'c':>3}  {'ADD':4} {'新增第三方模型':30}[/]")
    console.print(f"[dim]{'m':>3}  {'MGR':4} {'管理第三方模型':30}[/]")
    console.print()


def _print_third_party_candidates(console, items, role: str):
    role_label = "Vision" if role == ROLE_VISION else "Brain"
    console.print(f"[bold magenta]第三方模型（适用于 {role_label}）[/]")
    if not items:
        console.print("[dim]  暂无已保存的第三方模型。可输入 c 新增，或输入 m 进入管理菜单。[/]")
        return
    for index, item in enumerate(items, start=1):
        roles = "/".join(item.get("roles") or [])
        provider = item.get("provider") or "openai_compatible"
        model_id = item.get("model_id") or "-"
        alias = item.get("name") or model_id
        price = _format_registry_price(item)
        console.print(f"  [magenta]{index}.[/] {alias} -> {model_id} [{provider}] roles={roles} {price}")
    console.print("[dim]输入 t 可从已保存第三方模型中直接选择。[/]")


def _cap_icon(status: str) -> str:
    if status == "ok":
        return "✅"
    if status == "failed":
        return "❌"
    if status == "skipped":
        return "⏭"
    return "·"


def _find_record_index(records, provider, model_id):
    for i, rec in enumerate(records, start=1):
        if rec.provider == provider and rec.model_id == model_id:
            return i
    return 1


def _apply_record(config: AppConfig, role: str, rec: ModelRecord):
    base_url, api_key_env = _provider_defaults(rec.provider, role, config)
    if role == ROLE_VISION:
        return replace(
            config,
            vision_provider=rec.provider,
            model_vision=rec.model_id,
            vision_base_url=base_url,
            vision_api_key_env=api_key_env,
            vision_input_price_per_million=rec.input_price,
            vision_output_price_per_million=rec.output_price,
        )
    return replace(
        config,
        brain_provider=rec.provider,
        model_brain=rec.model_id,
        brain_base_url=base_url,
        brain_api_key_env=api_key_env,
        brain_input_price_per_million=rec.input_price,
        brain_output_price_per_million=rec.output_price,
    )


def _apply_registry_item(config: AppConfig, role: str, item: Dict):
    if role == ROLE_VISION:
        return replace(
            config,
            vision_provider=item.get("provider") or config.vision_provider,
            model_vision=item.get("model_id") or config.model_vision,
            vision_base_url=item.get("base_url") or config.vision_base_url,
            vision_api_key_env=item.get("api_key_env") or config.vision_api_key_env,
            vision_input_price_per_million=item.get("input_price"),
            vision_output_price_per_million=item.get("output_price"),
        )
    return replace(
        config,
        brain_provider=item.get("provider") or config.brain_provider,
        model_brain=item.get("model_id") or config.model_brain,
        brain_base_url=item.get("base_url") or config.brain_base_url,
        brain_api_key_env=item.get("api_key_env") or config.brain_api_key_env,
        brain_input_price_per_million=item.get("input_price"),
        brain_output_price_per_million=item.get("output_price"),
    )


def _provider_defaults(provider, role, config: AppConfig):
    if provider == "deepseek":
        return "https://api.deepseek.com", "DEEPSEEK_API_KEY"
    if provider in ("dashscope", "dashscope_openai"):
        return config.openai_base_url, "DASHSCOPE_API_KEY"
    return (
        config.vision_base_url if role == ROLE_VISION else config.brain_base_url,
        config.vision_api_key_env if role == ROLE_VISION else config.brain_api_key_env,
    )


def _select_third_party_model(console, config: AppConfig, role: str):
    items = filter_registry_models(load_third_party_models(config), role)
    if not items:
        console.print("[yellow]当前没有可用的第三方模型。[/]")
        return None
    _print_third_party_candidates(console, items, role)
    selected = input("   请输入第三方模型编号 [回车取消]: ").strip()
    if not selected:
        return None
    try:
        index = int(selected)
    except ValueError:
        console.print("[yellow]编号无效。[/]")
        return None
    if not 1 <= index <= len(items):
        console.print("[yellow]编号超出范围。[/]")
        return None
    return items[index - 1]


def _manage_third_party_models(console, config: AppConfig, role: str):
    while True:
        items = load_third_party_models(config)
        console.print("\n[bold magenta]第三方模型管理[/]")
        if items:
            for index, item in enumerate(items, start=1):
                roles = "/".join(item.get("roles") or [])
                console.print(
                    f"  [{index}] {item.get('name')} -> {item.get('model_id')} "
                    f"[{item.get('provider')}] roles={roles}"
                )
        else:
            console.print("[dim]当前还没有保存任何第三方模型。[/]")

        console.print("[dim]可选操作: a=新增, b=批量导入, d=自动发现, e=编辑, x=删除, s=选择, q=返回[/]")
        action = input("   操作: ").strip().lower()
        if action in ("q", "quit", ""):
            return None
        if action == "a":
            created = _create_third_party_model_wizard(console, config, role)
            if created:
                use_now = input("   已保存。立即用于当前步骤吗？(y/n) [默认 y]: ").strip().lower()
                if use_now != "n":
                    return created
            continue
        if action == "b":
            _bulk_import_third_party_models(console, config, role)
            continue
        if action == "d":
            discovered = _discover_and_import_models(console, config, role)
            if discovered:
                return discovered
            continue
        if action == "e":
            _edit_third_party_model(console, config)
            continue
        if action == "x":
            _delete_third_party_model(console, config)
            continue
        if action == "s":
            chosen = _select_third_party_model(console, config, role)
            if chosen:
                return chosen
            continue
        console.print("[yellow]未知操作，请重试。[/]")


def _create_third_party_model_wizard(console, config: AppConfig, role: str):
    console.print("\n[bold]新增第三方模型[/]")
    provider, base_url, api_key_env = _read_custom_provider(console, config, role)
    model_id = input("   模型 ID: ").strip()
    if not model_id:
        console.print("   [yellow]模型 ID 不能为空。[/]")
        return None

    name = input(f"   显示名称/别名 [默认 {model_id}]: ").strip() or model_id
    default_roles = role if role in (ROLE_VISION, ROLE_BRAIN) else ROLE_BRAIN
    roles_raw = input(f"   用途角色 (vision/brain/both) [默认 {default_roles}]: ").strip() or default_roles
    supports_vision = _ask_supports_vision(role)
    input_price = _read_optional_float("   输入价格 元/百万 tokens (未知可回车): ")
    output_price = _read_optional_float("   输出价格 元/百万 tokens (未知可回车): ")
    note = input("   备注 [可回车]: ").strip()

    item = {
        "name": name,
        "provider": provider,
        "base_url": base_url,
        "api_key_env": api_key_env,
        "model_id": model_id,
        "roles": roles_raw,
        "supports_vision": supports_vision,
        "supports_thinking": None,
        "input_price": input_price,
        "output_price": output_price,
        "note": note,
    }

    verify_choice = input("   要立即验证该模型吗？(y/n) [默认 n]: ").strip().lower()
    if verify_choice == "y":
        item["verification"] = _verify_registry_item(console, item, role)

    saved = upsert_third_party_model(config, item)
    console.print(f"   [green]已保存第三方模型: {saved['name']}[/]")
    return saved


def _bulk_import_third_party_models(console, config: AppConfig, role: str):
    console.print("\n[bold]批量导入第三方模型[/]")
    provider, base_url, api_key_env = _read_custom_provider(console, config, role)
    default_roles = input(f"   默认角色 (vision/brain/both) [默认 {role}]: ").strip() or role
    console.print("   [dim]请输入 JSON 数组，或每行一个模型：model_id, 名称, roles, input_price, output_price[/]")
    console.print("   [dim]输入空行结束。[/]")
    lines = []
    while True:
        line = input()
        if not line.strip():
            break
        lines.append(line)
    parsed = parse_bulk_models_text(
        "\n".join(lines),
        defaults={
            "provider": provider,
            "base_url": base_url,
            "api_key_env": api_key_env,
            "roles": default_roles,
        },
    )
    if not parsed:
        console.print("   [yellow]没有解析出任何模型。[/]")
        return
    for item in parsed:
        upsert_third_party_model(config, item)
    console.print(f"   [green]已导入 {len(parsed)} 个第三方模型。[/]")


def _discover_and_import_models(console, config: AppConfig, role: str):
    console.print("\n[bold]自动发现 OpenAI-compatible 模型[/]")
    provider = "openai_compatible"
    default_base, default_env = _provider_defaults(provider, role, config)
    base_url = input(f"   Base URL [默认 {default_base}]: ").strip() or default_base
    api_key_env = input(f"   API Key 环境变量名 [默认 {default_env}]: ").strip() or default_env
    if not get_env_value(api_key_env):
        console.print(f"   [yellow]当前未检测到环境变量 {api_key_env}。[/]")
        save_key = input("   是否现在粘贴 API Key 并保存到当前用户环境变量？(y/n) [默认 n]: ").strip().lower()
        if save_key == "y":
            _prompt_and_save_api_key(console, api_key_env, indent="   ")
    api_key = get_env_value(api_key_env)
    if not api_key:
        console.print("   [yellow]没有 API Key，无法自动发现。[/]")
        return None

    try:
        discovered = discover_openai_compatible_models(base_url, api_key)
    except Exception as exc:
        console.print(f"   [red]自动发现失败: {exc}[/]")
        return None

    if not discovered:
        console.print("   [yellow]没有发现可导入的模型。[/]")
        return None

    console.print(f"   [green]发现 {len(discovered)} 个模型。[/]")
    for index, item in enumerate(discovered, start=1):
        roles = "/".join(item.get("roles") or [])
        console.print(f"     [{index}] {item['model_id']} roles={roles}")
    choice = input("   输入要导入的编号（逗号分隔，a=全部，回车取消）: ").strip().lower()
    if not choice:
        return None
    if choice == "a":
        selected = discovered
    else:
        selected = []
        try:
            indexes = [int(part.strip()) for part in choice.split(",") if part.strip()]
        except ValueError:
            console.print("   [yellow]编号格式无效。[/]")
            return None
        for index in indexes:
            if 1 <= index <= len(discovered):
                selected.append(discovered[index - 1])
    if not selected:
        console.print("   [yellow]没有选中任何模型。[/]")
        return None

    for item in selected:
        item["api_key_env"] = api_key_env
        upsert_third_party_model(config, item)
    console.print(f"   [green]已导入 {len(selected)} 个模型。[/]")

    use_now = input("   是否立刻从已导入模型中选一个用于当前步骤？(y/n) [默认 y]: ").strip().lower()
    if use_now == "n":
        return None
    return _select_third_party_model(console, config, role)


def _edit_third_party_model(console, config: AppConfig):
    items = load_third_party_models(config)
    if not items:
        console.print("[yellow]没有可编辑的第三方模型。[/]")
        return
    for index, item in enumerate(items, start=1):
        console.print(f"  [{index}] {item['name']} -> {item['model_id']}")
    selected = input("   输入要编辑的编号 [回车取消]: ").strip()
    if not selected:
        return
    try:
        index = int(selected)
    except ValueError:
        console.print("[yellow]编号无效。[/]")
        return
    if not 1 <= index <= len(items):
        console.print("[yellow]编号超出范围。[/]")
        return

    item = dict(items[index - 1])
    item["name"] = input(f"   名称 [当前 {item['name']}]: ").strip() or item["name"]
    item["model_id"] = input(f"   模型 ID [当前 {item['model_id']}]: ").strip() or item["model_id"]
    item["base_url"] = input(f"   Base URL [当前 {item['base_url']}]: ").strip() or item["base_url"]
    item["api_key_env"] = input(f"   API Key 环境变量名 [当前 {item['api_key_env']}]: ").strip() or item["api_key_env"]
    roles_default = "/".join(item.get("roles") or []) or ROLE_BRAIN
    item["roles"] = input(f"   roles [当前 {roles_default}]: ").strip() or roles_default
    new_input = input(f"   输入价格 [当前 {item.get('input_price')}]: ").strip()
    if new_input:
        item["input_price"] = _safe_float_from_text(new_input)
    new_output = input(f"   输出价格 [当前 {item.get('output_price')}]: ").strip()
    if new_output:
        item["output_price"] = _safe_float_from_text(new_output)
    item["note"] = input(f"   备注 [当前 {item.get('note', '')}]: ").strip() or item.get("note", "")
    item["supports_vision"] = _ask_supports_vision_from_current(item.get("supports_vision"))

    verify_choice = input("   是否重新验证该模型？(y/n) [默认 n]: ").strip().lower()
    if verify_choice == "y":
        role = ROLE_VISION if ROLE_VISION in (item.get("roles") or []) else ROLE_BRAIN
        item["verification"] = _verify_registry_item(console, item, role)

    upsert_third_party_model(config, item)
    console.print("   [green]已更新。[/]")


def _delete_third_party_model(console, config: AppConfig):
    items = load_third_party_models(config)
    if not items:
        console.print("[yellow]没有可删除的第三方模型。[/]")
        return
    for index, item in enumerate(items, start=1):
        console.print(f"  [{index}] {item['name']} -> {item['model_id']}")
    selected = input("   输入要删除的编号 [回车取消]: ").strip()
    if not selected:
        return
    try:
        index = int(selected)
    except ValueError:
        console.print("[yellow]编号无效。[/]")
        return
    if not 1 <= index <= len(items):
        console.print("[yellow]编号超出范围。[/]")
        return
    item = items[index - 1]
    confirm = input(f"   确认删除 {item['name']} ? (y/n) [默认 n]: ").strip().lower()
    if confirm != "y":
        return
    delete_third_party_model(config, item["id"])
    console.print("   [green]已删除。[/]")


def _verify_registry_item(console, item: Dict, role: str):
    api_key_env = item.get("api_key_env") or "OPENAI_API_KEY"
    api_key = get_env_value(api_key_env)
    if not api_key:
        console.print(f"   [yellow]未检测到 {api_key_env}，跳过验证。[/]")
        return {}
    base_url = item.get("base_url") or ""
    is_vision = role == ROLE_VISION or bool(item.get("supports_vision"))
    console.print(f"   [dim]正在验证 {item.get('model_id')} ...[/]", end="")
    status, error = verify_openai_chat_model(
        item.get("model_id") or "",
        api_key,
        base_url,
        is_vision=is_vision,
    )
    icon = "✅" if status == "ok" else "❌"
    summary = (error or "OK")[:120].replace("\n", " ")
    console.print(f" {icon} [{status}] {summary}")
    return {
        "vision" if is_vision else "text": "ok" if status == "ok" else "failed"
    }


def _read_custom_provider(console, config: AppConfig, role: str):
    console.print("\n[bold]自定义 API 类型[/]")
    options = [
        ("1", "dashscope", "阿里云 DashScope 原生接口，适合 Vision 默认路径"),
        ("2", "dashscope_openai", "阿里云 OpenAI 兼容接口"),
        ("3", "deepseek", "DeepSeek OpenAI 兼容接口，适合 Brain"),
        ("4", "openai_compatible", "其他 OpenAI 兼容服务，例如 One API、OpenRouter、LiteLLM、自建转发"),
    ]
    for key, provider, desc in options:
        console.print(f"   [{key}] {provider} - {desc}")

    default_choice = "1" if role == ROLE_VISION else "3"
    choice = input(f"   选择 API 类型 [默认 {default_choice}]: ").strip() or default_choice
    provider = next((p for key, p, _ in options if key == choice), None) or choice.strip().lower()

    if role == ROLE_VISION and provider == "deepseek":
        console.print("   [yellow]DeepSeek 当前不支持图片输入，Vision 已改为 openai_compatible。[/]")
        provider = "openai_compatible"

    default_base, default_env = _provider_defaults(provider, role, config)
    base_url = default_base
    if provider != "dashscope":
        base_url = input(f"   Base URL [默认 {default_base}]: ").strip() or default_base
    elif role == ROLE_VISION:
        console.print("   DashScope 原生 Vision 不需要填写 Base URL。")

    api_key_env = input(f"   API Key 环境变量名 [默认 {default_env}]: ").strip() or default_env
    if not get_env_value(api_key_env):
        console.print(f"   [yellow]当前未检测到环境变量 {api_key_env}。[/]")
        save_key = input("   是否现在粘贴 API Key 并保存到当前用户环境变量？(y/n) [默认 n]: ").strip().lower()
        if save_key == "y":
            _prompt_and_save_api_key(console, api_key_env, indent="   ")

    return provider, base_url, api_key_env


def _ensure_api_keys_for_config(console, config: AppConfig):
    required = [
        ("Step 1 Vision", config.vision_provider, config.vision_api_key_env),
        ("Step 2 Brain", config.brain_provider, config.brain_api_key_env),
    ]
    seen = set()
    for role, provider, env_name in required:
        if not env_name or env_name in seen:
            continue
        seen.add(env_name)
        if provider not in ("dashscope", "dashscope_openai", "deepseek", "openai_compatible"):
            continue
        if get_env_value(env_name):
            continue

        console.print(f"[yellow]{role} 需要环境变量 {env_name}，当前未检测到。[/]")
        save_key = input(f"👉 是否现在粘贴并保存 {env_name}？(y/n) [默认 n]: ").strip().lower()
        if save_key == "y":
            _prompt_and_save_api_key(console, env_name)


def _prompt_and_save_api_key(console, env_name: str, indent: str = ""):
    key_value = input(f"{indent}粘贴 API Key（不会写入仓库文件）: ").strip()
    if not key_value:
        return
    if set_user_env_value(env_name, key_value):
        console.print(f"{indent}[green]已写入用户环境变量 {env_name}。新开终端也可以读取。[/]")
    else:
        console.print(
            f"{indent}[yellow]已写入当前进程环境变量 {env_name}；"
            "若下次启动读不到，请手动设置系统环境变量。[/]"
        )


def load_model_settings(config: AppConfig):
    if not config.model_settings_path.exists():
        return None
    try:
        with config.model_settings_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_model_settings(base_config: AppConfig, selected_config: AppConfig):
    base_config.log_path.mkdir(parents=True, exist_ok=True)
    data = {
        "vision_provider": selected_config.vision_provider,
        "model_vision": selected_config.model_vision,
        "vision_base_url": selected_config.vision_base_url,
        "vision_api_key_env": selected_config.vision_api_key_env,
        "vision_input_price_per_million": selected_config.vision_input_price_per_million,
        "vision_output_price_per_million": selected_config.vision_output_price_per_million,
        "brain_provider": selected_config.brain_provider,
        "model_brain": selected_config.model_brain,
        "brain_base_url": selected_config.brain_base_url,
        "brain_api_key_env": selected_config.brain_api_key_env,
        "brain_input_price_per_million": selected_config.brain_input_price_per_million,
        "brain_output_price_per_million": selected_config.brain_output_price_per_million,
    }
    with base_config.model_settings_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def apply_model_settings(config: AppConfig, settings: Dict):
    return replace(
        config,
        vision_provider=settings.get("vision_provider", config.vision_provider),
        model_vision=settings.get("model_vision", config.model_vision),
        vision_base_url=settings.get("vision_base_url", config.vision_base_url),
        vision_api_key_env=settings.get("vision_api_key_env", config.vision_api_key_env),
        vision_input_price_per_million=settings.get("vision_input_price_per_million"),
        vision_output_price_per_million=settings.get("vision_output_price_per_million"),
        brain_provider=settings.get("brain_provider", config.brain_provider),
        model_brain=settings.get("model_brain", config.model_brain),
        brain_base_url=settings.get("brain_base_url", config.brain_base_url),
        brain_api_key_env=settings.get("brain_api_key_env", config.brain_api_key_env),
        brain_input_price_per_million=settings.get("brain_input_price_per_million"),
        brain_output_price_per_million=settings.get("brain_output_price_per_million"),
    )


def _read_optional_float(prompt):
    raw = input(prompt).strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _safe_float_from_text(raw: str):
    try:
        return float(raw)
    except ValueError:
        return None


def _ask_supports_vision(role: str):
    if role == ROLE_VISION:
        default = "y"
    else:
        default = "n"
    answer = input(f"   是否支持图片输入？(y/n/unknown) [默认 {default}]: ").strip().lower()
    if not answer:
        answer = default
    if answer in ("y", "yes"):
        return True
    if answer in ("n", "no"):
        return False
    return None


def _ask_supports_vision_from_current(current):
    default = "unknown"
    if current is True:
        default = "y"
    elif current is False:
        default = "n"
    answer = input(f"   是否支持图片输入？(y/n/unknown) [默认 {default}]: ").strip().lower()
    if not answer:
        answer = default
    if answer in ("y", "yes"):
        return True
    if answer in ("n", "no"):
        return False
    return None


def _format_registry_price(item: Dict):
    inp = item.get("input_price")
    out = item.get("output_price")
    if inp is None and out is None:
        return "[价格未知]"
    return f"[¥{inp if inp is not None else '?'} / ¥{out if out is not None else '?'}]"


def get_configured_price(config: AppConfig, role: str):
    if role == ROLE_VISION:
        return ModelPrice(
            input_per_million=config.vision_input_price_per_million,
            output_per_million=config.vision_output_price_per_million,
        )
    return ModelPrice(
        input_per_million=config.brain_input_price_per_million,
        output_per_million=config.brain_output_price_per_million,
    )
