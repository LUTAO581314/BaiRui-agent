from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .config import Settings
from .storage import (
    create_audit_event,
    create_channel_approval_request,
    create_channel_approval_review,
    list_channel_approval_requests,
    list_channel_approval_reviews,
)
from .social_bridge import dispatch_channel_target, is_deliverable_target


SUPPORTED_MEDIA_KINDS = ("text", "image", "video", "file")
DEFAULT_TARGETS = (
    {
        "id": "owner_review",
        "label": "Owner Review",
        "channel_type": "personal_chat",
        "status": "approval_required",
        "supports": SUPPORTED_MEDIA_KINDS,
        "requires_owner_confirmation": True,
    },
)


@dataclass(frozen=True)
class ChannelStatus:
    status: str
    enabled: bool
    configured_target_count: int
    deliverable_target_count: int
    supported_media_kinds: tuple[str, ...]
    requires_owner_confirmation: bool
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    approval_queue_count: int
    configured_targets: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class ChannelTargetDiagnostic:
    id: str
    label: str
    channel_type: str
    status: str
    supports: tuple[str, ...]
    requires_owner_confirmation: bool
    enabled: bool
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class ChannelSendPlan:
    status: str
    target_id: str
    channel_type: str
    media_kind: str
    message_preview: str
    attachment_path: str
    requires_owner_confirmation: bool
    will_send: bool
    reason: str
    audit_event_id: str
    approval_request_id: str


@dataclass(frozen=True)
class ChannelApprovalReviewResult:
    status: str
    request_id: str
    decision: str
    reviewer_ref: str
    note: str
    will_send: bool
    reason: str
    review_id: str
    delivery_status: str = "not_sent"
    delivery_reason: str = ""
    external_message_id: str = ""
    delivery_evidence: dict[str, Any] | None = None


def wecom_trial_next_step(plan_status: str, review_status: str = "", will_send: bool = False) -> str:
    if will_send:
        return "Enterprise group bot trial message was dispatched; verify the group message and archive the receipt."
    if review_status:
        return "Approval was recorded but no external send happened; inspect delivery_status and delivery_reason."
    if plan_status == "approval_required":
        return "Approval request created. Rerun with approval enabled, or approve from Settings after owner review."
    if plan_status == "blocked":
        return "Configure the enterprise group Bot Key and keep channels enabled, then rerun the enterprise group bot trial."
    if plan_status == "not_found":
        return "Save WECOM_BOT_KEY so bairui can auto-create safe target wecom:webhook:."
    return "Resolve channel diagnostics, then rerun the enterprise group bot trial."


