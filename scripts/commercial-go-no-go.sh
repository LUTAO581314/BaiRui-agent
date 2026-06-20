#!/usr/bin/env bash
set -euo pipefail

OUTPUT_PATH="${OUTPUT_PATH:-artifacts/commercial-go-no-go.json}"
SERVER_VERIFICATION_PATH="${SERVER_VERIFICATION_PATH:-artifacts/server-deployment-verification.json}"
POSTGRES_VERIFICATION_PATH="${POSTGRES_VERIFICATION_PATH:-artifacts/postgres-production-verification.json}"
DEPLOYMENT_CHECKLIST_PATH="${DEPLOYMENT_CHECKLIST_PATH:-artifacts/deployment-checklist.json}"
DEPLOYMENT_CHECKLIST_MARKDOWN_PATH="${DEPLOYMENT_CHECKLIST_MARKDOWN_PATH:-artifacts/deployment-checklist.md}"
DELIVERY_STATUS_PATH="${DELIVERY_STATUS_PATH:-artifacts/delivery-status.json}"
WECOM_TRIAL_PATH="${WECOM_TRIAL_PATH:-artifacts/wecom-trial.json}"
WECOM_RECEIPT_PATH="${WECOM_RECEIPT_PATH:-artifacts/wecom-receipt.json}"
REQUIRE_SERVER_EVIDENCE="${REQUIRE_SERVER_EVIDENCE:-0}"
REQUIRE_POSTGRES_EVIDENCE="${REQUIRE_POSTGRES_EVIDENCE:-0}"
REQUIRE_WECOM_TRIAL="${REQUIRE_WECOM_TRIAL:-0}"
SKIP_ACCEPTANCE="${SKIP_ACCEPTANCE:-0}"
SUMMARY_ONLY="${SUMMARY_ONLY:-0}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  if command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    echo "python3 or python is required." >&2
    exit 1
  fi
fi

mkdir -p "$(dirname "$OUTPUT_PATH")"

"$PYTHON_BIN" - "$OUTPUT_PATH" "$SERVER_VERIFICATION_PATH" "$POSTGRES_VERIFICATION_PATH" "$DEPLOYMENT_CHECKLIST_PATH" "$DEPLOYMENT_CHECKLIST_MARKDOWN_PATH" "$DELIVERY_STATUS_PATH" "$WECOM_TRIAL_PATH" "$WECOM_RECEIPT_PATH" "$REQUIRE_SERVER_EVIDENCE" "$REQUIRE_POSTGRES_EVIDENCE" "$REQUIRE_WECOM_TRIAL" "$SKIP_ACCEPTANCE" "$SUMMARY_ONLY" <<'PY'
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

output_path = Path(sys.argv[1])
server_verification_path = Path(sys.argv[2])
postgres_verification_path = Path(sys.argv[3])
deployment_checklist_path = Path(sys.argv[4])
deployment_checklist_markdown_path = Path(sys.argv[5])
delivery_status_path = Path(sys.argv[6])
wecom_trial_path = Path(sys.argv[7])
wecom_receipt_path = Path(sys.argv[8])
require_server = sys.argv[9] == "1"
require_postgres = sys.argv[10] == "1"
require_wecom = sys.argv[11] == "1"
skip_acceptance = sys.argv[12] == "1"
summary_only = sys.argv[13] == "1"


def run(label, command):
    try:
        completed = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except FileNotFoundError as exc:
        return {"ok": False, "code": 127, "stdout": "", "stderr": str(exc), "payload": None}
    payload = None
    raw = (completed.stdout or "").strip()
    if raw:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = None
    return {
        "ok": completed.returncode == 0,
        "code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "payload": payload,
        "label": label,
    }


def read_json(path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}


def check(id, name, status, evidence, next_step):
    return {
        "id": id,
        "name": name,
        "status": status,
        "evidence": evidence,
        "next_step": next_step,
    }


checks = []
evidence = {}

head = run("git", ["git", "rev-parse", "--short", "HEAD"])
git_head = (head["stdout"] or "").strip()
checks.append(
    check(
        "git_commit",
        "Git commit recorded",
        "passed" if git_head else "blocked",
        f"HEAD={git_head}" if git_head else "git HEAD unavailable",
        "Use this commit in the customer handoff notes.",
    )
)

