from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .config import Settings
from .storage import (
    create_audit_event,
    create_channel_approval_request,
    create_document_memory_candidate,
    create_job,
    create_report_record,
    list_audit_events,
)


DEMO_MARKER = "bairui-demo-seed"


def seed_demo_data(settings: Settings, *, force: bool = False) -> dict[str, Any]:
    existing = [
        event
        for event in list_audit_events(settings.data_dir, limit=500)
        if event.get("action") == DEMO_MARKER
    ]
    if existing and not force:
        return {"status": "skipped", "reason": "demo_data_already_seeded", "marker_event_id": existing[-1].get("id", "")}

    job = create_job(
        settings.data_dir,
        title="Demo research task",
        prompt="Summarize a customer onboarding request, identify knowledge gaps, and propose owner-reviewed next actions.",
        route="research",
    )
    report = create_report_record(
        settings.data_dir,
        title="Demo onboarding report",
        body=(
            "This draft report demonstrates the bairui flow from an agent message into a reviewable deliverable.\n\n"
            "- Keep external sends owner-reviewed.\n"
            "- Review memory candidates before long-term promotion.\n"
            "- Use CodeGraph separately for source structure."
        ),
        source_type="demo",
        source_ref=job.id,
        status="draft",
    )
    candidate = create_document_memory_candidate(
        settings.data_dir,
        ingest_id="demo-ingest",
        artifact_id="demo-artifact",
        source_path="demo://onboarding-notes",
        candidate_type="customer_preference",
        text="Demo customer prefers concise weekly progress reports and owner-approved outbound messages.",
        confidence=0.72,
        reason="demo_memory_candidate_requires_owner_review",
    )
    approval = create_channel_approval_request(
        settings.data_dir,
        target_id="owner_review",
        channel_type="personal_chat",
        media_kind="text",
        message_preview="Demo outbound draft: confirm onboarding scope after owner approval.",
        reason="demo_channel_draft_requires_owner_review",
    )
    marker = create_audit_event(
        settings.data_dir,
        DEMO_MARKER,
        resource_type="demo_seed",
        resource_ref=job.id,
        payload={
            "job_id": job.id,
            "report_id": report.id,
            "memory_candidate_id": candidate.id,
            "channel_approval_id": approval.id,
            "will_send": False,
            "will_write_long_term_memory": False,
        },
    )
    return {
        "status": "completed",
        "job": asdict(job),
        "report": asdict(report),
        "memory_candidate": asdict(candidate),
        "channel_approval": asdict(approval),
        "audit_marker": asdict(marker),
    }
