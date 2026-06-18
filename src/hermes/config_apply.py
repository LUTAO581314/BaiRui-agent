from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .config import Settings, local_config_path


FIELD_TO_ENV = {
    "model_base_url": "BAIRUI_MODEL_BASE_URL",
    "model_api_key": "BAIRUI_MODEL_API_KEY",
    "model_name": "BAIRUI_MODEL_NAME",
    "channel_enabled": "BAIRUI_CHANNELS_ENABLED",
    "document_output_dir": "MINERU_OUTPUT_DIR",
    "memory_vault_dir": "HERMES_OBSIDIAN_VAULT_DIR",
    "channel_targets_json": "BAIRUI_CHANNEL_TARGETS_JSON",
    "avatar_assets_dir": "BAIRUI_AVATAR_ASSETS_DIR",
    "avatar_default_model": "BAIRUI_AVATAR_DEFAULT_MODEL",
    "codegraph_root": "BAIRUI_CODEGRAPH_ROOT",
    "database_url": "HERMES_DATABASE_URL",
    "owner_token": "BAIRUI_OWNER_TOKEN",
    "feishu_verification_token": "FEISHU_VERIFICATION_TOKEN",
    "feishu_app_id": "FEISHU_APP_ID",
    "feishu_app_secret": "FEISHU_APP_SECRET",
    "wechat_official_token": "WECHAT_OFFICIAL_TOKEN",
    "wechat_official_app_id": "WECHAT_OFFICIAL_APP_ID",
    "wechat_official_app_secret": "WECHAT_OFFICIAL_APP_SECRET",
    "wecom_incoming_token": "WECOM_INCOMING_TOKEN",
    "wecom_bot_key": "WECOM_BOT_KEY",
    "discord_bot_token": "DISCORD_BOT_TOKEN",
}

SECRET_FIELDS = {
    "model_api_key",
    "database_url",
    "owner_token",
    "feishu_verification_token",
    "feishu_app_id",
    "feishu_app_secret",
    "wechat_official_token",
    "wechat_official_app_id",
    "wechat_official_app_secret",
    "wecom_incoming_token",
    "wecom_bot_key",
    "discord_bot_token",
}
PATH_FIELDS = {"document_output_dir", "memory_vault_dir", "avatar_assets_dir", "codegraph_root"}
HIGH_RISK_FIELDS = {"database_url", "owner_token", "memory_vault_dir", "channel_enabled", "channel_targets_json", "codegraph_root"}
DANGEROUS_CONFIRMATION_PHRASE = "APPLY BAIRUI CONFIG"
PATH_SCOPE_POLICY = "paths must stay inside the bairui workspace, configured data/log/vault roots, or ~/bairui / ~/.bairui"


