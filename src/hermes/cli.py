from __future__ import annotations

import argparse
import json
from dataclasses import asdict, is_dataclass
from typing import Any

from . import __version__
from .capabilities import collect_capabilities
from .config import ensure_runtime_dirs, load_settings
from .db import database_status, run_migrations
from .license import load_license
from .model_gateway import complete_chat
from .platform import build_platform_heartbeat
from .server import serve
from .storage import create_job, list_audit_events, list_jobs, write_obsidian_report


def _normalize(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, tuple):
        return list(value)
    return value


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=_normalize))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m src.hermes",
        description="bairui Agent OS Hermes runtime CLI",
    )
    subcommands = parser.add_subparsers(dest="command")

    subcommands.add_parser("serve", help="Start the Hermes HTTP server")
    subcommands.add_parser("status", help="Print health, readiness, license, and database status")
    subcommands.add_parser("capabilities", help="List runtime and vendor capabilities")
    subcommands.add_parser("license", help="Inspect the configured license file")
    subcommands.add_parser("jobs", help="List recent file-backed jobs")
    subcommands.add_parser("audit", help="List recent audit events")
    subcommands.add_parser("migrate", help="Run PostgreSQL schema migrations")
    subcommands.add_parser("heartbeat", help="Print the platform heartbeat payload")
    subcommands.add_parser("paths", help="Print runtime paths and key configuration")

    job_parser = subcommands.add_parser("job", help="Create a queued job")
    job_parser.add_argument("--title", default="CLI job")
    job_parser.add_argument("--prompt", required=True)
    job_parser.add_argument("--route", default="general")

    chat_parser = subcommands.add_parser("chat", help="Run one OpenAI-compatible model gateway chat")
    chat_parser.add_argument("--prompt", required=True)
    chat_parser.add_argument("--system", default="")

    report_parser = subcommands.add_parser("report", help="Write one markdown report into the Obsidian vault")
    report_parser.add_argument("--title", default="Hermes CLI Report")
    report_parser.add_argument("--body", required=True)

    return parser


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command = args.command or "serve"

    settings = load_settings()
    ensure_runtime_dirs(settings)

    if command == "serve":
        serve(settings)
        return 0

    if command == "status":
        license_state = load_license(settings.license_file, settings.license_secret)
        db_state = database_status(settings)
        print_json(
            {
                "service": "hermes",
                "version": __version__,
                "product": settings.product_name,
                "brand_key": settings.brand_key,
                "env": settings.env,
                "host": settings.host,
                "port": settings.port,
                "license": license_state,
                "database": db_state,
                "platform": "configured" if settings.platform_base_url else "missing_config",
                "server_id": "configured" if settings.server_id else "missing_config",
            }
        )
        return 0

    if command == "capabilities":
        print_json({"service": "hermes", "capabilities": collect_capabilities(settings)})
        return 0

    if command == "license":
        print_json({"service": "hermes", "license": load_license(settings.license_file, settings.license_secret)})
        return 0

    if command == "jobs":
        print_json({"service": "hermes", "jobs": list_jobs(settings.data_dir)})
        return 0

    if command == "audit":
        print_json({"service": "hermes", "audit": list_audit_events(settings.data_dir)})
        return 0

    if command == "migrate":
        result = run_migrations(settings)
        print_json({"service": "hermes", "database": result})
        return 0 if result.status == "ready" else 1

    if command == "heartbeat":
        print_json({"service": "hermes", "heartbeat": build_platform_heartbeat(settings)})
        return 0

    if command == "paths":
        print_json(
            {
                "service": "hermes",
                "data_dir": str(settings.data_dir),
                "log_dir": str(settings.log_dir),
                "obsidian_vault_dir": str(settings.obsidian_vault_dir),
                "license_file": str(settings.license_file),
                "vendor_dir": str(settings.vendor_dir),
            }
        )
        return 0

    if command == "job":
        job = create_job(settings.data_dir, title=args.title, prompt=args.prompt, route=args.route)
        print_json({"service": "hermes", "job": job})
        return 0

    if command == "chat":
        result = complete_chat(settings, args.prompt, system=args.system)
        print_json({"service": "hermes", "chat": result})
        return 0 if result.status == "completed" else 1

    if command == "report":
        report = write_obsidian_report(settings.obsidian_vault_dir, settings.data_dir, title=args.title, body=args.body)
        print_json({"service": "hermes", "report": report})
        return 0

    parser.error(f"unknown command: {command}")
    return 2


def main() -> None:
    raise SystemExit(run())
