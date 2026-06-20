#!/usr/bin/env bash
set -euo pipefail

MODE="${MODE:-local}"
DOMAIN="${DOMAIN:-}"
BASE_URL="${BASE_URL:-http://127.0.0.1:8787}"
OUTPUT_PATH="${OUTPUT_PATH:-artifacts/server-trial-acceptance.json}"
FAILURE_SUMMARY_PATH="${FAILURE_SUMMARY_PATH:-artifacts/server-trial-failure-summary.md}"
EXECUTION_PLAN_PATH="${EXECUTION_PLAN_PATH:-artifacts/server-trial-execution-plan.md}"
READINESS_FILE="${READINESS_FILE:-data/readiness.json}"
SKIP_DEPLOY="${SKIP_DEPLOY:-0}"
SKIP_SERVER_VERIFICATION="${SKIP_SERVER_VERIFICATION:-0}"
SKIP_POSTGRES="${SKIP_POSTGRES:-0}"
REQUIRE_POSTGRES="${REQUIRE_POSTGRES:-0}"
INCLUDE_DOCS="${INCLUDE_DOCS:-0}"

step_statuses=()
step_json_files=()

find_command() {
  local candidate
  for candidate in "$@"; do
    if command -v "$candidate" >/dev/null 2>&1; then
      command -v "$candidate"
      return 0
    fi
  done
  return 1
}

PYTHON_BIN="${PYTHON_BIN:-}"
if [[ -z "$PYTHON_BIN" ]]; then
  PYTHON_BIN="$(find_command python3 python py || true)"
fi
if [[ -z "$PYTHON_BIN" ]]; then
  echo "python3, python, or py is required for server trial acceptance." >&2
  exit 1
fi

PWSH_BIN="${PWSH_BIN:-}"
if [[ -z "$PWSH_BIN" ]]; then
  PWSH_BIN="$(find_command pwsh powershell.exe powershell || true)"
fi
if [[ -z "$PWSH_BIN" ]]; then
  echo "pwsh or powershell was not found; PowerShell-only steps will be skipped with repair guidance." >&2
fi

json_escape() {
  "$PYTHON_BIN" - "$1" <<'PY'
import json
import sys
print(json.dumps(sys.argv[1]))
PY
}

read_json_or_null() {
  local path="$1"
  if [[ -f "$path" ]]; then
    cat "$path"
  else
    printf 'null'
  fi
}

json_status() {
  local path="$1"
  if [[ ! -f "$path" ]]; then
    printf 'missing'
    return 0
  fi
  "$PYTHON_BIN" - "$path" <<'PY'
import json
import sys
try:
    raw = open(sys.argv[1], "rb").read()
    for encoding in ("utf-8-sig", "utf-16"):
        try:
            data = json.loads(raw.decode(encoding))
            print(data.get("status", "passed"))
            break
        except Exception:
            continue
    else:
        print("failed")
except Exception:
    print("failed")
PY
}

write_step() {
  local id="$1"
  local name="$2"
  local status="$3"
  local evidence="$4"
  local next_step="$5"
  local target="artifacts/server-trial-acceptance-steps/${id}.json"
  mkdir -p "$(dirname "$target")"
  "$PYTHON_BIN" - "$id" "$name" "$status" "$evidence" "$next_step" "$target" <<'PY'
import json
import sys
payload = {
    "id": sys.argv[1],
    "name": sys.argv[2],
    "status": sys.argv[3],
    "evidence": sys.argv[4],
    "next_step": sys.argv[5],
}
with open(sys.argv[6], "w", encoding="utf-8") as handle:
    json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
    handle.write("\n")
PY
  step_statuses+=("$status")
  step_json_files+=("$target")
}

run_step() {
  local id="$1"
  local name="$2"
  local evidence_path="$3"
  local next_step="$4"
  local allow_blocked="$5"
  shift 5

  if "$@"; then
    local status
    status="$(json_status "$evidence_path")"
    if [[ "$status" == "blocked" && "$allow_blocked" != "1" ]]; then
      status="failed"
    fi
    write_step "$id" "$name" "$status" "$evidence_path" "$next_step"
  else
    write_step "$id" "$name" "failed" "$*" "$next_step"
  fi
}

skip_step() {
  write_step "$1" "$2" "skipped" "skipped by operator" "$3"
}

if [[ "$MODE" != "local" && "$MODE" != "domain" ]]; then
  echo "MODE must be local or domain" >&2
  exit 1
