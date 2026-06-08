"""Performance budgets and routing hints for the minimal Hermes runtime."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class PerformanceProfile:
    """Human-visible latency targets and slow-work routing thresholds."""

    quick_ack_delay_ms: int
    fast_reply_target_ms: int
    slow_task_threshold_ms: int
    async_task_timeout_seconds: int
    latency_telemetry_enabled: bool


def build_performance_profile(config: Any) -> PerformanceProfile:
    return PerformanceProfile(
        quick_ack_delay_ms=config.social_quick_ack_delay_ms,
        fast_reply_target_ms=config.social_fast_reply_target_ms,
        slow_task_threshold_ms=config.slow_task_threshold_ms,
        async_task_timeout_seconds=config.async_task_timeout_seconds,
        latency_telemetry_enabled=config.latency_telemetry_enabled,
    )


def performance_payload(config: Any) -> dict[str, Any]:
    """Return a safe public payload with no secrets or provider credentials."""

    profile = build_performance_profile(config)
    return {
        "status": "ok",
        "profile": asdict(profile),
        "latency_budgets": {
            "social_quick_ack": "send a short human-like acknowledgement before slow work",
            "fast_reply": "answer simple social messages directly within the target",
            "slow_task": "move image, search, company, and long reasoning jobs to async flow",
            "final_result": "slow acknowledgements never count as final delivery",
        },
        "routing_slots": {
            "fast": config.ai_fast_model,
            "reasoning": config.ai_reasoning_model,
            "vision": config.ai_vision_model,
        },
    }
