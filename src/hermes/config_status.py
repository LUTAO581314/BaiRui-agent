from __future__ import annotations

from pathlib import Path
from typing import Any

from .channels import channel_status
from .config import Settings
from .config_apply import PATH_SCOPE_POLICY


def build_config_status(settings: Settings) -> dict[str, Any]:
    """Return operator-safe configuration diagnostics without secret values."""

    items = [
        _item(
            "model_gateway",
            "Model API",
            "ready" if settings.has_model_gateway else "missing_config",
            "OpenAI-compatible model endpoint. API key is reported only as configured or missing.",
            {
                "base_url": _configured_value(settings.model_base_url),
                "api_key": _secret_state(settings.model_api_key),
                "model": settings.model_name or "missing_config",
                "timeout_seconds": settings.model_timeout_seconds,
            },
        ),
        _item(
            "data_dir",
            "Data directory",
            _path_status(settings.data_dir),
            "Local JSONL product records live here until the PostgreSQL migration is activated.",
            {"path": _path_value(settings.data_dir)},
        ),
        _item(
            "document_output_dir",
            "Document output directory",
            _path_status(settings.mineru_output_dir),
            "Parsed document artifacts and report-ready outputs are written here.",
            {"path": _path_value(settings.mineru_output_dir), "backend": settings.mineru_backend, "device": settings.mineru_device},
        ),
        _item(
            "memory_vault",
            "Memory vault",
            _path_status(settings.obsidian_vault_dir),
            "Owner-reviewed memory notes and reports use this local vault path.",
            {"path": _path_value(settings.obsidian_vault_dir)},
        ),
        _item(
            "channel_targets",
            "Channel targets",
            channel_status(settings).status,
            "Outbound channel targets are approval-controlled; configuration never means automatic send.",
            {"target_count": channel_status(settings).configured_target_count, "will_send": False},
        ),
        _item(
            "avatar_assets",
            "Avatar assets",
            _path_status(settings.avatar_assets_dir),
            "Browser avatar models are validated locally. Backend records state only.",
            {"path": _path_value(settings.avatar_assets_dir), "default_model": settings.avatar_default_model or "missing_config"},
        ),
        _item(
            "codegraph_root",
            "CodeGraph root",
            _path_status(settings.codegraph_root),
            "CodeGraph stores source-structure indexes separately from long-term memory.",
            {"path": _path_value(settings.codegraph_root), "max_file_bytes": settings.codegraph_max_file_bytes},
        ),
        _item(
            "database",
            "Database",
            "configured" if settings.has_database else "missing_config",
            "Database URL is never returned; this only reports migration readiness.",
            {"database_url": _secret_state(settings.database_url), "jsonl_fallback": True},
        ),
        _item(
            "owner_gate",
            "Owner token gate",
            "configured" if settings.owner_token.strip() else "missing_config",
            "All write API calls require the local owner token when configured; token value is never returned.",
            {
                "owner_token": _secret_state(settings.owner_token),
                "protects": ["POST /* write APIs"],
                "accepted_headers": ["X-Bairui-Owner-Token", "Authorization: Bearer"],
            },
        ),
        _item(
            "license",
            "License",
            _path_status(settings.license_file.parent) if settings.license_file.exists() else "missing_config",
            "License file path is visible; license secret is never returned.",
            {"path": _path_value(settings.license_file), "secret": _secret_state(settings.license_secret)},
        ),
    ]
    required = {"model_gateway", "data_dir", "memory_vault", "codegraph_root"}
    blockers = [item for item in items if item["id"] in required and item["status"] in {"missing_config", "blocked", "error"}]
    status = "blocked" if blockers else "partial" if any(item["status"] == "missing_config" for item in items) else "ready"
    checklist = _build_checklist(settings, items, blockers)
    return {
        "status": status,
        "secret_policy": "secrets are reported only as configured or missing; values are never returned",
        "items": items,
        "blockers": [f"{item['id']}: {item['detail']}" for item in blockers],
        "next_step": "Configure missing required items, then refresh Settings before running a customer demo.",
        "checklist": checklist,
    }


def _item(id: str, label: str, status: str, detail: str, fields: dict[str, Any]) -> dict[str, Any]:
    return {"id": id, "label": label, "status": status, "detail": detail, "fields": fields}


def _path_status(path: Path) -> str:
    return "ready" if path.exists() else "missing_config"


def _path_value(path: Path) -> str:
    return str(path.expanduser().resolve())


def _secret_state(value: str) -> str:
    return "configured" if str(value or "").strip() else "missing_config"


def _configured_value(value: str) -> str:
    return str(value or "").strip() or "missing_config"