fi
if [[ "$MODE" == "domain" && -z "$DOMAIN" ]]; then
  echo "DOMAIN is required when MODE=domain" >&2
  exit 1
fi

mkdir -p artifacts

if [[ -z "$PWSH_BIN" ]]; then
  skip_step "preflight" "Server prerequisite preflight" "Install pwsh/powershell or run scripts/check-server-prereqs.ps1 from an operator machine."
else
  preflight_cmd=("$PWSH_BIN" -NoLogo -NoProfile -File scripts/check-server-prereqs.ps1 -Mode "$MODE" -OutputPath artifacts/server-prereq-check.json)
  if [[ "$MODE" == "domain" ]]; then
    preflight_cmd+=(-Domain "$DOMAIN")
  fi
  run_step "preflight" "Server prerequisite preflight" "artifacts/server-prereq-check.json" "Fix failed prerequisite checks before deploying." 0 "${preflight_cmd[@]}"
fi

if [[ "$SKIP_DEPLOY" == "1" ]]; then
  skip_step "deploy" "Usable deployment" "Run deploy-usable.sh on the target server."
else
  MODE="$MODE" DOMAIN="$DOMAIN" HERMES_LOCAL_URL="$BASE_URL" READINESS_FILE="$READINESS_FILE" \
    run_step "deploy" "Usable deployment" "$READINESS_FILE" "Inspect Docker, service logs, ports, reverse proxy, and readiness output." 0 bash scripts/deploy-usable.sh
fi

if [[ "$SKIP_SERVER_VERIFICATION" == "1" ]]; then
  skip_step "server_verification" "Post-deployment server verification" "Run verify-server-deployment.ps1 against the target server before customer handoff."
elif [[ -z "$PWSH_BIN" ]]; then
  skip_step "server_verification" "Post-deployment server verification" "Install pwsh/powershell or run verify-server-deployment.ps1 from an operator machine."
else
  verify_cmd=("$PWSH_BIN" -NoLogo -NoProfile -File scripts/verify-server-deployment.ps1 -BaseUrl "$BASE_URL" -ReadinessFile "$READINESS_FILE" -OutputPath artifacts/server-deployment-verification.json -RequireReady)
  if [[ "$REQUIRE_POSTGRES" == "1" ]]; then
    verify_cmd+=(-RequirePostgreSQL)
  fi
  run_step "server_verification" "Post-deployment server verification" "artifacts/server-deployment-verification.json" "Fix failed endpoints, console routing, owner gate, config status, or PostgreSQL visibility." 0 "${verify_cmd[@]}"
fi

if [[ "$SKIP_POSTGRES" == "1" ]]; then
  skip_step "postgres_verification" "PostgreSQL production verification" "Run verify-postgres-production.ps1 -RequireDatabase -RunMigration or verify-postgres-production.sh --require-database --run-migration on the target database."
else
  if [[ -n "$PWSH_BIN" ]]; then
    postgres_cmd=("$PWSH_BIN" -NoLogo -NoProfile -File scripts/verify-postgres-production.ps1 -OutputPath artifacts/postgres-production-verification.json)
  else
    postgres_cmd=(bash scripts/verify-postgres-production.sh --output-path artifacts/postgres-production-verification.json)
  fi
  allow_postgres_blocked="1"
  if [[ "$REQUIRE_POSTGRES" == "1" ]]; then
    if [[ -n "$PWSH_BIN" ]]; then
      postgres_cmd+=(-RequireDatabase -RunMigration)
    else
      postgres_cmd+=(--require-database --run-migration)
    fi
    allow_postgres_blocked="0"
  fi
  run_step "postgres_verification" "PostgreSQL production verification" "artifacts/postgres-production-verification.json" "Fix migration, backup, restore guardrail, or database visibility evidence." "$allow_postgres_blocked" "${postgres_cmd[@]}"
fi

allow_go_blocked="0"
if [[ "$SKIP_DEPLOY" == "1" || "$SKIP_SERVER_VERIFICATION" == "1" || "$SKIP_POSTGRES" == "1" || "$REQUIRE_POSTGRES" != "1" ]]; then
  allow_go_blocked="1"
fi
if [[ -z "$PWSH_BIN" ]]; then
  skip_step "commercial_go_no_go" "Commercial Go/No-Go" "Install pwsh/powershell for commercial-go-no-go.ps1, or run commercial-go-no-go.sh manually after evidence exists."
