"""Safe latency telemetry primitives for agent turns."""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import time
from typing import Any
from uuid import uuid4


ALLOWED_STAGES = {
    "intake_ms",
    "quick_ack_ms",
    "context_ms",
    "first_token_ms",
    "tool_ms",
    "final_send_ms",
    "total_ms",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class LatencyRecord:
    turn_id: str
    route: str
    status: str
    started_at: str
    stages: dict[str, int]
    total_ms: int


class LatencyTrace:
    def __init__(self, recorder: "LatencyRecorder", route: str = "unknown") -> None:
        self._recorder = recorder
        self.turn_id = uuid4().hex
        self.route = route
        self.started_at = utc_now()
        self._started = time.perf_counter()
        self._marks: dict[str, int] = {}

    def mark(self, stage: str) -> None:
        if stage not in ALLOWED_STAGES:
            raise ValueError(f"unknown latency stage: {stage}")
        self._marks[stage] = int((time.perf_counter() - self._started) * 1000)

    def finish(self, status: str = "ok") -> LatencyRecord:
        total_ms = int((time.perf_counter() - self._started) * 1000)
        stages = dict(self._marks)
        stages["total_ms"] = total_ms
        record = LatencyRecord(
            turn_id=self.turn_id,
            route=self.route,
            status=status,
            started_at=self.started_at,
            stages=stages,
            total_ms=total_ms,
        )
        self._recorder.add(record)
        return record


class LatencyRecorder:
    def __init__(self, max_records: int = 200) -> None:
        self._records: deque[LatencyRecord] = deque(maxlen=max_records)

    def trace(self, route: str = "unknown") -> LatencyTrace:
        return LatencyTrace(self, route=route)

    def add(self, record: LatencyRecord) -> None:
        self._records.append(record)

    def add_external(
        self,
        *,
        route: str,
        stages: dict[str, Any],
        status: str = "ok",
        turn_id: str | None = None,
    ) -> LatencyRecord:
        safe_stages: dict[str, int] = {}
        for key, value in stages.items():
            if key not in ALLOWED_STAGES:
                continue
            try:
                safe_stages[key] = max(0, int(value))
            except (TypeError, ValueError):
                continue
        total_ms = safe_stages.get("total_ms", max(safe_stages.values(), default=0))
        record = LatencyRecord(
            turn_id=(turn_id or uuid4().hex)[:64],
            route=str(route or "unknown")[:80],
            status=str(status or "ok")[:40],
            started_at=utc_now(),
            stages=safe_stages,
            total_ms=total_ms,
        )
        self.add(record)
        return record

    def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 200))
        return [asdict(item) for item in list(self._records)[-limit:]]


def latency_payload(recorder: LatencyRecorder, limit: int = 50) -> dict[str, Any]:
    return {
        "status": "ok",
        "allowed_stages": sorted(ALLOWED_STAGES),
        "records": recorder.recent(limit),
    }
