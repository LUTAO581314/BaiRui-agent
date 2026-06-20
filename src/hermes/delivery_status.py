from __future__ import annotations

from typing import Any

from .backup import backup_status
from .channels import channel_status, list_channel_delivery_receipts
from .config import Settings
from .config_status import build_config_status
from .db import database_status
from .document_pipeline import list_document_ingest_session_summaries
from .runtime_readiness import collect_runtime_readiness


def build_delivery_status(settings: Settings) -> dict[str, Any]:
    """Return a secret-safe commercial trial readiness summary."""

    config = build_config_status(settings)
    commercial = config.get("commercial_trial", {})
    runtime = collect_runtime_readiness(settings)
    channels = channel_status(settings)
    channel_receipts = list_channel_delivery_receipts(settings, limit=5)
    sent_channel_receipts = tuple(
        item for item in channel_receipts
        if bool(item.get("will_send")) and str(item.get("delivery_status", "")).lower() == "sent" and str(item.get("external_message_id", "")).strip()
    )
    backup = backup_status(settings)
    database = database_status(settings)
    document_session_list = list_document_ingest_session_summaries(settings, limit=5)
    document_sessions = tuple(getattr(document_session_list, "sessions", ()) or ())
    document_ready = any(str(_field(item, "current_stage") or "") == "done" for item in document_sessions)

    checks = [
        _check(
            "commercial_trial",
            commercial.get("status") == "ready",
            "Commercial trial gate",
            "Owner token, model gateway, and one deliverable channel must be ready.",
            commercial.get("blockers", ()),
        ),
        _check(
            "runtime_readiness",
            runtime.get("status") in {"ready", "partial"},
            "Runtime readiness",
            "Required runtime blockers must be absent.",
            runtime.get("blockers", ()),
        ),
        _check(
            "channel_delivery",
            channels.enabled and channels.deliverable_target_count > 0,
            "Channel delivery",
            "Configure at least one approval-controlled real outbound channel.",
            tuple(channels.blockers) + tuple(channels.warnings),
        ),
        _check(
            "channel_receipt",
            bool(sent_channel_receipts),
            "Channel receipt",
            "Run one owner-approved Enterprise WeCom send and archive the secret-safe receipt.",
            ("missing_enterprise_group_receipt",) if not sent_channel_receipts else (),
        ),
        _check(
            "document_memory_loop",
            document_ready,
            "Document memory loop",
            "Run at least one document ingestion through review, report, and source references.",
            ("no_completed_document_ingest_session",) if not document_ready else (),
        ),
        _check(
            "database",
            database.status == "ready",
            "Database",
            "PostgreSQL should be reachable for server trials.",
            (database.detail,) if database.status != "ready" else (),
        ),
        _check(
            "backup",
            backup.status == "ready",
            "Backup",
            "Backup plan should be ready before customer-facing use.",
            (backup.detail,) if backup.status != "ready" else (),
        ),
    ]
    blockers = [check["id"] for check in checks if check["status"] == "blocked"]
    status = "ready" if not blockers else "blocked"
    blocker_reasons = _blocker_reasons(checks)
    return {
        "status": status,
        "service": "bairui",
        "secret_echo": False,
        "blockers": blockers,
        "blocker_reasons": blocker_reasons,
        "checks": checks,
        "next_step": _next_step(blockers, blocker_reasons),
        "actions": _actions_for_blockers(blockers, blocker_reasons),
        "evidence": {
            "config_status": config.get("status"),
            "commercial_trial": commercial.get("status"),
            "runtime_readiness": runtime.get("status"),
            "channel_status": channels.status,
            "channel_blockers": tuple(channels.blockers),
            "channel_warnings": tuple(channels.warnings),
            "deliverable_target_count": channels.deliverable_target_count,
            "channel_receipt_count": len(channel_receipts),
            "sent_channel_receipt_count": len(sent_channel_receipts),
            "latest_channel_receipt": sent_channel_receipts[0] if sent_channel_receipts else {},
            "document_session_count": len(document_sessions),
            "completed_document_session_count": sum(1 for item in document_sessions if str(_field(item, "current_stage") or "") == "done"),
            "database": database.status,
            "backup": backup.status,
        },
    }


def _check(id: str, passed: bool, label: str, detail: str, blockers: Any = ()) -> dict[str, Any]:
    blocker_list = [str(item) for item in (blockers or ()) if str(item)]
    return {
        "id": id,
        "label": label,
        "status": "ready" if passed else "blocked",
        "detail": detail,
        "blockers": () if passed else tuple(blocker_list),
    }


def _field(item: Any, name: str) -> Any:
    if isinstance(item, dict):
        return item.get(name)
    return getattr(item, name, None)


def _blocker_reasons(checks: list[dict[str, Any]]) -> tuple[str, ...]:
    reasons: list[str] = []
    for check in checks:
        if check.get("status") != "blocked":
            continue
        for blocker in check.get("blockers", ()):
            text = str(blocker).strip()
            if text and text not in reasons:
                reasons.append(text)
    return tuple(reasons)