def run_wecom_trial(settings: Settings, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    text = str(payload.get("text", "bairui enterprise group bot channel trial")).strip() or "bairui enterprise group bot channel trial"
    approve = bool(payload.get("approve", False))
    reviewer_ref = str(payload.get("reviewer_ref", "owner")).strip() or "owner"
    note = str(payload.get("note", "wecom-trial")).strip() or "wecom-trial"

    status = channel_status(settings)
    diagnostics = tuple(diagnose_channel_targets(settings))
    plan = plan_channel_send(
        settings,
        {
            "target_id": "wecom:webhook:",
            "text": text,
            "media_kind": "text",
            "attachment_path": "",
        },
    )
    review = None
    if approve and plan.status == "approval_required" and plan.approval_request_id:
        review = review_channel_approval(
            settings,
            {
                "request_id": plan.approval_request_id,
                "decision": "approve",
                "reviewer_ref": reviewer_ref,
                "note": note,
            },
        )
    trial_status = "blocked"
    if plan.status == "approval_required" and not approve:
        trial_status = "ready_to_approve"
    elif review and review.status == "reviewed":
        trial_status = "reviewed"
    return {
        "status": trial_status,
        "safe_target_id": "wecom:webhook:",
        "requires_owner_approval_for_real_send": True,
        "approved_this_request": bool(approve),
        "channels": as_payload(status),
        "diagnostics": tuple(as_payload(item) for item in diagnostics),
        "plan": as_payload(plan),
        "review": as_payload(review) if review else None,
        "next_step": wecom_trial_next_step(
            plan.status,
            review.status if review else "",
            getattr(review, "will_send", False) if review else False,
        ),
    }


def channel_status(settings: Settings) -> ChannelStatus:
    targets = channel_targets(settings)
    enabled = _channels_enabled(settings)
    approvals = list_channel_approvals(settings, only_pending=True)
    deliverable_targets = [target for target in targets if is_deliverable_target(target)]
    blockers: list[str] = []
    warnings: list[str] = []
    if not enabled:
        blockers.append("channels_disabled")
    if not targets:
        blockers.append("missing_targets")
    if enabled and targets and not deliverable_targets:
        warnings.append("missing_deliverable_targets")
    if enabled and not approvals and targets:
        warnings.append("no_pending_approvals")
    if targets and not enabled:
        warnings.append("targets_configured_but_channels_disabled")
    status = "missing_config"
    if enabled and deliverable_targets:
        status = "ready"
    elif enabled and targets:
        status = "approval_only"
    return ChannelStatus(
        status=status,
        enabled=enabled,
        configured_target_count=len(targets),
        deliverable_target_count=len(deliverable_targets),
        supported_media_kinds=SUPPORTED_MEDIA_KINDS,
        requires_owner_confirmation=True,
        blockers=tuple(blockers),
        warnings=tuple(warnings),
        approval_queue_count=len(approvals),
        configured_targets=tuple(targets),
    )


def channel_targets(settings: Settings) -> tuple[dict[str, Any], ...]:
    configured = _load_configured_targets(settings)
    configured = _with_auto_targets(settings, configured)
    if configured:
        return tuple(configured)
    return DEFAULT_TARGETS


def diagnose_channel_targets(settings: Settings) -> tuple[ChannelTargetDiagnostic, ...]:
    enabled = _channels_enabled(settings)
    diagnostics: list[ChannelTargetDiagnostic] = []
    for target in channel_targets(settings):
        target_id = str(target.get("id", "")).strip()
        label = str(target.get("label", target_id)).strip() or target_id
        channel_type = str(target.get("channel_type", "")).strip()
        supports = tuple(str(value) for value in target.get("supports", ()) if str(value) in SUPPORTED_MEDIA_KINDS)
        requires_owner_confirmation = bool(target.get("requires_owner_confirmation", True))
        blockers: list[str] = []
        warnings: list[str] = []
        if not enabled:
            blockers.append("channels_disabled")
        if not target_id:
            blockers.append("missing_target_id")
        if not channel_type:
            blockers.append("missing_channel_type")
        if not supports:
            blockers.append("missing_supported_media")
        if is_deliverable_target(target):
            missing_credentials = _missing_credentials_for_target(channel_type, settings)
            blockers.extend(missing_credentials)
        else:
            warnings.append("approval_only_target")
        if not requires_owner_confirmation:
            warnings.append("owner_confirmation_disabled")
        target_status = "ready" if enabled and not blockers else "missing_config"
        if enabled and requires_owner_confirmation and not blockers:
            target_status = "approval_required"
        diagnostics.append(
            ChannelTargetDiagnostic(
                id=target_id,
                label=label,
                channel_type=channel_type,
                status=target_status,
                supports=supports,
                requires_owner_confirmation=requires_owner_confirmation,
                enabled=enabled,
                blockers=tuple(blockers),
                warnings=tuple(warnings),
            )
        )
    return tuple(diagnostics)


def plan_channel_send(settings: Settings, payload: dict[str, Any]) -> ChannelSendPlan:
    targets = {str(target.get("id", "")): target for target in channel_targets(settings)}
    target_id = str(payload.get("target_id", "")).strip()
    media_kind = str(payload.get("media_kind", "text")).strip() or "text"
    message = str(payload.get("text", "")).strip()
    attachment_path = str(payload.get("attachment_path", "")).strip()

    status = "approval_required"
    reason = "owner_confirmation_required"
    target = targets.get(target_id)
    if not _channels_enabled(settings):
        status = "blocked"
        reason = "channels_disabled"
    elif not target:
        status = "not_found"
        reason = "target_not_found"
    elif media_kind not in SUPPORTED_MEDIA_KINDS:
        status = "unsupported_media"
        reason = "unsupported_media_kind"
    elif media_kind == "text" and not message:
        status = "invalid_request"
        reason = "text_required"
    elif media_kind != "text" and not attachment_path:
        status = "invalid_request"
        reason = "attachment_path_required"
    elif media_kind != "text" and not Path(attachment_path).exists():
        status = "blocked"
        reason = "attachment_not_found"
    elif target and is_deliverable_target(target):
        missing_credentials = _missing_credentials_for_target(str(target.get("channel_type", "")), settings)
        if missing_credentials:
            status = "blocked"
            reason = ",".join(missing_credentials)

    approval_request_id = ""
    if status == "approval_required":
        approval = create_channel_approval_request(
            settings.data_dir,
            target_id=target_id,
            channel_type=str((target or {}).get("channel_type", "")),
            media_kind=media_kind,
            message_preview=message[:160],
            attachment_path=attachment_path,
            reason=reason,
        )
        approval_request_id = approval.id

    audit = create_audit_event(
        settings.data_dir,
        "channel.send_planned" if status == "approval_required" else "channel.send_blocked",
        resource_type="channel_target",
        resource_ref=target_id or "missing_target",
        risk_level="high",
        payload={
            "status": status,
            "target_id": target_id,
            "channel_type": str((target or {}).get("channel_type", "")),
            "media_kind": media_kind,
            "reason": reason,
            "will_send": False,
            "approval_request_id": approval_request_id,
        },
    )
    return ChannelSendPlan(
        status=status,
        target_id=target_id,
        channel_type=str((target or {}).get("channel_type", "")),
        media_kind=media_kind,
        message_preview=message[:160],
        attachment_path=attachment_path,
        requires_owner_confirmation=True,
        will_send=False,
        reason=reason,
        audit_event_id=audit.id,
        approval_request_id=approval_request_id,
    )


def list_channel_approvals(settings: Settings, *, only_pending: bool = False) -> tuple[dict[str, Any], ...]:
    requests = list_channel_approval_requests(settings.data_dir, limit=200)
    reviews = list_channel_approval_reviews(settings.data_dir, limit=200)
    reviewed_ids = {str(review.get("request_id", "")) for review in reviews}
    rows: list[dict[str, Any]] = []
    for request in requests:
        request_id = str(request.get("id", ""))
        current = dict(request)
        current["review_status"] = "reviewed" if request_id in reviewed_ids else "pending_review"
        if only_pending and current["review_status"] != "pending_review":
            continue
        rows.append(current)
    return tuple(rows)


def list_channel_delivery_receipts(settings: Settings, *, limit: int = 50) -> tuple[dict[str, Any], ...]:
    receipts_dir = settings.data_dir / "channel_receipts"
    if not receipts_dir.exists():
        return ()
    rows: list[dict[str, Any]] = []
    for path in sorted(receipts_dir.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        if len(rows) >= limit:
            break
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        rows.append(
            {
                "service": "bairui",
                "receipt_type": str(payload.get("receipt_type", "channel_delivery")),
                "request_id": str(payload.get("request_id", "")),
                "review_id": str(payload.get("review_id", "")),
                "target_id": _safe_target_ref(str(payload.get("target_id", ""))),
                "channel_type": str(payload.get("channel_type", "")),
                "media_kind": str(payload.get("media_kind", "")),
                "message_preview": str(payload.get("message_preview", ""))[:160],
                "will_send": bool(payload.get("will_send", False)),
                "delivery_status": str(payload.get("delivery_status", "")),
                "delivery_reason": str(payload.get("delivery_reason", "")),
                "external_message_id": str(payload.get("external_message_id", "")),
                "created_at": str(payload.get("created_at", "")),
                "receipt_path": str(path),
                "secret_echo": False,
            }
        )
    return tuple(rows)


def review_channel_approval(settings: Settings, payload: dict[str, Any]) -> ChannelApprovalReviewResult:
    request_id = str(payload.get("request_id", "")).strip()
    decision = str(payload.get("decision", "")).strip()
    reviewer_ref = str(payload.get("reviewer_ref", "owner")).strip() or "owner"
    note = str(payload.get("note", "")).strip()

    if decision not in {"approve", "reject"}:
        return ChannelApprovalReviewResult(
            status="invalid_decision",
            request_id=request_id,
            decision=decision,
            reviewer_ref=reviewer_ref,
            note=note,
            will_send=False,
            reason="decision_must_be_approve_or_reject",
            review_id="",
        )

    requests = {str(item.get("id", "")): item for item in list_channel_approval_requests(settings.data_dir, limit=200)}
    if request_id not in requests:
        return ChannelApprovalReviewResult(
            status="not_found",
            request_id=request_id,
            decision=decision,
            reviewer_ref=reviewer_ref,
            note=note,
            will_send=False,
            reason="approval_request_not_found",
            review_id="",
        )

    reviews = list_channel_approval_reviews(settings.data_dir, limit=200)
    if any(str(review.get("request_id", "")) == request_id for review in reviews):
        return ChannelApprovalReviewResult(
            status="already_reviewed",
            request_id=request_id,
            decision=decision,
            reviewer_ref=reviewer_ref,
            note=note,
            will_send=False,
            reason="approval_request_already_reviewed",
            review_id="",
        )

    request = requests[request_id]
    targets = {str(target.get("id", "")): target for target in channel_targets(settings)}
    target = targets.get(str(request.get("target_id", "")).strip(), {})
    will_send = False
    reason = "review_recorded_without_external_dispatch"
    delivery_status = "not_sent"
    delivery_reason = ""
    external_message_id = ""
    delivery_evidence: dict[str, Any] = {}

    if decision == "approve" and target and is_deliverable_target(target):
        dispatch = dispatch_channel_target(
            settings,
            target,
            {
                "text": str(request.get("message_preview", "")).strip(),
                "media_kind": str(request.get("media_kind", "text")).strip() or "text",
                "attachment_path": str(request.get("attachment_path", "")).strip(),
            },
        )
        delivery_status = dispatch.delivery_status
        delivery_reason = dispatch.delivery_reason
        external_message_id = dispatch.external_message_id
        delivery_evidence = _delivery_evidence_from_dispatch(dispatch)
        will_send = dispatch.will_send
        reason = dispatch.status if dispatch.status != "dispatched" else "approved_and_dispatched"
        if will_send:
            delivery_evidence["receipt_path"] = str(_channel_receipt_path(settings, request_id))
        if will_send:
            create_audit_event(
                settings.data_dir,
                "channel.external_send_recorded",
                resource_type="channel_approval_request",
                resource_ref=request_id,
                risk_level="high",
                payload={
                    "target_id": str(request.get("target_id", "")),
                    "channel_type": str(request.get("channel_type", "")),
                    "delivery_status": delivery_status,
                    "external_message_id": external_message_id,
                    "delivery_evidence": delivery_evidence,
                },
            )

    review = create_channel_approval_review(
        settings.data_dir,
        request_id=request_id,
        decision=decision,
        reviewer_ref=reviewer_ref,
        note=note,
        will_send=will_send,
        delivery_status=delivery_status,
        delivery_reason=delivery_reason,
        external_message_id=external_message_id,
        delivery_evidence=delivery_evidence,
    )
    if will_send:
        _archive_channel_receipt(settings, request, review, delivery_evidence)
    return ChannelApprovalReviewResult(
        status="reviewed",
        request_id=request_id,
        decision=decision,
        reviewer_ref=reviewer_ref,
        note=note,
        will_send=will_send,
        reason=reason,
        review_id=review.id,
        delivery_status=delivery_status,
        delivery_reason=delivery_reason,
        external_message_id=external_message_id,
        delivery_evidence=delivery_evidence,
    )


def _channel_receipt_path(settings: Settings, request_id: str) -> Path:
    safe_id = "".join(ch for ch in request_id if ch.isalnum() or ch in {"-", "_"}) or "receipt"
    return settings.data_dir / "channel_receipts" / f"{safe_id}.json"


def _archive_channel_receipt(
    settings: Settings,
    request: dict[str, Any],
    review: Any,
    delivery_evidence: dict[str, Any],
) -> Path:
    path = _channel_receipt_path(settings, str(request.get("id", "")))
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "service": "bairui",
        "receipt_type": "channel_delivery",
        "secret_echo": False,
        "request_id": str(request.get("id", "")),
        "review_id": str(getattr(review, "id", "")),
        "target_id": _safe_target_ref(str(request.get("target_id", ""))),
        "channel_type": str(request.get("channel_type", "")),
        "media_kind": str(request.get("media_kind", "")),
        "message_preview": str(request.get("message_preview", "")),
        "decision": str(getattr(review, "decision", "")),
        "reviewer_ref": str(getattr(review, "reviewer_ref", "")),
        "will_send": bool(getattr(review, "will_send", False)),
        "delivery_status": str(getattr(review, "delivery_status", "")),
        "delivery_reason": str(getattr(review, "delivery_reason", "")),
        "external_message_id": str(getattr(review, "external_message_id", "")),
        "delivery_evidence": {
            "platform": str(delivery_evidence.get("platform", "")),
            "status": str(delivery_evidence.get("status", "")),
            "delivery_status": str(delivery_evidence.get("delivery_status", "")),
            "external_message_id": str(delivery_evidence.get("external_message_id", "")),
            "raw_ok": bool(delivery_evidence.get("raw_ok", False)),
            "raw_keys": list(delivery_evidence.get("raw_keys", ()))[:20],
            "secret_echo": False,
        },
        "created_at": str(getattr(review, "created_at", "")),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _safe_target_ref(target_id: str) -> str:
    if target_id.startswith("wecom:webhook:"):
        return "wecom:webhook:"
    if target_id.startswith("discord:"):
        return "discord:"
    if target_id.startswith("feishu:"):
        return "feishu:"
    if target_id.startswith("wechat:"):
        return "wechat:"
    if target_id.startswith("qq:"):
        return "qq:"
    return target_id[:80]


def _delivery_evidence_from_dispatch(dispatch: SocialDispatchResult) -> dict[str, Any]:
    raw = dispatch.raw if isinstance(dispatch.raw, dict) else {}
    raw_keys = sorted(str(key) for key in raw.keys())[:20]
    return {
        "platform": dispatch.platform,
        "status": dispatch.status,
        "delivery_status": dispatch.delivery_status,
        "external_message_id": dispatch.external_message_id,
        "raw_ok": bool(raw.get("ok", False)) if raw else dispatch.delivery_status == "sent",
        "raw_keys": raw_keys,
        "secret_echo": False,
    }


def as_payload(value: Any) -> dict[str, Any]:
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    if isinstance(value, dict):
        return value
    return dict(value)


def _channels_enabled(settings: Settings) -> bool:
    value = _local_config_value(settings, "BAIRUI_CHANNELS_ENABLED")
    if not value.strip():
        value = os.getenv("BAIRUI_CHANNELS_ENABLED", "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _load_configured_targets(settings: Settings | None = None) -> list[dict[str, Any]]:
    raw = ""
    if settings is not None:
        raw = _local_config_value(settings, "BAIRUI_CHANNEL_TARGETS_JSON").strip()
    if not raw:
        raw = os.getenv("BAIRUI_CHANNEL_TARGETS_JSON", "").strip()
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    targets: list[dict[str, Any]] = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        target_id = str(item.get("id", "")).strip()
        if not target_id:
            continue
        supports = item.get("supports", SUPPORTED_MEDIA_KINDS)
        if not isinstance(supports, list):
            supports = list(SUPPORTED_MEDIA_KINDS)
        targets.append(
            {
                "id": target_id,
                "label": str(item.get("label", target_id)).strip() or target_id,
                "channel_type": str(item.get("channel_type", "team_webhook")).strip() or "team_webhook",
                "status": str(item.get("status", "approval_required")).strip() or "approval_required",
                "supports": tuple(str(value) for value in supports if str(value) in SUPPORTED_MEDIA_KINDS),
                "requires_owner_confirmation": bool(item.get("requires_owner_confirmation", True)),
            }
        )
    return targets


def _with_auto_targets(settings: Settings, targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Expose safe default targets for configured connectors without leaking secrets."""

    result = list(targets)
    channel_types = {str(item.get("channel_type", "")).strip().lower() for item in result}
    target_ids = {str(item.get("id", "")).strip() for item in result}
    if settings.wecom_bot_key.strip() and "wecom-webhook" not in channel_types and "wecom:webhook:" not in target_ids:
        result.append(
            {
                "id": "wecom:webhook:",
                "label": "Enterprise Group Bot",
                "channel_type": "wecom-webhook",
                "status": "approval_required",
                "supports": ("text",),
                "requires_owner_confirmation": True,
                "auto_generated": True,
            }
        )
    return result


def _local_config_value(settings: Settings, key: str) -> str:
    try:
        from .config import local_config_path

        path = local_config_path(settings.data_dir)
        if not path.exists():
            return ""
        payload = json.loads(path.read_text(encoding="utf-8"))
        values = payload.get("values", {}) if isinstance(payload, dict) else {}
        value = values.get(key, "") if isinstance(values, dict) else ""
        return str(value or "")
    except (OSError, json.JSONDecodeError):
        return ""


def _missing_credentials_for_target(channel_type: str, settings: Settings) -> list[str]:
    channel_type = channel_type.strip().lower()
    if channel_type == "discord" and not settings.discord_bot_token.strip():
        return ["missing_discord_bot_token"]
    if channel_type == "feishu":
        missing = []
        if not settings.feishu_app_id.strip():
            missing.append("missing_feishu_app_id")
        if not settings.feishu_app_secret.strip():
            missing.append("missing_feishu_app_secret")
        if not settings.feishu_verification_token.strip():
            missing.append("missing_feishu_verification_token")
        return missing
    if channel_type == "wechat-official":
        missing = []
        if not settings.wechat_official_app_id.strip():
            missing.append("missing_wechat_official_app_id")
        if not settings.wechat_official_app_secret.strip():
            missing.append("missing_wechat_official_app_secret")
        if not settings.wechat_official_token.strip():
            missing.append("missing_wechat_official_token")
        return missing
    if channel_type == "wecom-webhook" and not settings.wecom_bot_key.strip():
        return ["missing_wecom_bot_key"]
    if channel_type == "qq-napcat":
        missing = []
        if not settings.qq_napcat_base_url.strip():
            missing.append("missing_qq_napcat_base_url")
        return missing
    return []
