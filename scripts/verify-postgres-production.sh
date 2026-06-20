#!/usr/bin/env bash
set -euo pipefail

OUTPUT_PATH="${OUTPUT_PATH:-artifacts/postgres-production-verification.json}"
FAILURE_SUMMARY_PATH="${FAILURE_SUMMARY_PATH:-artifacts/postgres-production-failure-summary.md}"
SAMPLE_BACKUP_PATH="${SAMPLE_BACKUP_PATH:-data/backups/postgres/sample-verification.dump}"
RUN_MIGRATION="${RUN_MIGRATION:-0}"
REQUIRE_DATABASE="${REQUIRE_DATABASE:-0}"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --output-path)
      OUTPUT_PATH="${2:-}"
      shift 2
      ;;
    --failure-summary-path)
      FAILURE_SUMMARY_PATH="${2:-}"
      shift 2
      ;;
    --sample-backup-path)
      SAMPLE_BACKUP_PATH="${2:-}"
      shift 2
      ;;
    --run-migration)
      RUN_MIGRATION="1"
      shift
      ;;
    --require-database)
      REQUIRE_DATABASE="1"
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

PYTHON_BIN="${PYTHON_BIN:-python}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  else
    echo "python or python3 is required." >&2
    exit 1
  fi
fi

mkdir -p "$(dirname "$OUTPUT_PATH")" "$(dirname "$FAILURE_SUMMARY_PATH")" "$(dirname "$SAMPLE_BACKUP_PATH")"

run_json() {
  local label="$1"
  shift
  "$PYTHON_BIN" - "$label" "$@" <<'PY'
import json
import subprocess
import sys

label = sys.argv[1]
cmd = sys.argv[2:]
proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
raw = proc.stdout
try:
    payload = json.loads(raw)
    ok = proc.returncode == 0
    error = ""
except Exception:
    payload = None
    ok = False
    error = f"{label} non-json output: {raw.strip()}"
print(json.dumps({"ok": ok, "exit_code": proc.returncode, "payload": payload, "error": error}, ensure_ascii=False))
PY
}

"$PYTHON_BIN" - "$OUTPUT_PATH" "$FAILURE_SUMMARY_PATH" "$SAMPLE_BACKUP_PATH" "$RUN_MIGRATION" "$REQUIRE_DATABASE" <<'PY'
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

output_path = Path(sys.argv[1])
failure_summary_path = Path(sys.argv[2])
sample_backup_path = Path(sys.argv[3])
run_migration = sys.argv[4] == "1"
require_database = sys.argv[5] == "1"


def check(id, name, status, evidence, next_step):
    return {
        "id": id,
        "name": name,
        "status": status,
        "evidence": evidence,
        "next_step": next_step,
    }


