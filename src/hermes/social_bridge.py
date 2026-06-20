from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import Settings


DELIVERABLE_CHANNEL_TYPES = {"discord", "feishu", "wechat-official", "wecom-webhook", "wechat-clawbot", "qq-napcat"}


@dataclass(frozen=True)
class SocialDispatchResult:
    status: str
    will_send: bool
    delivery_status: str
    delivery_reason: str
    external_message_id: str
    platform: str
    raw: dict[str, Any]


def is_deliverable_target(target: dict[str, Any]) -> bool:
    channel_type = str(target.get("channel_type", "")).strip().lower()
    return channel_type in DELIVERABLE_CHANNEL_TYPES


def dispatch_channel_target(settings: Settings, target: dict[str, Any], payload: dict[str, Any]) -> SocialDispatchResult:
    target_id = str(target.get("id", "")).strip()
    channel_type = str(target.get("channel_type", "")).strip().lower()
    if not target_id:
        return SocialDispatchResult(
            status="invalid_target",
            will_send=False,
            delivery_status="failed",
            delivery_reason="missing_target_id",
            external_message_id="",
            platform=channel_type,
            raw={},
        )
    if not is_deliverable_target(target):
        return SocialDispatchResult(
            status="not_deliverable",
            will_send=False,
            delivery_status="not_sent",
            delivery_reason="target_not_bound_to_social_connector",
            external_message_id="",
            platform=channel_type,
            raw={},
        )

    bridge = settings.vendor_dir.parent / "bairui-social" / "bridge.mjs"
    if not bridge.exists():
        return SocialDispatchResult(
            status="bridge_missing",
            will_send=False,
            delivery_status="failed",
            delivery_reason="social_bridge_missing",
            external_message_id="",
            platform=channel_type,
            raw={},
        )

    request_payload = {
        "action": "dispatch",
        "targetId": target_id,
        "payload": {
            "text": str(payload.get("text", "")).strip(),
            "mediaPath": str(payload.get("attachment_path", "")).strip(),
            "mediaKind": str(payload.get("media_kind", "text")).strip() or "text",
        },
    }
    env = _bridge_env(settings)
    try:
        completed = subprocess.run(
            ["node", str(bridge)],
            input=json.dumps(request_payload, ensure_ascii=False).encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(bridge.parent),
            env=env,
            check=False,
            timeout=max(10, settings.model_timeout_seconds),
        )
    except FileNotFoundError:
        return SocialDispatchResult(
            status="node_missing",
            will_send=False,
            delivery_status="failed",
            delivery_reason="node_runtime_not_installed",
            external_message_id="",
            platform=channel_type,
            raw={},
        )
    except subprocess.TimeoutExpired:
        return SocialDispatchResult(
            status="dispatch_timeout",
            will_send=False,
            delivery_status="failed",
            delivery_reason="social_dispatch_timeout",
            external_message_id="",
            platform=channel_type,
            raw={},
        )

    stdout = completed.stdout.decode("utf-8", errors="replace").strip()
    stderr = completed.stderr.decode("utf-8", errors="replace").strip()
    if not stdout:
        return SocialDispatchResult(
            status="dispatch_failed",
            will_send=False,
            delivery_status="failed",
            delivery_reason=stderr or "social_bridge_empty_response",
            external_message_id="",
            platform=channel_type,
            raw={},
        )
    try:
        bridge_payload = json.loads(stdout.splitlines()[-1])
    except json.JSONDecodeError:
        return SocialDispatchResult(
            status="dispatch_failed",
            will_send=False,
            delivery_status="failed",
            delivery_reason="social_bridge_invalid_json",
            external_message_id="",
            platform=channel_type,
            raw={"stdout": stdout, "stderr": stderr},
        )

    if not bridge_payload.get("ok"):
        return SocialDispatchResult(
            status="dispatch_failed",
            will_send=False,
            delivery_status="failed",
            delivery_reason=str(bridge_payload.get("error") or stderr or "social_dispatch_failed"),
            external_message_id="",
            platform=channel_type,
            raw=bridge_payload,
        )

    result = bridge_payload.get("result", {}) if isinstance(bridge_payload.get("result"), dict) else {}
    external_message_id = (
        str(result.get("messageId") or "")
        or str(result.get("id") or "")
        or str(result.get("message_id") or "")
    )
    if result.get("ok") is False:
        return SocialDispatchResult(
            status="dispatch_failed",
            will_send=False,
            delivery_status="failed",
            delivery_reason=str(result.get("error") or result.get("reason") or "social_dispatch_failed"),
            external_message_id=external_message_id,
            platform=str(result.get("platform") or channel_type),
            raw=result,
        )

    delivery_status = "sent"
    if result.get("skipped"):
        delivery_status = "skipped"
    return SocialDispatchResult(
        status="dispatched",
        will_send=delivery_status == "sent",
        delivery_status=delivery_status,
        delivery_reason=str(result.get("reason") or ""),
        external_message_id=external_message_id,
        platform=str(result.get("platform") or channel_type),
        raw=result,
    )


def _bridge_env(settings: Settings) -> dict[str, str]:
    env = dict(os.environ)
    env.update(
        {
            "FEISHU_VERIFICATION_TOKEN": settings.feishu_verification_token,
            "FEISHU_APP_ID": settings.feishu_app_id,
            "FEISHU_APP_SECRET": settings.feishu_app_secret,
            "WECHAT_OFFICIAL_TOKEN": settings.wechat_official_token,
            "WECHAT_OFFICIAL_APP_ID": settings.wechat_official_app_id,
            "WECHAT_OFFICIAL_APP_SECRET": settings.wechat_official_app_secret,
            "WECOM_INCOMING_TOKEN": settings.wecom_incoming_token,
            "WECOM_BOT_KEY": settings.wecom_bot_key,
            "DISCORD_BOT_TOKEN": settings.discord_bot_token,
            "QQ_NAPCAT_BASE_URL": settings.qq_napcat_base_url,
            "QQ_NAPCAT_TOKEN": settings.qq_napcat_token,
            "PYTHONUTF8": "1",
        }
    )
    return env
