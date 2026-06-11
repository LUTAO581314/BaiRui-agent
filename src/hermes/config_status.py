from __future__ import annotations

from pathlib import Path
from typing import Any

from .channels import channel_status
from .config import Settings


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
    return {
        "status": status,
        "secret_policy": "secrets are reported only as configured or missing; values are never returned",
        "items": items,
        "blockers": [f"{item['id']}: {item['detail']}" for item in blockers],
        "next_step": "Configure missing required items, then refresh Settings before running a customer demo.",
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