def run_cli(*args):
    proc = subprocess.run([sys.executable, "-m", "src.hermes", *args], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        payload = json.loads(proc.stdout)
        return {"ok": proc.returncode == 0, "exit_code": proc.returncode, "payload": payload, "error": ""}
    except Exception:
        return {"ok": False, "exit_code": proc.returncode, "payload": None, "error": f"non-json output: {proc.stdout.strip()}"}


def secret_safe(text):
    if re.search(r"postgresql://[^\"'\s]+:[^\"'\s]+@", text):
        return False
    if re.search(r"password|secret|token", text, re.IGNORECASE):
        return bool(re.search(r"never printed|never returned|configured or missing|HERMES_DATABASE_URL|\$HERMES_DATABASE_URL", text))
    return True


def evidence_summary(payload, kind):
    if not payload:
        return None
    if kind == "migration":
        db = payload.get("database", {})
        return {"status": db.get("status", ""), "detail": db.get("detail", "")}
    if kind == "backup_status":
        backup = payload.get("backup", {})
        return {
            "status": backup.get("status", ""),
            "detail": backup.get("detail", ""),
            "backup_dir": backup.get("backup_dir", ""),
            "latest_backup": backup.get("latest_backup", ""),
            "restore_requires_confirmation": backup.get("restore_requires_confirmation", True),
        }
    if kind == "backup_plan":
        plan = payload.get("backup_plan", {})
        return {
            "status": plan.get("status", ""),
            "database": plan.get("database", {}),
            "backup_dir": plan.get("backup_dir", ""),
            "command": plan.get("command", ""),
            "secret_policy": plan.get("secret_policy", ""),
            "creates_customer_data": plan.get("creates_customer_data", True),
        }
    if kind == "restore_plan":
        plan = payload.get("restore_plan", {})
        return {
            "status": plan.get("status", ""),
            "database": plan.get("database", {}),
            "command": plan.get("command", ""),
            "confirmation_phrase": plan.get("confirmation_phrase", ""),
            "confirmed": plan.get("confirmed", False),
            "blockers": plan.get("blockers", []),
            "destructive": plan.get("destructive", True),
            "secret_policy": plan.get("secret_policy", ""),
        }
    if kind == "config_status":
        config = payload.get("config_status", {})
        database = next((item for item in config.get("items", []) if item.get("id") == "database"), {})
        return {"status": config.get("status", ""), "database": database, "secret_policy": config.get("secret_policy", "")}
    return payload


checks = []
evidence = {}

schema = Path("src/hermes/db.py").read_text(encoding="utf-8")
requirements = {
    "jobs": "create table if not exists jobs",
    "audit_logs": "create table if not exists audit_logs",
    "source_refs": "create table if not exists source_refs",
    "agent_sessions": "create table if not exists agent_sessions",
    "agent_events": "create table if not exists agent_events",
    "codegraph_repos": "create table if not exists codegraph_repos",
    "codegraph_files": "create table if not exists codegraph_files",
    "codegraph_symbols": "create table if not exists codegraph_symbols",
}
missing = [key for key, needle in requirements.items() if needle not in schema]
if not missing:
    checks.append(check("schema_core_tables", "Core production schema coverage", "passed", "jobs, audit_logs, source_refs, agent sessions, and CodeGraph tables are present", "Run migration on the target PostgreSQL instance."))
else:
    checks.append(check("schema_core_tables", "Core production schema coverage", "failed", f"missing: {', '.join(missing)}", "Add migrations for missing commercial product state before production."))

if run_migration:
    migration = run_cli("migrate")
    evidence["migration"] = evidence_summary(migration["payload"], "migration")
    if migration["ok"]:
        checks.append(check("migration", "PostgreSQL migration command", "passed", "migration command returned ready", "Record this output in the database production proof."))
    else:
        checks.append(check("migration", "PostgreSQL migration command", "failed", f"exit={migration['exit_code']}; {migration['error']}", "Configure HERMES_DATABASE_URL and PostgreSQL access, then rerun migration."))
elif require_database:
    checks.append(check("migration", "PostgreSQL migration command", "blocked", "real migration was not run", "Rerun with --run-migration on the target PostgreSQL server."))
else:
    checks.append(check("migration", "PostgreSQL migration command", "blocked", "dry-run mode; migration command not executed", "Use --run-migration --require-database on a real server."))

backup_status = run_cli("backup", "status")
evidence["backup_status"] = evidence_summary(backup_status["payload"], "backup_status")
if backup_status["ok"]:
    checks.append(check("backup_status", "Backup readiness status", "passed", "backup status command returned acceptable state", "Continue to backup plan validation."))
elif require_database:
    checks.append(check("backup_status", "Backup readiness status", "failed", f"exit={backup_status['exit_code']}; {backup_status['error']}", "Configure HERMES_DATABASE_URL before production backup validation."))
else:
    checks.append(check("backup_status", "Backup readiness status", "blocked", "backup status requires configured PostgreSQL for production proof", "Use --require-database on a real server."))

backup_plan = run_cli("backup", "plan")
evidence["backup_plan"] = evidence_summary(backup_plan["payload"], "backup_plan")
backup_text = json.dumps(backup_plan["payload"], ensure_ascii=False)
if backup_plan["ok"] and "pg_dump" in backup_text and "$HERMES_DATABASE_URL" in backup_text and secret_safe(backup_text):
    checks.append(check("backup_plan", "Secret-safe backup plan", "passed", "pg_dump plan uses $HERMES_DATABASE_URL without printing the database URL", "Run the command during the server backup validation window."))
elif require_database:
    checks.append(check("backup_plan", "Secret-safe backup plan", "failed", "backup plan unavailable or secret policy failed", "Fix backup planning before production handoff."))
else:
    checks.append(check("backup_plan", "Secret-safe backup plan", "blocked", "backup plan requires configured PostgreSQL for production proof", "Use --require-database on a real server."))

sample_backup_path.parent.mkdir(parents=True, exist_ok=True)
sample_backup_path.write_text("verification only", encoding="utf-8")
try:
    blocked_restore = run_cli("backup", "restore-plan", "--backup-path", str(sample_backup_path.resolve()))
    ready_restore = run_cli("backup", "restore-plan", "--backup-path", str(sample_backup_path.resolve()), "--confirm-restore", "RESTORE BAIRUI POSTGRES")
    evidence["restore_plan_blocked"] = evidence_summary(blocked_restore["payload"], "restore_plan")
    evidence["restore_plan_confirmed"] = evidence_summary(ready_restore["payload"], "restore_plan")
    blocked_text = json.dumps(blocked_restore["payload"], ensure_ascii=False)
    ready_text = json.dumps(ready_restore["payload"], ensure_ascii=False)
    blocked_ok = "RESTORE BAIRUI POSTGRES" in blocked_text and "blocked" in blocked_text
    ready_ok = "pg_restore" in ready_text and "$HERMES_DATABASE_URL" in ready_text and '"destructive": true' in ready_text
    if blocked_ok and ready_ok and secret_safe(blocked_text) and secret_safe(ready_text):
        checks.append(check("restore_guardrail", "Restore guardrail and confirmation", "passed", "restore is blocked without typed confirmation and uses pg_restore with $HERMES_DATABASE_URL", "Run restore only on a disposable test database before production use."))
    else:
        checks.append(check("restore_guardrail", "Restore guardrail and confirmation", "failed", "restore plan did not prove confirmation, destructive flag, or secret policy", "Fix restore guardrails before production handoff."))
finally:
    try:
        sample_backup_path.unlink()
    except FileNotFoundError:
        pass

config_status = run_cli("config-status")
evidence["config_status"] = evidence_summary(config_status["payload"], "config_status")
settings_text = json.dumps(config_status["payload"], ensure_ascii=False)
if '"database"' in settings_text and re.search(r"never returned|configured or missing|secret", settings_text):
    checks.append(check("settings_database_visibility", "Settings database visibility", "passed", "Settings diagnostics expose database state without returning secrets", "Confirm the same state is visible in Settings on the target server."))
else:
    checks.append(check("settings_database_visibility", "Settings database visibility", "failed", "database state or secret policy missing from config status", "Fix Settings database diagnostics before trial handoff."))

evidence_text = json.dumps(evidence, ensure_ascii=False)
if secret_safe(evidence_text):
    checks.append(check("secret_redaction", "Database secret redaction", "passed", "database URL/password were not printed in verification evidence", "Keep raw database credentials only in protected environment files."))
else:
    checks.append(check("secret_redaction", "Database secret redaction", "failed", "verification evidence appears to contain raw database credentials", "Remove secret output before customer handoff."))

blocking = {"failed"}
if require_database:
    blocking.add("blocked")
blocked = [item for item in checks if item["status"] in blocking]
status = "passed" if not blocked else "failed"
report = {
    "service": "bairui",
    "mode": "postgres_production_verification",
    "status": status,
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "require_database": require_database,
    "run_migration": run_migration,
    "checks": checks,
    "evidence": evidence,
    "secret_echo": False,
}
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

actionable = [item for item in checks if item["status"] in {"failed", "blocked"}]
lines = [
    "# bairui PostgreSQL Production Failure Summary",
    "",
    f"- status: {status}",
    f"- require_database: {require_database}",
    f"- run_migration: {run_migration}",
    f"- generated_at: {report['generated_at']}",
    "",
]
if actionable:
    lines += ["| Check | Status | Evidence | Next step |", "| --- | --- | --- | --- |"]
    for item in actionable:
        lines.append(f"| {item['id']} | {item['status']} | {item['evidence']} | {item['next_step']} |")
else:
    lines.append("No failed or blocked PostgreSQL checks were recorded.")
failure_summary_path.parent.mkdir(parents=True, exist_ok=True)
failure_summary_path.write_text("\n".join(lines), encoding="utf-8")

print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
if status != "passed":
    raise SystemExit(1)
PY