else
  go_cmd=("$PWSH_BIN" -NoLogo -NoProfile -File scripts/commercial-go-no-go.ps1 -OutputPath artifacts/commercial-go-no-go.json)
  if [[ "$SKIP_DEPLOY" != "1" && "$SKIP_SERVER_VERIFICATION" != "1" ]]; then
    go_cmd+=(-RequireServerEvidence)
  fi
  if [[ "$REQUIRE_POSTGRES" == "1" && "$SKIP_POSTGRES" != "1" ]]; then
    go_cmd+=(-RequirePostgresEvidence)
  fi
  run_step "commercial_go_no_go" "Commercial Go/No-Go" "artifacts/commercial-go-no-go.json" "Resolve failed or blocked final gate checks before customer handoff." "$allow_go_blocked" "${go_cmd[@]}"
fi

if [[ -z "$PWSH_BIN" ]]; then
  skip_step "handoff_bundle" "Commercial handoff bundle" "Install pwsh/powershell or run export-commercial-handoff-bundle.ps1 from an operator machine."
else
  bundle_cmd=("$PWSH_BIN" -NoLogo -NoProfile -File scripts/export-commercial-handoff-bundle.ps1 -OutputDir artifacts/commercial-handoff-bundle)
  if [[ "$INCLUDE_DOCS" == "1" ]]; then
    bundle_cmd+=(-IncludeDocs)
  fi
  run_step "handoff_bundle" "Commercial handoff bundle" "artifacts/commercial-handoff-bundle/manifest.json" "Attach the bundle manifest and selected report JSON to the operator handoff." 0 "${bundle_cmd[@]}"
fi

"$PYTHON_BIN" - "$OUTPUT_PATH" "$FAILURE_SUMMARY_PATH" "$EXECUTION_PLAN_PATH" "$MODE" "$DOMAIN" "$BASE_URL" "$READINESS_FILE" "$REQUIRE_POSTGRES" "$SKIP_DEPLOY" "$SKIP_SERVER_VERIFICATION" "$SKIP_POSTGRES" "${step_json_files[@]}" <<'PY'
import json
import sys
from datetime import datetime, timezone

output_path, failure_summary_path, execution_plan_path, mode, domain, base_url, readiness_file = sys.argv[1:8]
require_postgres, skip_deploy, skip_server_verification, skip_postgres = sys.argv[8:12]
step_files = sys.argv[12:]
steps = []
for path in step_files:
    with open(path, "r", encoding="utf-8") as handle:
        steps.append(json.load(handle))
failed = [item for item in steps if item["status"] == "failed"]
blocked = [item for item in steps if item["status"] == "blocked"]
skipped = [item for item in steps if item["status"] == "skipped"]
status = "failed" if failed else "blocked" if (blocked or skipped) else "passed"
evidence_paths = {
    "preflight": "artifacts/server-prereq-check.json",
    "server_verification": "artifacts/server-deployment-verification.json",
    "postgres_verification": "artifacts/postgres-production-verification.json",
    "commercial_go_no_go": "artifacts/commercial-go-no-go.json",
    "handoff_bundle": "artifacts/commercial-handoff-bundle/manifest.json",
}
payload = {
    "service": "bairui",
    "mode": "server_trial_acceptance",
    "status": status,
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "deployment_mode": mode,
    "domain": domain,
    "base_url": base_url.rstrip("/"),
    "readiness_file": readiness_file,
    "require_postgres": require_postgres == "1",
    "skip_deploy": skip_deploy == "1",
    "skip_server_verification": skip_server_verification == "1",
    "skip_postgres": skip_postgres == "1",
    "failure_summary_path": failure_summary_path,
    "execution_plan_path": execution_plan_path,
    "steps": steps,
    "evidence_paths": evidence_paths,
    "decision": {
        "ready_for_customer_trial": status == "passed",
        "failed_count": len(failed),
        "blocked_count": len(blocked),
        "skipped_count": len(skipped),
        "next_step": (
            "Customer trial can proceed with this evidence bundle."
            if status == "passed"
            else "Fix failed server acceptance steps and rerun."
            if failed
            else "Run skipped or blocked target-server/database steps before real customer handoff."
        ),
    },
}
with open(output_path, "w", encoding="utf-8") as handle:
    json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
    handle.write("\n")
