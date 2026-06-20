from __future__ import annotations

import json
import os
import subprocess
import threading
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .adapters.funasr import build_docker_command as build_funasr_docker_command
from .adapters.mineru import build_install_command as build_mineru_install_command
from .adapters.searxng import build_docker_command as build_searxng_docker_command
from .adapters.sonic import build_docker_command as build_sonic_docker_command
from .avatar import avatar_engine_status
from .config import Settings
from .storage import create_audit_event, utc_now


ALLOWED_RUNTIME_IDS = {
    "mineru_document_parse",
    "searxng_metasearch",
    "sonic_local_index",
    "funasr_voice_asr",
    "bairui_avatar_runtime",
}


@dataclass(frozen=True)
class RuntimeInstallPlan:
    runtime_id: str
    label: str
    command: tuple[str, ...]
    cwd: str
    detail: str
    requires_confirmation: bool


def installation_state_path(settings: Settings) -> Path:
    return settings.data_dir / "runtime-installations.jsonl"


def list_runtime_installations(settings: Settings) -> tuple[dict[str, Any], ...]:
    path = installation_state_path(settings)
    if not path.exists():
        return ()
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return tuple(rows[-50:])


def build_runtime_install_plan(settings: Settings, runtime_id: str) -> RuntimeInstallPlan:
    runtime_id = runtime_id.strip()
    if runtime_id == "mineru_document_parse":
        plan = build_mineru_install_command(settings)
        return RuntimeInstallPlan(runtime_id, "文档解析", tuple(plan.command), plan.cwd, plan.detail, True)
    if runtime_id == "searxng_metasearch":
        plan = build_searxng_docker_command(settings)
        return RuntimeInstallPlan(runtime_id, "联网搜索", tuple(plan.command), str(Path.cwd()), plan.detail, True)
    if runtime_id == "sonic_local_index":
        plan = build_sonic_docker_command(settings)
        return RuntimeInstallPlan(runtime_id, "本地索引", tuple(plan.command), str(Path.cwd()), plan.detail, True)
    if runtime_id == "funasr_voice_asr":
        plan = build_funasr_docker_command(settings)
        return RuntimeInstallPlan(runtime_id, "语音识别", tuple(plan.command), plan.cwd, plan.detail, True)
    if runtime_id == "bairui_avatar_runtime":
        avatar = avatar_engine_status(settings)
        package = f"{avatar.package}@{avatar.version}"
        return RuntimeInstallPlan(runtime_id, "Avatar", ("npm", "install", package), str(Path.cwd()), avatar.install_hint, True)
    raise ValueError(f"unsupported runtime_id: {runtime_id}")


def start_runtime_installation(settings: Settings, runtime_id: str, *, confirmation: str = "") -> dict[str, Any]:
    runtime_id = str(runtime_id or "").strip()
    if runtime_id not in ALLOWED_RUNTIME_IDS:
        return {"status": "invalid_runtime", "message": "runtime_id is not in the bairui install allowlist"}
    plan = build_runtime_install_plan(settings, runtime_id)
    if plan.requires_confirmation and confirmation != "INSTALL BAIRUI RUNTIME":
        return {
            "status": "confirmation_required",
            "confirmation_phrase": "INSTALL BAIRUI RUNTIME",
            "runtime_install_plan": asdict(plan),
        }
    job = {
        "id": uuid.uuid4().hex[:16],
        "runtime_id": runtime_id,
        "label": plan.label,
        "status": "queued",
        "progress_percent": 5,
        "command": list(plan.command),
        "cwd": plan.cwd,
        "detail": plan.detail,
        "started_at": utc_now(),
        "updated_at": utc_now(),
        "finished_at": "",
        "exit_code": None,
        "stdout_tail": "",
        "stderr_tail": "",
    }
    _append_installation(settings, job)
    create_audit_event(
        settings.data_dir,
        "runtime.installation_started",
        actor_type="owner",
        actor_ref="local_console",
        resource_type="runtime",
        resource_ref=runtime_id,
        risk_level="high",
        payload={"job_id": job["id"], "command": list(plan.command), "cwd": plan.cwd},
    )
    thread = threading.Thread(target=_run_installation, args=(settings, job, plan), daemon=True)
    thread.start()
    return {"status": "started", "runtime_installation": job, "runtime_install_plan": asdict(plan)}


def _run_installation(settings: Settings, job: dict[str, Any], plan: RuntimeInstallPlan) -> None:
    _append_installation(settings, {**job, "status": "running", "progress_percent": 20, "updated_at": utc_now()})
    try:
        cwd = Path(plan.cwd).expanduser()
        cwd.mkdir(parents=True, exist_ok=True)
        completed = subprocess.run(
            list(plan.command),
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=900,
            env={**os.environ, "PYTHONUTF8": "1"},
        )
        status = "completed" if completed.returncode == 0 else "failed"
        _append_installation(
            settings,
            {
                **job,
                "status": status,
                "progress_percent": 100,
                "updated_at": utc_now(),
                "finished_at": utc_now(),
                "exit_code": completed.returncode,
                "stdout_tail": _tail(completed.stdout.decode("utf-8", errors="replace")),
                "stderr_tail": _tail(completed.stderr.decode("utf-8", errors="replace")),
            },
        )
    except Exception as exc:  # pragma: no cover - defensive background guard
        _append_installation(
            settings,
            {
                **job,
                "status": "failed",
                "progress_percent": 100,
                "updated_at": utc_now(),
                "finished_at": utc_now(),
                "exit_code": None,
                "stderr_tail": str(exc),
            },
        )


def _append_installation(settings: Settings, payload: dict[str, Any]) -> None:
    path = installation_state_path(settings)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def _tail(text: str, limit: int = 2000) -> str:
    text = str(text or "").strip()
    return text[-limit:]
