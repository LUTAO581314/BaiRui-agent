"""Rule-first route classification for latency-aware agent turns."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import re
from typing import Any


class RouteType(str, Enum):
    CASUAL_CHAT = "casual_chat"
    QUICK_QUESTION = "quick_question"
    IMAGE_READ = "image_read"
    IMAGE_GENERATE = "image_generate"
    SEARCH = "search"
    PUBLIC_OPINION = "public_opinion"
    COMPANY_TASK = "company_task"
    MEMORY_TASK = "memory_task"
    HIGH_RISK = "high_risk"


@dataclass(frozen=True)
class RoutePolicy:
    route: RouteType
    model_slot: str
    memory_depth: str
    tool_group: str
    quick_ack: bool
    async_required: bool
    approval_required: bool
    latency_budget_ms: int


IMAGE_READ_RE = re.compile(
    r"(\[image attachments\]|analyze_image|ocr|screenshot|read image|image recognition|"
    r"look at (this )?(image|picture|photo)|image|picture|photo)",
    re.I,
)
IMAGE_GENERATE_RE = re.compile(
    r"(generate image|image generation|create image|draw|paint|sticker|avatar|"
    r"gpt-image|image2)",
    re.I,
)
SEARCH_RE = re.compile(r"(search|browse|look up|fetch|http://|https://|source|latest)", re.I)
PUBLIC_OPINION_RE = re.compile(
    r"(trend|trending|hot list|hotspot|public opinion|sentiment|news|feed)", re.I
)
COMPANY_RE = re.compile(
    r"(feishu|lark|company|project|task|approval|calendar|doc|table|department|"
    r"employee|meeting|crm|sales|receivable)",
    re.I,
)
MEMORY_RE = re.compile(r"(memory|remember|forget|obsidian|dream|consolidat)", re.I)
HIGH_RISK_RE = re.compile(
    r"(trade|trading|buy stock|sell stock|money movement|wire transfer|delete all|"
    r"approve expense|hr action|legal promise|destructive)",
    re.I,
)


def classify_route(message: str, config: Any) -> RoutePolicy:
    """Classify an inbound message before heavy context or tool loading.

    This is intentionally rule-first. A model can refine the route later, but the
    first pass must be cheap, deterministic, and safe.
    """

    text = str(message or "").strip()
    lower = text.lower()
    fast_budget = config.social_fast_reply_target_ms
    slow_budget = config.slow_task_threshold_ms

    if HIGH_RISK_RE.search(lower):
        return RoutePolicy(
            route=RouteType.HIGH_RISK,
            model_slot="reasoning",
            memory_depth="policy_only",
            tool_group="approval_gate",
            quick_ack=True,
            async_required=False,
            approval_required=True,
            latency_budget_ms=fast_budget,
        )

    if IMAGE_GENERATE_RE.search(lower):
        return RoutePolicy(
            route=RouteType.IMAGE_GENERATE,
            model_slot="image_generation",
            memory_depth="recent_only",
            tool_group="image_generation",
            quick_ack=True,
            async_required=True,
            approval_required=False,
            latency_budget_ms=slow_budget,
        )

    if IMAGE_READ_RE.search(lower):
        return RoutePolicy(
            route=RouteType.IMAGE_READ,
            model_slot="vision",
            memory_depth="recent_only",
            tool_group="vision",
            quick_ack=True,
            async_required=True,
            approval_required=False,
            latency_budget_ms=slow_budget,
        )

    if PUBLIC_OPINION_RE.search(lower):
        return RoutePolicy(
            route=RouteType.PUBLIC_OPINION,
            model_slot="summary",
            memory_depth="source_policy",
            tool_group="trend_search",
            quick_ack=True,
            async_required=True,
            approval_required=False,
            latency_budget_ms=slow_budget,
        )

    if SEARCH_RE.search(lower):
        return RoutePolicy(
            route=RouteType.SEARCH,
            model_slot="summary",
            memory_depth="source_policy",
            tool_group="search",
            quick_ack=True,
            async_required=True,
            approval_required=False,
            latency_budget_ms=slow_budget,
        )

    if COMPANY_RE.search(lower):
        return RoutePolicy(
            route=RouteType.COMPANY_TASK,
            model_slot="reasoning",
            memory_depth="company_policy",
            tool_group="company_read",
            quick_ack=True,
            async_required=True,
            approval_required=True,
            latency_budget_ms=slow_budget,
        )

    if MEMORY_RE.search(lower):
        return RoutePolicy(
            route=RouteType.MEMORY_TASK,
            model_slot="reasoning",
            memory_depth="memory_governance",
            tool_group="memory_review",
            quick_ack=True,
            async_required=True,
            approval_required=True,
            latency_budget_ms=slow_budget,
        )

    if len(text) <= 18 and not text.endswith("?"):
        return RoutePolicy(
            route=RouteType.CASUAL_CHAT,
            model_slot="fast",
            memory_depth="identity_recent",
            tool_group="send_only",
            quick_ack=False,
            async_required=False,
            approval_required=False,
            latency_budget_ms=fast_budget,
        )

    return RoutePolicy(
        route=RouteType.QUICK_QUESTION,
        model_slot="fast",
        memory_depth="critical_recent",
        tool_group="minimal",
        quick_ack=False,
        async_required=False,
        approval_required=False,
        latency_budget_ms=fast_budget,
    )


def route_payload(message: str, config: Any) -> dict[str, Any]:
    policy = classify_route(message, config)
    return {
        "status": "ok",
        "route": asdict(policy),
        "message_preview_chars": min(len(str(message or "")), 160),
    }