def _actions_for_blockers(blockers: list[str], blocker_reasons: tuple[str, ...] = ()) -> tuple[dict[str, Any], ...]:
    actions: list[dict[str, Any]] = []

    def add(
        id: str,
        label: str,
        detail: str,
        *,
        fields: tuple[str, ...] = (),
        endpoint: str = "",
        command: str = "",
        owner_required: bool = False,
    ) -> None:
        if any(item["id"] == id for item in actions):
            return
        actions.append(
            {
                "id": id,
                "label": label,
                "detail": detail,
                "fields": fields,
                "endpoint": endpoint,
                "command": command,
                "owner_required": owner_required,
            }
        )

    if "model_gateway" in blocker_reasons:
        add(
            "configure_model_gateway",
            "Configure model gateway",
            "Save the OpenAI-compatible Base URL, API key, and preferred model, then run a real chat probe.",
            fields=("model_base_url", "model_api_key", "model_name"),
            endpoint="/config/apply",
            command="python -m src.hermes model-gateway probe --model <model-name>",
        )
    if "owner_gate" in blocker_reasons:
        add(
            "configure_owner_gate",
            "Configure owner token",
            "Set the owner token before exposing write APIs on a server or public domain.",
            fields=("owner_token",),
            endpoint="/config/apply",
            command="python -m src.hermes config-status",
            owner_required=True,
        )
    if (
        "deliverable_channel" in blocker_reasons
        or "missing_deliverable_targets" in blocker_reasons
        or "channel_delivery" in blockers
        or "missing_enterprise_group_receipt" in blocker_reasons
        or "channel_receipt" in blockers
    ):
        add(
            "configure_wecom_trial_channel",
            "Configure enterprise group channel",
            "Save the enterprise group Bot Key if needed, then run and approve one Enterprise WeCom send so bairui can archive a receipt.",
            fields=("wecom_bot_key", "channel_enabled"),
            endpoint="/channels/wecom-trial",
            command='python -m src.hermes channels wecom-trial --text "bairui channel trial" --approve',
            owner_required=True,
        )
    if "document_memory_loop" in blockers:
        add(
            "run_document_memory_trial",
            "Run document memory trial",
            "Upload or parse one document, approve at least one memory candidate, then verify graph/report/source references.",
            fields=("document_output_dir", "memory_vault_dir"),
            command="python -m src.hermes document parse memory-trial",
            owner_required=True,
        )
    if "database" in blockers or any("HERMES_DATABASE_URL" in reason for reason in blocker_reasons):
        add(
            "configure_postgresql",
            "Configure PostgreSQL",
            "Set HERMES_DATABASE_URL on the target server and run migration verification before a customer-facing trial.",
            fields=("database_url",),
            endpoint="/config/apply",
            command=".\\scripts\\verify-postgres-production.ps1 -RequireDatabase -RunMigration",
            owner_required=True,
        )
    if "backup" in blockers or any("backup" in reason.lower() for reason in blocker_reasons):
        add(
            "verify_backup",
            "Verify backup",
            "Create and verify a PostgreSQL backup artifact, then keep the restore command guarded by confirmation.",
            fields=("database_url",),
            endpoint="/backup/plan",
            command="python -m src.hermes backup plan",
            owner_required=True,
        )
    if "server_verification" in blockers:
        add(
            "verify_server",
            "Verify target server",
            "Run the server deployment verifier against the real bairui domain and archive the evidence.",
            command=".\\scripts\\verify-server-deployment.ps1 -BaseUrl <https://your-bairui-domain>",
        )
    if not actions and blockers:
        add(
            "refresh_delivery_status",
            "Refresh delivery status",
            "Refresh /delivery/status and rerun the commercial smoke test after resolving blocked checks.",
            endpoint="/delivery/status",
            command="python -m src.hermes delivery-status",
        )
    return tuple(actions)


def _next_step(blockers: list[str], blocker_reasons: tuple[str, ...] = ()) -> str:
    if not blockers:
        return "Commercial trial gate is ready; proceed with final smoke test and customer handoff."
    if "model_gateway" in blocker_reasons:
        return "Configure the model gateway, run model-gateway probe, then refresh /delivery/status."
    if "owner_gate" in blocker_reasons:
        return "Set BAIRUI_OWNER_TOKEN before exposing the console, then refresh /delivery/status."
    if "deliverable_channel" in blocker_reasons or "missing_deliverable_targets" in blocker_reasons or "channel_delivery" in blockers:
        return "Save the enterprise group Bot Key so bairui can auto-create safe target wecom:webhook:, then run channels wecom-trial --approve and archive the receipt."
    if "missing_enterprise_group_receipt" in blocker_reasons or "channel_receipt" in blockers:
        return "Run and approve one Enterprise WeCom group message, then verify channels receipts and archive artifacts/wecom-receipt.json."
    if "commercial_trial" in blockers or "channel_delivery" in blockers:
        return "Set BAIRUI_OWNER_TOKEN and the enterprise group Bot Key, then send and approve one enterprise group test message."
    if "document_memory_loop" in blockers:
        return "Upload one document, run ingestion until review, approve a memory candidate, and generate report/source references."
    if "database" in blockers:
        return "Configure HERMES_DATABASE_URL on the target server, run migration verification, then rerun /delivery/status."
    if "backup" in blockers:
        return "Create and verify a PostgreSQL backup artifact before customer-facing use."
    return "Resolve blocked checks, refresh /delivery/status, and rerun the commercial smoke test."
