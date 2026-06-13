from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .config import Settings


RESTORE_CONFIRMATION = "RESTORE BAIRUI POSTGRES"


@dataclass(frozen=True)
class BackupStatus:
    status: str
    detail: str
    backup_dir: str
    latest_backup: str
    restore_requires_confirmation: bool = True


def backup_root(settings: Settings) -> Path:
    return settings.data_dir / "backups" / "postgres"


def backup_status(settings: Settings) -> BackupStatus:
    root = backup_root(settings)
    if not settings.has_database:
        return BackupStatus(
            status="missing_config",
            detail="HERMES_DATABASE_URL is empty; PostgreSQL backup is not configured",
            backup_dir=str(root),
            latest_backup="",
        )
    latest = _latest_backup(root)
    if latest is None:
        return BackupStatus(
            status="not_ready",
            detail="PostgreSQL is configured, but no local backup artifact is recorded yet",
            backup_dir=str(root),
            latest_backup="",
        )
    return BackupStatus(
        status="ready",
        detail="At least one local PostgreSQL backup artifact is present",
        backup_dir=str(root),
        latest_backup=str(latest),
    )


def build_backup_plan(settings: Settings) -> dict[str, Any]:
    root = backup_root(settings)
    filename = f"bairui-postgres-{_timestamp()}.dump"
    output_path = root / filename
    db_ref = _database_reference(settings.database_url)
    return {
        "service": "bairui",
        "mode": "backup_plan",
        "status": "ready" if settings.has_database else "missing_config",
        "database": db_ref,
        "backup_dir": str(root),
        "output_path": str(output_path),
        "format": "custom",
        "command": f'pg_dump --format=custom --no-owner --no-privileges --file "{output_path}" "$HERMES_DATABASE_URL"',
        "secret_policy": "database URL and password are passed through HERMES_DATABASE_URL and are never printed",
        "creates_customer_data": True,
        "next_step": "Run the command on the server, then store the artifact in an access-controlled backup path.",
    }


def build_restore_plan(settings: Settings, backup_path: str, *, confirm: str = "") -> dict[str, Any]:
    path = Path(backup_path)
    db_ref = _database_reference(settings.database_url)
    confirmed = confirm == RESTORE_CONFIRMATION
    status = "ready" if settings.has_database and path.exists() and confirmed else "blocked"
    blockers: list[str] = []
    if not settings.has_database:
        blockers.append("HERMES_DATABASE_URL is empty")
    if not backup_path:
        blockers.append("backup path is required")
    elif not path.exists():
        blockers.append("backup artifact does not exist")
    if not confirmed:
        blockers.append(f'type confirmation phrase "{RESTORE_CONFIRMATION}"')
    return {
        "service": "bairui",
        "mode": "restore_plan",
        "status": status,
        "database": db_ref,
        "backup_path": str(path) if backup_path else "",
        "command": f'pg_restore --clean --if-exists --no-owner --no-privileges --dbname "$HERMES_DATABASE_URL" "{path}"',
        "confirmation_phrase": RESTORE_CONFIRMATION,
        "confirmed": confirmed,
        "blockers": blockers,
        "destructive": True,
        "secret_policy": "database URL and password are passed through HERMES_DATABASE_URL and are never printed",
        "next_step": "Run only during a maintenance window after taking a fresh backup and stopping write traffic.",
    }


def backup_payload(settings: Settings) -> dict[str, Any]:
    return asdict(backup_status(settings))


def _latest_backup(root: Path) -> Path | None:
    if not root.exists():
        return None
    candidates = [path for path in root.iterdir() if path.is_file() and path.suffix in {".dump", ".sql", ".backup"}]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _database_reference(database_url: str) -> dict[str, str]:
    if not database_url.strip():
        return {"configured": "false", "host": "", "port": "", "database": ""}
    parsed = urlparse(database_url)
    return {
        "configured": "true",
        "host": parsed.hostname or "",
        "port": str(parsed.port or ""),
        "database": parsed.path.lstrip("/") if parsed.path else "",
    }
