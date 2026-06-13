from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from . import __version__
from .backup import backup_status
from .config import Settings
from .db import database_status
from .license import load_license


HEARTBEAT_PROTOCOL_VERSION = "2026-06-10.p0"


def _health_status(license_status: str, db_status: str) -> str:
    if license_status == "valid" and db_status == "ready":
        return "ok"
    if license_status in {"missing_config", "unsigned"} or db_status == "missing_config":
        return "partial"
    if license_status in {"invalid", "expired"} or db_status in {"unavailable", "failed", "missing_dependency"}:
        return "degraded"
    return "unknown"


def build_platform_heartbeat(settings: Settings) -> dict[str, Any]:
    license_state = load_license(settings.license_file, settings.license_secret)
    db_state = database_status(settings)
    backup_state = backup_status(settings)
    organization_id = license_state.organization_id or "missing_config"
    license_id = license_state.license_id or "missing_config"
    server_id = settings.server_id or "missing_config"

    return {
        "protocol_version": HEARTBEAT_PROTOCOL_VERSION,
        "server_id": server_id,
        "organization_id": organization_id,
        "license_id": license_id,
        "license_status": license_state.status,
        "hermes_version": __version__,
        "health_status": _health_status(license_state.status, db_state.status),
        "database_status": db_state.status,
        "database": asdict(db_state),
        "backup_status": backup_state.status,
        "backup": asdict(backup_state),
        "connector_status_summary": {},
        "error_count_24h": 0,
        "brand_key": settings.brand_key,
        "product": settings.product_name,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