brand = run("public brand scan", ["bash", "scripts/check-public-brand.sh"]) if Path("scripts/check-public-brand.sh").exists() else run("public brand scan", ["pwsh", "-NoLogo", "-NoProfile", "-File", "scripts/check-public-brand.ps1"])
checks.append(
    check(
        "public_brand",
        "Public brand boundary",
        "passed" if brand["ok"] else "failed",
        "public brand scan passed" if brand["ok"] else (brand["stderr"] or brand["stdout"] or "public brand scan failed"),
        "Keep customer-facing UI limited to bairui.",
    )
)

hygiene = run("repository hygiene", ["bash", "scripts/check-repo-hygiene.sh"]) if Path("scripts/check-repo-hygiene.sh").exists() else run("repository hygiene", ["pwsh", "-NoLogo", "-NoProfile", "-File", "scripts/check-repo-hygiene.ps1"])
checks.append(
    check(
        "repo_hygiene",
        "Repository hygiene",
        "passed" if hygiene["ok"] else "failed",
        "repository hygiene passed" if hygiene["ok"] else (hygiene["stderr"] or hygiene["stdout"] or "repository hygiene failed"),
        "Fix repository hygiene before trial.",
    )
)

required_assets = [
    "infra/hermes/env.example",
    "infra/hermes/systemd/bairui-hermes.service",
    "infra/hermes/scripts/deploy-hermes.sh",
    "scripts/deploy-usable.sh",
    "scripts/check-server-prereqs.ps1",
    "scripts/verify-server-deployment.ps1",
    "scripts/verify-postgres-production.ps1",
    "scripts/commercial-go-no-go.ps1",
    "scripts/commercial-go-no-go.sh",
    "scripts/run-server-trial-acceptance.sh",
    "docker-compose.production.yml",
    ".env.example",
]
missing_assets = [item for item in required_assets if not Path(item).exists()]
checks.append(
    check(
        "deploy_assets",
        "Deployment assets",
        "passed" if not missing_assets else "failed",
        "deployment assets are present" if not missing_assets else "missing: " + ", ".join(missing_assets),
        "Restore missing deployment assets before trial.",
    )
)