def _build_checklist(settings: Settings, items: list[dict[str, Any]], blockers: list[dict[str, Any]]) -> dict[str, Any]:
    required_ids = {"model_gateway", "data_dir", "memory_vault", "codegraph_root"}
    missing_required = [item["id"] for item in blockers]
    optional_missing = [item["id"] for item in items if item["id"] not in required_ids and item["status"] == "missing_config"]
    env_template = [
        "BAIRUI_MODEL_BASE_URL=https://your-model-gateway.example/v1",
        "BAIRUI_MODEL_API_KEY=<set-in-local-env-or-server-secret-store>",
        "BAIRUI_MODEL_NAME=<model-name>",
        f"HERMES_DATA_DIR={_path_value(settings.data_dir)}",
        f"HERMES_OBSIDIAN_VAULT_DIR={_path_value(settings.obsidian_vault_dir)}",
        f"MINERU_OUTPUT_DIR={_path_value(settings.mineru_output_dir)}",
        f"BAIRUI_CODEGRAPH_ROOT={_path_value(settings.codegraph_root)}",
        f"BAIRUI_AVATAR_ASSETS_DIR={_path_value(settings.avatar_assets_dir)}",
        "HERMES_DATABASE_URL=<optional-postgresql-url>",
        "BAIRUI_OWNER_TOKEN=<recommended-local-owner-token>",
        "BAIRUI_LICENSE_SECRET=<optional-license-value>",
        "BAIRUI_CHANNEL_TARGETS_JSON=<optional-owner-reviewed-channel-targets-json>",
    ]
    commands = [
        "python -m src.hermes config-status",
        "python -m src.hermes runtime-readiness",
        ".\\scripts\\config-doctor.ps1",
        ".\\scripts\\smoke-test.ps1 -FullAcceptance",
        "python -m src.hermes serve",
    ]
    steps = [
        _checklist_step(
            "model_gateway",
            "Configure model gateway",
            "ready" if settings.has_model_gateway else "missing_config",
            "Set BAIRUI_MODEL_BASE_URL, BAIRUI_MODEL_API_KEY, and BAIRUI_MODEL_NAME. The API key value is never returned by bairui.",
        ),
        _checklist_step("data_dir", "Verify data directory", _path_status(settings.data_dir), _path_value(settings.data_dir)),
        _checklist_step("memory_vault", "Verify memory vault", _path_status(settings.obsidian_vault_dir), _path_value(settings.obsidian_vault_dir)),
        _checklist_step("codegraph_root", "Verify CodeGraph root", _path_status(settings.codegraph_root), _path_value(settings.codegraph_root)),
        _checklist_step("documents", "Prepare document output", _path_status(settings.mineru_output_dir), _path_value(settings.mineru_output_dir)),
        _checklist_step("avatar", "Prepare Avatar assets", _path_status(settings.avatar_assets_dir), _path_value(settings.avatar_assets_dir)),
        _checklist_step("path_scope", "Keep local paths in the bairui scope", "required", PATH_SCOPE_POLICY),
        _checklist_step("channels", "Confirm channel approval boundary", channel_status(settings).status, "Configured targets create approval records only; will_send=false until a future sender is explicitly approved."),
        _checklist_step("database", "Optional PostgreSQL", "configured" if settings.has_database else "optional", "JSONL remains available for product beta; PostgreSQL URL is reported only as configured or missing."),
        _checklist_step("owner_gate", "Recommended owner token gate", "configured" if settings.owner_token else "recommended", "Set BAIRUI_OWNER_TOKEN before exposing the console beyond trusted local development. All POST write APIs require it when configured; token value is never returned."),
        _checklist_step("license", "Optional license gate", "configured" if settings.license_secret else "optional", "License secret is reported only as configured or missing."),
    ]
    markdown = _checklist_markdown(steps, env_template, commands, missing_required, optional_missing)
    return {
        "title": "bairui deployment checklist",
        "status": "blocked" if missing_required else "ready_for_demo" if not optional_missing else "ready_with_optional_gaps",
        "missing_required": missing_required,
        "optional_missing": optional_missing,
        "steps": steps,
        "env_template": env_template,
        "commands": commands,
        "markdown": markdown,
    }


def _checklist_step(id: str, title: str, status: str, detail: str) -> dict[str, str]:
    return {"id": id, "title": title, "status": status, "detail": detail}


def _checklist_markdown(
    steps: list[dict[str, str]],
    env_template: list[str],
    commands: list[str],
    missing_required: list[str],
    optional_missing: list[str],
) -> str:
    lines = [
        "# bairui deployment checklist",
        "",
        "## Required blockers",
        *(f"- {item}" for item in (missing_required or ["none"])),
        "",
        "## Optional gaps",
        *(f"- {item}" for item in (optional_missing or ["none"])),
        "",
        "## Steps",
        *(f"- [{step['status']}] {step['title']}: {step['detail']}" for step in steps),
        "",
        "## Environment template",
        "```env",
        *env_template,
        "```",
        "",
        "## Verification commands",
        "```powershell",
        *commands,
        "```",
        "",
        "Secret policy: values are reported only as configured or missing; bairui never returns secret values.",
    ]
    return "\n".join(lines)
