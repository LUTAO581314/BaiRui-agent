from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from ..config import Settings


TRENDRADAR_LICENSE = "GPLv3"
TRENDRADAR_CLI_MODULE = "trendradar"
TRENDRADAR_MCP_MODULE = "mcp_server.server"


@dataclass(frozen=True)
class TrendRadarStatus:
    status: str
    detail: str
    source_path: str
    license: str
    project_root: str
    mcp_url: str
    cli_contract: tuple[str, ...]
    mcp_contract: tuple[str, ...]
    commercial_boundary: str


@dataclass(frozen=True)
class TrendRadarCommandPlan:
    status: str
    command: tuple[str, ...]
    cwd: str
    detail: str


def source_path(settings: Settings) -> Path:
    return settings.vendor_dir / "trendradar"


def project_root(settings: Settings) -> Path:
    return settings.trendradar_project_root or source_path(settings)


def status(settings: Settings) -> TrendRadarStatus:
    src = source_path(settings)
    cli_contract = (
        "python -m trendradar --doctor",
        "python -m trendradar --show-schedule",
        "python -m trendradar",
    )
    mcp_contract = (
        "python -m mcp_server.server --transport stdio",
        "python -m mcp_server.server --transport http --host 127.0.0.1 --port 3333",
        "HTTP MCP endpoint: /mcp",
    )

    if not src.exists():
        state = "missing_source"
        detail = "TrendRadar source is not present under vendor/runtimes/trendradar"
    elif not (src / "LICENSE").exists():
        state = "invalid_source"
        detail = "TrendRadar source is present but LICENSE is missing"
    elif not (src / "trendradar" / "__main__.py").exists():
        state = "invalid_source"
        detail = "TrendRadar CLI source is missing"
    elif not (src / "mcp_server" / "server.py").exists():
        state = "invalid_source"
        detail = "TrendRadar MCP server source is missing"
    elif not settings.trendradar_mcp_url:
        state = "source_ready"
        detail = "TrendRadar source is present; set TRENDRADAR_MCP_URL to enable live MCP-backed intelligence calls"
    else:
        state = "configured"
        detail = "TrendRadar source and MCP URL are configured"

    return TrendRadarStatus(
        status=state,
        detail=detail,
        source_path=str(src),
        license=TRENDRADAR_LICENSE,
        project_root=str(project_root(settings)),
        mcp_url=settings.trendradar_mcp_url,
        cli_contract=cli_contract,
        mcp_contract=mcp_contract,
        commercial_boundary="GPLv3 runtime must remain attributable and needs source-delivery review for distribution.",
    )


def build_doctor_command(settings: Settings) -> TrendRadarCommandPlan:
    root = project_root(settings)
    if status(settings).status not in {"source_ready", "configured"}:
        return TrendRadarCommandPlan(status="unavailable", command=(), cwd=str(root), detail=status(settings).detail)
    return TrendRadarCommandPlan(
        status="ready",
        command=("python", "-m", TRENDRADAR_CLI_MODULE, "--doctor"),
        cwd=str(root),
        detail="Run inside the TrendRadar project root after installing its Python dependencies.",
    )


def build_schedule_command(settings: Settings) -> TrendRadarCommandPlan:
    root = project_root(settings)
    if status(settings).status not in {"source_ready", "configured"}:
        return TrendRadarCommandPlan(status="unavailable", command=(), cwd=str(root), detail=status(settings).detail)
    return TrendRadarCommandPlan(
        status="ready",
        command=("python", "-m", TRENDRADAR_CLI_MODULE, "--show-schedule"),
        cwd=str(root),
        detail="Shows TrendRadar schedule and behavior switches using its real CLI.",
    )


def build_mcp_command(settings: Settings, *, transport: str = "http", host: str = "127.0.0.1", port: int = 3333) -> TrendRadarCommandPlan:
    root = project_root(settings)
    if status(settings).status not in {"source_ready", "configured"}:
        return TrendRadarCommandPlan(status="unavailable", command=(), cwd=str(root), detail=status(settings).detail)
    command = ("python", "-m", TRENDRADAR_MCP_MODULE, "--transport", transport)
    if transport == "http":
        command = command + ("--host", host, "--port", str(port))
    return TrendRadarCommandPlan(
        status="ready",
        command=command,
        cwd=str(root),
        detail="Starts the upstream TrendRadar MCP server without copying GPLv3 internals into Hermes core.",
    )


def as_payload(value: TrendRadarStatus | TrendRadarCommandPlan) -> dict[str, object]:
    return asdict(value)
