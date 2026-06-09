from __future__ import annotations

import json
import hmac
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LicenseState:
    status: str
    path: str
    license_id: str = ""
    organization_id: str = ""
    plan: str = ""
    expires_at: str = ""
    features: tuple[str, ...] = ()
    error: str = ""


SIGNATURE_FIELD = "signature"


def canonical_payload(payload: dict[str, Any]) -> bytes:
    unsigned = {key: value for key, value in payload.items() if key != SIGNATURE_FIELD}
    return json.dumps(unsigned, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def sign_license_payload(payload: dict[str, Any], secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), canonical_payload(payload), hashlib.sha256).hexdigest()


def _is_expired(value: str) -> bool:
    if not value:
        return False
    normalized = value.replace("Z", "+00:00")
    try:
        expires_at = datetime.fromisoformat(normalized)
    except ValueError:
        return True
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at <= datetime.now(timezone.utc)


def load_license(path: Path, secret: str = "") -> LicenseState:
    if not path.exists():
        return LicenseState(status="missing_config", path=str(path))
    try:
        payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return LicenseState(status="invalid", path=str(path), error=str(exc))

    if not secret:
        status = "unsigned"
        error = "BAIRUI_LICENSE_SECRET is not configured."
    else:
        expected = sign_license_payload(payload, secret)
        actual = str(payload.get(SIGNATURE_FIELD, ""))
        if not actual:
            status = "invalid"
            error = "license signature is missing."
        elif not hmac.compare_digest(actual, expected):
            status = "invalid"
            error = "license signature is invalid."
        elif _is_expired(str(payload.get("expires_at", ""))):
            status = "expired"
            error = "license is expired."
        else:
            status = "valid"
            error = ""

    features = payload.get("features", [])
    if not isinstance(features, list):
        features = []

    return LicenseState(
        status=status,
        path=str(path),
        license_id=str(payload.get("license_id", "")),
        organization_id=str(payload.get("organization_id", "")),
        plan=str(payload.get("plan", payload.get("plan_code", ""))),
        expires_at=str(payload.get("expires_at", "")),
        features=tuple(str(item) for item in features),
        error=error,
    )