actionable = [item for item in steps if item["status"] in {"failed", "blocked", "skipped"}]
lines = [
    "# bairui Server Trial Failure Summary",
    "",
    f"- status: {status}",
    f"- base_url: {base_url.rstrip('/')}",
    f"- deployment_mode: {mode}",
    f"- generated_at: {payload['generated_at']}",
    "",
]
if actionable:
    lines.extend([
        "| Step | Status | Evidence | Next step |",
        "| --- | --- | --- | --- |",
    ])
    for item in actionable:
        lines.append(f"| {item['id']} | {item['status']} | {item['evidence']} | {item['next_step']} |")
else:
    lines.append("No failed, blocked, or skipped steps were recorded.")
with open(failure_summary_path, "w", encoding="utf-8") as handle:
    handle.write("\n".join(lines))
    handle.write("\n")
base = base_url.rstrip("/")
plan = [
    "# bairui Server Trial Execution Plan",
    "",
    f"- deployment_mode: {mode}",
    f"- domain: {domain}",
    f"- base_url: {base}",
    f"- readiness_file: {readiness_file}",
    f"- require_postgres: {require_postgres == '1'}",
    "",
    "## Target Server Commands",
    "",
]
if mode == "domain":
    plan.extend([
        "```powershell",
        f".\\scripts\\check-server-prereqs.ps1 -Mode domain -Domain {domain} -RequireDocker -RequireEnv",
        f".\\scripts\\deploy-usable.ps1 -Mode domain -Domain {domain}",
        f".\\scripts\\verify-server-deployment.ps1 -BaseUrl {base} -ReadinessFile {readiness_file} -RequireReady -RequirePostgreSQL",
        ".\\scripts\\verify-postgres-production.ps1 -RequireDatabase -RunMigration",
        ".\\scripts\\commercial-go-no-go.ps1 -RequireServerEvidence -RequirePostgresEvidence",
        ".\\scripts\\export-commercial-handoff-bundle.ps1 -IncludeDocs",
        "```",
        "",
        "```bash",
        f"MODE=domain DOMAIN={domain} BASE_URL={base} REQUIRE_POSTGRES=1 INCLUDE_DOCS=1 bash scripts/run-server-trial-acceptance.sh",
        "```",
    ])
else:
    plan.extend([
        "```powershell",
        ".\\scripts\\check-server-prereqs.ps1 -Mode local -RequireDocker -RequireEnv",
        ".\\scripts\\deploy-usable.ps1 -Mode local",
        f".\\scripts\\verify-server-deployment.ps1 -BaseUrl {base} -ReadinessFile {readiness_file} -RequireReady",
        ".\\scripts\\verify-postgres-production.ps1 -RequireDatabase -RunMigration" if require_postgres == "1" else ".\\scripts\\verify-postgres-production.ps1",
        ".\\scripts\\commercial-go-no-go.ps1 -RequireServerEvidence -RequirePostgresEvidence" if require_postgres == "1" else ".\\scripts\\commercial-go-no-go.ps1 -RequireServerEvidence",
        ".\\scripts\\export-commercial-handoff-bundle.ps1 -IncludeDocs",
        "```",
        "",
        "```bash",
        f"MODE=local BASE_URL={base} INCLUDE_DOCS=1 bash scripts/run-server-trial-acceptance.sh",
        "```",
    ])
plan.extend([
    "",
    "## Required Evidence",
    "",
    "- artifacts/server-prereq-check.json",
    f"- {readiness_file}",
    "- artifacts/server-deployment-verification.json",
    "- artifacts/postgres-production-verification.json",
    "- artifacts/postgres-production-failure-summary.md when database checks are blocked or failed",
    "- artifacts/commercial-go-no-go.json",
    "- artifacts/commercial-handoff-bundle/manifest.json",
    "",
    "## Current Runner Skips",
    "",
    f"- deploy skipped: {skip_deploy == '1'}",
    f"- server verification skipped: {skip_server_verification == '1'}",
    f"- postgres verification skipped: {skip_postgres == '1'}",
    "",
    "If any item is skipped, blocked, or failed, do not mark the target server ready.",
])
with open(execution_plan_path, "w", encoding="utf-8") as handle:
    handle.write("\n".join(plan))
    handle.write("\n")
print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
PY

if grep -q '"status": "failed"' "$OUTPUT_PATH"; then
  echo "bairui server trial acceptance failed" >&2
  exit 1
fi