def apply_local_config(settings: Settings, payload: dict[str, Any]) -> dict[str, Any]:
    """Persist owner-provided configuration without returning secret values."""

    values = payload.get("values", payload)
    if not isinstance(values, dict):
        return {"status": "invalid_request", "message": "values must be an object"}

    create_dirs = bool(payload.get("create_dirs", True))
    danger_confirmation = str(payload.get("danger_confirmation", "")).strip()
    existing = _read_existing(settings)
    applied: dict[str, str] = {}
    pending: dict[str, str] = {}
    errors: list[dict[str, str]] = []

    for field, env_key in FIELD_TO_ENV.items():
        if field not in values:
            continue
        raw_value = values.get(field)
        if raw_value is None:
            continue
        value = str(raw_value).strip()
        if not value and field in SECRET_FIELDS:
            continue
        if field == "channel_targets_json" and value:
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                errors.append({"field": field, "message": "channel_targets_json must be valid JSON"})
                continue
            if not isinstance(parsed, list):
                errors.append({"field": field, "message": "channel_targets_json must be a JSON array"})
                continue
        pending[env_key] = value
        applied[field] = "configured" if field in SECRET_FIELDS and value else value

    if errors:
        return {"status": "invalid_request", "errors": errors, "applied": _safe_applied(applied)}
    if not applied:
        return {"status": "no_changes", "applied": {}}
    dangerous_fields = sorted(field for field in applied if field in HIGH_RISK_FIELDS)
    if dangerous_fields and danger_confirmation != DANGEROUS_CONFIRMATION_PHRASE:
        return {
            "status": "confirmation_required",
            "message": "High-risk configuration changes require typed confirmation before they are saved.",
            "dangerous_fields": dangerous_fields,
            "confirmation_phrase": DANGEROUS_CONFIRMATION_PHRASE,
            "applied": _safe_applied(applied),
            "restart_required": True,
            "secret_policy": "secret values were not saved and are not returned",
        }

    for field, value in ((field, str(values.get(field, "")).strip()) for field in applied if field in PATH_FIELDS):
        if not value:
            continue
        scope_error = _path_scope_error(settings, field, value)
        if scope_error:
            return {
                "status": "invalid_request",
                "errors": [scope_error],
                "applied": _safe_applied(applied),
                "path_scope_policy": PATH_SCOPE_POLICY,
                "dangerous_fields": dangerous_fields,
                "restart_required": bool(dangerous_fields),
            }
        if create_dirs:
            try:
                Path(value).expanduser().mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                return {"status": "invalid_request", "errors": [{"field": field, "message": f"could not create directory: {exc}"}], "applied": _safe_applied(applied)}

    existing.update(pending)

    path = local_config_path(settings.data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"values": existing}, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "status": "saved",
        "path": str(path.expanduser().resolve()),
        "applied": _safe_applied(applied),
        "dangerous_fields": dangerous_fields,
        "path_scope_policy": PATH_SCOPE_POLICY,
        "restart_required": bool(dangerous_fields),
        "secret_policy": "secret values were saved locally but are not returned",
    }


def _read_existing(settings: Settings) -> dict[str, str]:
    path = local_config_path(settings.data_dir)
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    values = payload.get("values", {}) if isinstance(payload, dict) else {}
    if not isinstance(values, dict):
        return {}
    return {str(key): str(value) for key, value in values.items()}


def _safe_applied(applied: dict[str, str]) -> dict[str, str]:
    return {field: ("configured" if field in SECRET_FIELDS else value) for field, value in applied.items()}


def _path_scope_error(settings: Settings, field: str, raw_value: str) -> dict[str, str] | None:
    candidate = Path(raw_value).expanduser()
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    resolved = candidate.resolve(strict=False)
    if _is_forbidden_system_path(resolved):
        return {"field": field, "message": f"{field} is outside the allowed bairui path scope", "policy": PATH_SCOPE_POLICY}
    if any(_is_relative_to(resolved, root) for root in _allowed_path_roots(settings)):
        return None
    return {"field": field, "message": f"{field} is outside the allowed bairui path scope", "policy": PATH_SCOPE_POLICY}


def _allowed_path_roots(settings: Settings) -> tuple[Path, ...]:
    project_root = Path(__file__).resolve().parents[2]
    data_dir = settings.data_dir.expanduser().resolve(strict=False)
    log_dir = settings.log_dir.expanduser().resolve(strict=False)
    vault_dir = settings.obsidian_vault_dir.expanduser().resolve(strict=False)
    home = Path.home().expanduser().resolve(strict=False)
    roots = {
        project_root,
        data_dir,
        data_dir.parent,
        log_dir,
        log_dir.parent,
        vault_dir,
        vault_dir.parent,
        settings.avatar_assets_dir.expanduser().resolve(strict=False),
        settings.codegraph_root.expanduser().resolve(strict=False),
        home / "bairui",
        home / ".bairui",
    }
    return tuple(root for root in roots if str(root))


def _is_forbidden_system_path(path: Path) -> bool:
    anchor_roots = [Path(anchor) for anchor in {path.anchor} if anchor]
    if any(_norm(path) == _norm(root) for root in anchor_roots):
        return True
    forbidden_roots: list[Path] = []
    for env_name in ("SystemRoot", "WINDIR", "ProgramFiles", "ProgramFiles(x86)", "ProgramData"):
        value = os.getenv(env_name)
        if value:
            forbidden_roots.append(Path(value))
    normalized = _norm(path)
    return any(normalized == _norm(root) or normalized.startswith(_norm(root) + os.sep) for root in forbidden_roots if str(root))


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _norm(path: Path) -> str:
    return os.path.normcase(str(path.expanduser().resolve(strict=False)))
