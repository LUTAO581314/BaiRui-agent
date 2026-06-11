from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .storage import list_audit_events


ACTION_EVENT_TYPES = {
    "job.created": "job.created",
    "document.ingest_planned": "document.step.planned",
    "document.ingest_run_finished": "document.step.completed",
    "document.artifacts_registered": "document.step.completed",
    "document.index_finished": "document.step.completed",
    "document.memory_candidates_generated": "memory.review.required",
    "document.memory_candidate_reviewed": "memory.review.completed",
    "document.memory_candidates_batch_reviewed": "memory.review.completed",
    "document.source_refs_created": "document.step.completed",
    "document.ingest_report_created": "report.created",
    "obsidian.report_written": "report.created",
    "chat.completed": "command.completed",
    "chat.not_completed": "command.blocked",
    "channel.send_planned": "channel.send.approval_required",
    "channel.send_blocked": "channel.send.blocked",
    "channel.approval_requested": "channel.approval.requested",
    "channel.approval_reviewed": "channel.approval.reviewed",
    "database.migration": "system.changed",
}


def audit_event_to_frontend_event(event: dict[str, Any]) -> dict[str, Any]:
    action = str(event.get("action", "audit.event"))
    payload = event.get("payload")
    if not isinstance(payload, dict):
        payload = {}
    return {
        "type": ACTION_EVENT_TYPES.get(action, "audit.event"),
        "ts": str(event.get("created_at", "")),
        "data": {
            "id": str(event.get("id", "")),
            "action": action,
            "resource_type": str(event.get("resource_type", "")),
            "resource_ref": str(event.get("resource_ref", "")),
            "risk_level": str(event.get("risk_level", "")),
            "payload": payload,
        },
    }


def list_frontend_events(data_dir: Path, limit: int = 50) -> list[dict[str, Any]]:
    return [audit_event_to_frontend_event(event) for event in list_audit_events(data_dir, limit=limit)]


def build_sse_frame(event: dict[str, Any]) -> bytes:
    event_type = str(event.get("type", "message"))
    body = json.dumps(event, ensure_ascii=False, sort_keys=True)
    return f"event: {event_type}\ndata: {body}\n\n".encode("utf-8")
