from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from ..config import Settings
from ..storage import create_audit_event


EVEROS_LICENSE = "Apache-2.0"
EVEROS_API_PREFIX = "/api/v1/memory"


@dataclass(frozen=True)
class EverOSStatus:
    status: str
    detail: str
    source_path: str
    license: str
    base_url: str
    memory_root: str
    api_contract: tuple[str, ...]


@dataclass(frozen=True)
class EverOSResult:
    status: str
    endpoint: str
    payload: dict[str, Any]
    response: dict[str, Any] | None = None
    error: str = ""


def source_path(settings: Settings) -> Path:
    return settings.vendor_dir / "everos"


def status(settings: Settings) -> EverOSStatus:
    src = source_path(settings)
    api_contract = (
        "POST /api/v1/memory/add",
        "POST /api/v1/memory/flush",
        "POST /api/v1/memory/search",
        "POST /api/v1/memory/get",
    )
    if not src.exists():
        state = "missing_source"
        detail = "EverOS source is not present under vendor/runtimes/everos"
    elif not (src / "LICENSE").exists():
        state = "invalid_source"
        detail = "EverOS source is present but LICENSE is missing"
    elif not (src / "src" / "everos").exists():
        state = "invalid_source"
        detail = "EverOS Python package source is missing"
    elif not settings.everos_base_url:
        state = "source_ready"
        detail = "EverOS source is present; set EVEROS_BASE_URL to enable live API calls"
    else:
        state = "configured"
        detail = "EverOS source and API base URL are configured"

    return EverOSStatus(
        status=state,
        detail=detail,
        source_path=str(src),
        license=EVEROS_LICENSE,
        base_url=settings.everos_base_url,
        memory_root=str(settings.everos_memory_root),
        api_contract=api_contract,
    )


def build_add_payload(
    *,
    user_id: str,
    session_id: str,
    text: str,
    app_id: str = "default",
    project_id: str = "default",
    role: str = "user",
    sender_name: str | None = None,
    timestamp_ms: int | None = None,
) -> dict[str, Any]:
    return {
        "session_id": session_id,
        "app_id": app_id,
        "project_id": project_id,
        "messages": [
            {
                "sender_id": user_id,
                "sender_name": sender_name,
                "role": role,
                "timestamp": timestamp_ms or int(time.time() * 1000),
                "content": text,
            }
        ],
    }


def build_flush_payload(*, session_id: str, app_id: str = "default", project_id: str = "default") -> dict[str, Any]:
    return {"session_id": session_id, "app_id": app_id, "project_id": project_id}


def build_search_payload(
    *,
    query: str,
    user_id: str = "",
    agent_id: str = "",
    app_id: str = "default",
    project_id: str = "default",
    top_k: int = 5,
    method: str = "hybrid",
    include_profile: bool = False,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "app_id": app_id,
        "project_id": project_id,
        "query": query,
        "method": method,
        "top_k": top_k,
        "include_profile": include_profile,
    }
    if agent_id:
        payload["agent_id"] = agent_id
    else:
        payload["user_id"] = user_id
    return payload


def post_memory(settings: Settings, endpoint: str, payload: dict[str, Any], *, audit_action: str) -> EverOSResult:
    if not settings.everos_base_url:
        return EverOSResult(status="missing_config", endpoint=endpoint, payload=payload, error="EVEROS_BASE_URL is not configured")

    url = settings.everos_base_url.rstrip("/") + endpoint
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=settings.everos_timeout_seconds) as response:
            raw = response.read().decode("utf-8")
            data = json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        error = exc.read().decode("utf-8", errors="replace")
        return EverOSResult(status="http_error", endpoint=endpoint, payload=payload, error=f"{exc.code}: {error}")
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return EverOSResult(status="error", endpoint=endpoint, payload=payload, error=str(exc))

    create_audit_event(
        settings.data_dir,
        audit_action,
        resource_type="everos",
        resource_ref=endpoint,
        risk_level="low",
        payload={"status": "completed"},
    )
    return EverOSResult(status="completed", endpoint=endpoint, payload=payload, response=data)


def add_memory(settings: Settings, payload: dict[str, Any]) -> EverOSResult:
    return post_memory(settings, f"{EVEROS_API_PREFIX}/add", payload, audit_action="everos.memory_add")


def flush_memory(settings: Settings, payload: dict[str, Any]) -> EverOSResult:
    return post_memory(settings, f"{EVEROS_API_PREFIX}/flush", payload, audit_action="everos.memory_flush")


def search_memory(settings: Settings, payload: dict[str, Any]) -> EverOSResult:
    return post_memory(settings, f"{EVEROS_API_PREFIX}/search", payload, audit_action="everos.memory_search")


def as_payload(value: EverOSStatus | EverOSResult) -> dict[str, Any]:
    return asdict(value)