deployment_checklist = run("deployment checklist", [sys.executable, "-m", "src.hermes", "deployment-checklist"])
deployment_checklist_payload = (deployment_checklist["payload"] or {}).get("deployment_checklist", {}) if isinstance(deployment_checklist["payload"], dict) else {}
evidence["deployment_checklist"] = deployment_checklist["payload"]
if deployment_checklist["payload"]:
    deployment_checklist_path.parent.mkdir(parents=True, exist_ok=True)
    deployment_checklist_path.write_text(json.dumps(deployment_checklist["payload"], ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown = deployment_checklist_payload.get("markdown")
    if markdown:
        deployment_checklist_markdown_path.parent.mkdir(parents=True, exist_ok=True)
        deployment_checklist_markdown_path.write_text(markdown + "\n", encoding="utf-8")
checklist_passed = deployment_checklist["ok"] and deployment_checklist_payload.get("status") != "blocked"
checks.append(
    check(
        "deployment_checklist",
        "Deployment checklist",
        "passed" if checklist_passed else "blocked",
        (
            f"checklist={deployment_checklist_path}; markdown={deployment_checklist_markdown_path}; status={deployment_checklist_payload.get('status')}"
            if deployment_checklist["payload"]
            else (deployment_checklist["stderr"] or deployment_checklist["stdout"] or "deployment checklist evidence missing")
        ),
        "Fill required activation/configuration values, then rerun deployment-checklist.",
    )
)

model_probe = run("model gateway probe", [sys.executable, "-m", "src.hermes", "model-gateway", "probe"])
model_probe_payload = (model_probe["payload"] or {}).get("model_gateway_probe", {}) if isinstance(model_probe["payload"], dict) else {}
evidence["model_gateway_probe"] = model_probe["payload"]
model_probe_passed = (
    model_probe["ok"]
    and model_probe_payload.get("status") == "ready"
    and model_probe_payload.get("chat_status") == "completed"
    and model_probe_payload.get("secret_echo") is False
)
checks.append(
    check(
        "model_gateway_probe",
        "Model gateway chat probe",
        "passed" if model_probe_passed else "blocked",
        (
            f"model={model_probe_payload.get('model')}; base_url={model_probe_payload.get('base_url')}; chat_status={model_probe_payload.get('chat_status')}"
            if model_probe_passed
            else f"status={model_probe_payload.get('status', 'unknown')}; chat_status={model_probe_payload.get('chat_status', 'unknown')}; error={model_probe_payload.get('error', '')}"
        ),
        "Configure model gateway and run python -m src.hermes model-gateway probe until it returns ready.",
    )
)

if skip_acceptance:
    checks.append(check("product_acceptance", "Product demo acceptance", "blocked", "skipped by operator", "Run without SKIP_ACCEPTANCE=1 before a final Go decision."))
else:
    acceptance = run("product acceptance", [sys.executable, "-m", "src.hermes", "demo", "flow"])
    evidence["product_acceptance"] = acceptance["payload"]
    demo_status = ((acceptance["payload"] or {}).get("demo_flow", {}) if isinstance(acceptance["payload"], dict) else {}).get("status")
    acceptance_status = "passed" if demo_status == "completed" else "blocked" if demo_status == "partial" else "failed"
    checks.append(
        check(
            "product_acceptance",
            "Product demo acceptance",
            acceptance_status,
            f"demo flow status={demo_status}" if acceptance["ok"] else (acceptance["stderr"] or acceptance["stdout"] or "demo flow failed"),
            "Fix local product acceptance before any customer trial.",
        )
    )

delivery = run("delivery status", [sys.executable, "-m", "src.hermes", "delivery-status"])
delivery_payload = (delivery["payload"] or {}).get("delivery_status", {}) if isinstance(delivery["payload"], dict) else {}
evidence["delivery_status"] = delivery["payload"]
if delivery["payload"]:
    delivery_status_path.parent.mkdir(parents=True, exist_ok=True)
    delivery_status_path.write_text(json.dumps(delivery["payload"], ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
checks.append(
    check(
        "delivery_status",
        "Commercial delivery status",
        "passed" if delivery_payload.get("status") == "ready" else "blocked",
        f"status={delivery_payload.get('status', 'unknown')}; blockers={','.join(delivery_payload.get('blockers', []))}",
        delivery_payload.get("next_step") or "Resolve delivery blockers and rerun.",
    )
)

wecom = run("Enterprise group bot trial", [sys.executable, "-m", "src.hermes", "channels", "wecom-trial", "--text", "bairui commercial go/no-go channel trial", "--approve"])
wecom_payload = (wecom["payload"] or {}).get("wecom_trial", {}) if isinstance(wecom["payload"], dict) else {}
evidence["wecom_trial"] = wecom["payload"]
if wecom["payload"]:
    wecom_trial_path.parent.mkdir(parents=True, exist_ok=True)
    wecom_trial_path.write_text(json.dumps(wecom["payload"], ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
wecom_review = wecom_payload.get("review") or {}
wecom_evidence = wecom_review.get("delivery_evidence") or {}
wecom_receipt = None
wecom_receipt_source = Path(str(wecom_evidence.get("receipt_path") or "")) if wecom_evidence.get("receipt_path") else None
if wecom_receipt_source and wecom_receipt_source.exists():
    wecom_receipt = read_json(wecom_receipt_source)
    wecom_receipt_path.parent.mkdir(parents=True, exist_ok=True)
    wecom_receipt_path.write_text(json.dumps(wecom_receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
evidence["wecom_receipt"] = wecom_receipt
wecom_passed = (
    wecom_payload.get("status") == "reviewed"
    and wecom_review.get("will_send") is True
    and wecom_review.get("delivery_status") == "sent"
    and bool(wecom_review.get("external_message_id"))
    and bool(wecom_evidence)
    and wecom_evidence.get("secret_echo") is False
    and bool(wecom_receipt)
    and wecom_receipt.get("secret_echo") is False
    and wecom_receipt.get("delivery_status") == "sent"
    and bool(wecom_receipt.get("external_message_id"))
)
checks.append(
    check(
        "wecom_trial",
        "Enterprise group bot channel trial",
        "passed" if wecom_passed else "failed" if require_wecom else "blocked",
        f"enterprise-group trial dispatched and recorded receipt: external_message_id={wecom_review.get('external_message_id')}; receipt={wecom_receipt_path}" if wecom_passed else f"status={wecom_payload.get('status', 'unknown')}; next={wecom_payload.get('next_step', '')}",
        "Configure the enterprise group Bot Key, rerun channels wecom-trial --approve, and confirm the external group receipt.",
    )
)

document_memory = run(
    "Document memory trial",
    [
        sys.executable,
        "-m",
        "src.hermes",
        "document",
        "parse",
        "memory-trial",
        "--text",
        "bairui commercial go/no-go document memory trial verifies ingest, review, graph sync, report, and source references.",
    ],
)
document_memory_payload = (document_memory["payload"] or {}).get("document_memory_trial", {}) if isinstance(document_memory["payload"], dict) else {}
document_memory_evidence = document_memory_payload.get("evidence") or {}
evidence["document_memory_trial"] = document_memory["payload"]
document_memory_passed = document_memory_payload.get("status") == "completed"
checks.append(
    check(
        "document_memory_trial",
        "Document memory closure trial",
        "passed" if document_memory_passed else "failed",
        (
            "current_stage={}; candidates={}; reviews={}; source_refs={}; reports={}".format(
                document_memory_evidence.get("current_stage", "unknown"),
                document_memory_evidence.get("candidate_count", 0),
                document_memory_evidence.get("review_count", 0),
                document_memory_evidence.get("source_ref_count", 0),
                document_memory_evidence.get("report_count", 0),
            )
            if document_memory_passed
            else f"status={document_memory_payload.get('status', 'unknown')}; next={document_memory_payload.get('next_step', '')}"
        ),
        "Run python -m src.hermes document parse memory-trial and fix document ingestion, memory review, graph sync, report, or source reference blockers.",
    )
)

server_evidence = read_json(server_verification_path)
evidence["server_deployment"] = server_evidence
if server_evidence and server_evidence.get("status") == "passed":
    server_status = "passed"
    server_detail = f"server verification report passed: {server_verification_path}"
elif require_server:
    server_status = "failed"
    server_detail = f"missing or not passed: {server_verification_path}"
else:
    server_status = "blocked"
    server_detail = "not required for local dry-run; evidence missing or not passed"
checks.append(check("server_verification", "Server deployment verification", server_status, server_detail, "Run verify-server-deployment.ps1 or server acceptance on the target server."))

postgres_evidence = read_json(postgres_verification_path)
evidence["postgres_production"] = postgres_evidence
if postgres_evidence and postgres_evidence.get("status") == "passed" and postgres_evidence.get("require_database") is True:
    postgres_status = "passed"
    postgres_detail = "database production proof passed with RequireDatabase"
elif require_postgres:
    postgres_status = "failed"
    postgres_detail = f"missing or not passed: {postgres_verification_path}"
else:
    postgres_status = "blocked"
    postgres_detail = "not required for local dry-run; production database evidence missing or dry-run only"
checks.append(check("postgres_verification", "PostgreSQL production verification", postgres_status, postgres_detail, "Run verify-postgres-production.ps1 -RequireDatabase -RunMigration on the target database."))

required_docs = [
    "docs/29-commercial-trial-handoff-pack.md",
    "docs/30-server-deployment-acceptance-report.md",
    "docs/31-postgresql-production-verification.md",
    "docs/32-commercial-go-no-go-report.md",
]
missing_docs = [item for item in required_docs if not Path(item).exists()]
checks.append(
    check(
        "handoff_docs",
        "Commercial handoff documents",
        "passed" if not missing_docs else "failed",
        "handoff documents are present" if not missing_docs else "missing: " + ", ".join(missing_docs),
        "Use these documents as the operator checklist.",
    )
)

failed = [item for item in checks if item["status"] == "failed"]
blocked = [item for item in checks if item["status"] == "blocked"]
status = "no_go" if failed else "blocked" if blocked else "go"
report = {
    "service": "bairui",
    "mode": "commercial_go_no_go_linux",
    "status": status,
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "git_commit": git_head,
    "require_server_evidence": require_server,
    "require_postgres_evidence": require_postgres,
    "require_wecom_trial": require_wecom,
    "checks": checks,
    "evidence": evidence,
    "decision": {
        "go": status == "go",
        "failed_count": len(failed),
        "blocked_count": len(blocked),
        "next_step": "Customer trial can proceed with the attached evidence." if status == "go" else "Fix failed checks before trial." if failed else "Collect blocked target-server or external-channel evidence before real customer trial.",
    },
}
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
if summary_only:
    print(json.dumps({
        "service": report["service"],
        "mode": report["mode"],
        "status": report["status"],
        "output_path": str(output_path),
        "checks": [{"id": item["id"], "status": item["status"], "evidence": item["evidence"]} for item in checks],
        "decision": report["decision"],
    }, ensure_ascii=False, indent=2, sort_keys=True))
else:
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
if status == "no_go":
    raise SystemExit("bairui Linux commercial Go/No-Go failed")
PY
