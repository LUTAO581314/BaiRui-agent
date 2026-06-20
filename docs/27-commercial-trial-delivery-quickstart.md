# bairui Commercial Trial Delivery Quickstart

This guide is the operator handoff for a commercial trial build. It turns the
current source tree into a usable local or server demo while keeping the public
product surface under the `bairui` brand only.

## 0. Customer-Visible Brand Rule

Customer-facing UI, activation copy, setup steps, public contracts, demo
reports, and exported operator instructions must expose only `bairui`.

Historical source names, upstream runtime names, and third-party repository
names are internal engineering attribution. Keep them in engineering docs,
license files, or vendor boundaries. Do not show them in the activation page,
console labels, customer quickstart, product screenshots, or public product
contract.

## 1. Local Trial Quickstart

Use this path for the first customer-facing walkthrough on a Windows laptop or
local development workstation.

```powershell
python -m pip install -r requirements.txt
python -m src.hermes demo flow
python -m src.hermes serve
```

Open the console:

```text
http://127.0.0.1:8787/console
```

The local demo flow creates trial evidence for dashboard, command, report,
memory review, channel approval, CodeGraph, runtime readiness, metrics, and
diagnostics. Demo data is local evidence only:

- `will_send=false`
- no external dispatch
- no automatic long-term memory write
- owner approval remains required for sends and memory promotion

## 2. First Activation Guide

Use this when the recipient only has the package and a fresh machine.

1. Open `/console`.
2. Choose an activation mode:
   - Local trial.
   - Local production.
   - Server production.
3. Open Settings and fill the required fields for that mode.
4. Save configuration.
5. Refresh checks and confirm `/config/status`, `/ready`, and
   `/runtime/readiness`.
6. Open Activation and verify each step shows ready, partial, or blocked with
   a visible repair action.
7. Open Events and export diagnostics after the demo flow.

If the machine is on Windows, keep the path inputs inside the allowed bairui
workspace, data, log, vault, or `~/bairui` / `~/.bairui` roots.

## 3. Windows Local Deployment Guide

Use this for laptop demos and internal rehearsals.

```powershell
python -m pip install -r requirements.txt
.\scripts\deploy-usable.ps1 -Mode local
python -m src.hermes demo flow
```

Open:

```text
http://127.0.0.1:8787/console
```

Then run:

```powershell
.\scripts\smoke-test.ps1
.\scripts\product-acceptance.ps1
.\scripts\check-server-prereqs.ps1 -Mode local
.\scripts\verify-server-deployment.ps1 -BaseUrl http://127.0.0.1:8787 -RequireReady
.\scripts\verify-postgres-production.ps1
.\scripts\commercial-go-no-go.ps1
```

## 4. Server / Domain Deployment Guide

Use this when the package is installed on a real server or domain host.

1. Copy `infra/hermes/env.example` to a protected server path.
2. Set the model gateway, owner token, PostgreSQL URL, and data roots.
3. Run:

```powershell
.\scripts\check-server-prereqs.ps1 -Mode domain -Domain bairui.example.com -RequireDocker -RequireEnv
.\scripts\deploy-usable.ps1 -Mode domain -Domain bairui.example.com
.\scripts\verify-server-deployment.ps1 -BaseUrl https://bairui.example.com -RequireReady -RequirePostgreSQL
.\scripts\verify-postgres-production.ps1 -RequireDatabase -RunMigration
.\scripts\run-wecom-channel-trial.ps1 -BotKey "<enterprise-wecom-bot-key>" -Text "bairui commercial channel trial"
python -m src.hermes channels receipts
.\scripts\commercial-go-no-go.ps1 -RequireServerEvidence -RequirePostgresEvidence -RequireWeComTrial
```

Linux server equivalent when PowerShell is not installed:

```bash
REQUIRE_DATABASE=1 RUN_MIGRATION=1 bash scripts/verify-postgres-production.sh
BOT_KEY="<enterprise-wecom-bot-key>" TEXT="bairui commercial channel trial" bash scripts/run-wecom-channel-trial.sh
REQUIRE_SERVER_EVIDENCE=1 REQUIRE_POSTGRES_EVIDENCE=1 REQUIRE_WECOM_TRIAL=1 bash scripts/commercial-go-no-go.sh
```

4. Export the operator handoff bundle:

```powershell
.\scripts\export-commercial-handoff-bundle.ps1 -IncludeDocs
```

## 5. Common Error Handling

`owner_token_required`

- Fix: save the owner token locally or set the server token.

`confirmation_required`

- Fix: type `APPLY BAIRUI CONFIG` before risky config saves.

`missing_config`

- Fix: open Settings, fill the missing field, then refresh checks.

`missing_wecom_bot_key` or `target_not_found` for `wecom:webhook:`

- Fix: set `WECOM_BOT_KEY` in Settings or the protected server environment.
- Verify: run `python -m src.hermes channels wecom-trial --text "bairui channel trial"` first. It should create an approval without sending.
- Final trial: run `python -m src.hermes channels wecom-trial --text "bairui channel trial" --approve` only after the owner is ready to send a real Enterprise WeCom group message.
- Operator shortcut: run `.\scripts\run-wecom-channel-trial.ps1 -BotKey "<enterprise-wecom-bot-key>"` to save the Bot Key, create approval, approve, send, and export the receipt without echoing secrets.
- Linux shortcut: run `BOT_KEY="<enterprise-wecom-bot-key>" bash scripts/run-wecom-channel-trial.sh` for the same guarded receipt flow.

`outside the allowed bairui path scope`

- Fix: move the path under the allowed workspace or `~/bairui` / `~/.bairui`.

`PostgreSQL unavailable`

- Fix: verify the target server, credentials, driver, and migration state.
- Linux evidence: run `REQUIRE_DATABASE=1 RUN_MIGRATION=1 bash scripts/verify-postgres-production.sh`.

## 6. Commercial Trial Checklist

Go only when all items are true:

- `/console` opens.
- Activation mode is selected.
- Settings can save and verify configuration.
- Owner-token gating is visible.
- PostgreSQL migration and backup plan are visible.
- Enterprise WeCom channel trial is verified when real external sending is part
  of the customer pilot.
- Documents -> Memory Review -> Reports -> Channels -> Events can be shown in order.
- Events can export diagnostics and the handoff pack.
- Customer UI shows only `bairui`.
- GitHub CI is green.

## 7. Verification Commands

Run these before a customer trial handoff:

```powershell
.\scripts\smoke-test.ps1
.\scripts\smoke-test.ps1 -FullAcceptance
.\scripts\product-acceptance.ps1
.\scripts\config-doctor.ps1
.\scripts\check-public-brand.ps1
```

Use `-FullAcceptance` when preparing a release candidate or guided demo. It
checks the product closure flow and expands into five acceptance scenarios:
research task, document knowledge base, customer communication draft, code
understanding, and runtime diagnostics.

## 8. Console Activation Details

The activation page is not a public website. It is the first-use product setup
surface for a customer/operator.

1. Open `/console` and start the activation screen.
2. Confirm the local or server runtime address.
3. Configure model gateway, data directory, log directory, vault directory,
   document output directory, CodeGraph root, and channel targets as needed.
4. If owner-token protection is enabled, set `BAIRUI_OWNER_TOKEN` on the server
   or local process.
5. Use `X-Bairui-Owner-Token` or `Authorization: Bearer <token>` for write API
   calls and protected console actions.
6. For risky self-service config fields, type the confirmation phrase:

```text
APPLY BAIRUI CONFIG
```

7. Keep configured paths inside the allowed bairui workspace/data/log/vault
   scope, or under `~/bairui` / `~/.bairui`.
8. Run `python -m src.hermes demo flow` or the dashboard `Run Demo Flow` action.
9. Open Events and export diagnostics after verification.

Owner-token protection blocks write APIs when `BAIRUI_OWNER_TOKEN` is set and a
matching token is not provided. Denied write attempts are audited.

## 9. Deployment Script Details

For local usable deployment:

```powershell
.\scripts\deploy-usable.ps1 -Mode local
```

For Linux shell deployment:

```bash
bash scripts/deploy-usable.sh
```

For commercial Linux service assets:

```bash
sh infra/hermes/scripts/deploy-hermes.sh
```

Copy `infra/hermes/env.example` to a protected server path before service
install. Set real values there. Never commit secrets, customer data, runtime
logs, QR state, generated media, or diagnostics bundles.

Both usable deployment scripts poll `/health`, `/ready`,
`/runtime/readiness`, `/frontend/contract`, and `/demo/flow`, then write local
readiness evidence to `data/readiness.json`.

## 10. Observability And Support Commands

HTTP endpoints:

- `GET /health`
- `GET /ready`
- `GET /runtime/readiness`
- `GET /metrics`
- `GET /errors`
- `GET /diagnostics/bundle`

CLI commands:

```powershell
python -m src.hermes status
python -m src.hermes runtime-readiness
python -m src.hermes admin-session
python -m src.hermes diagnostics
python -m src.hermes metrics
python -m src.hermes errors
python -m src.hermes backup status
python -m src.hermes backup plan
python -m src.hermes config-status
python -m src.hermes deployment-checklist --format markdown
python -m src.hermes delivery-status
python -m src.hermes channels wecom-trial --text "bairui channel trial"
python -m src.hermes channels receipts
python -m src.hermes events
```

Console support actions:

- Dashboard: run demo flow and inspect checkpoint evidence.
- Settings: apply self-service config with path and confirmation checks.
- Events: load metrics.
- Events: export diagnostics.
- Channels: inspect disabled, approval-required, and missing-config targets.
- Channels: run `python -m src.hermes channels wecom-trial --text "bairui channel trial"` to create a governed enterprise group approval without dispatch.
- Channels: run the same command with `--approve` only for a real external-send acceptance check.

Diagnostics are redacted before export. They summarize counts, readiness,
configuration status, metrics, recent errors, and audit events without echoing
owner tokens or secret values.

## 11. Common Errors Reference

`owner_token_required`

- Meaning: write protection is enabled.
- Fix: provide `X-Bairui-Owner-Token` or `Authorization: Bearer <token>`.
- Verify: run `python -m src.hermes admin-session` from the server shell and
  check the console Settings page for the local admin identity state.

`confirmation_required`

- Meaning: a risky self-service config field needs explicit operator approval.
- Fix: type `APPLY BAIRUI CONFIG` and retry only after reviewing the change.

`outside the allowed bairui path scope`

- Meaning: a configured path points outside the permitted workspace/data/log
  scope.
- Fix: move the path under the bairui workspace, `~/bairui`, or `~/.bairui`.

`missing_config`

- Meaning: a runtime, channel, model gateway, parser, or storage dependency is
  not configured.
- Fix: open Settings or the relevant screen, fill required references, and run
  readiness again.

PostgreSQL unavailable or missing dependency

- Meaning: production database mode cannot connect or the Python database
  driver is unavailable.
- Fix: verify `POSTGRES_DB`, `POSTGRES_USER`, server address, password source,
  network access, and installed dependencies. The current product still has a
  JSONL fallback for local use.

Model gateway missing

- Meaning: model-backed agents cannot run yet.
- Fix: configure the OpenAI-compatible gateway endpoint, model name, and secret
  reference. Do not expose secrets in screenshots or logs.

Document parser missing

- Meaning: document ingestion can plan or show readiness, but parsing runtime is
  not available.
- Fix: configure the parser runtime and re-run readiness before promising file
  ingestion to a trial customer.

## 12. PostgreSQL And Backup Note

The source tree includes PostgreSQL schema, migration, and guarded backup
planning foundations, while local demos can still use JSONL-backed storage.
Before real customer data is accepted, validate production PostgreSQL
connection, migration, backup, restore, and rollback on the target server.

```powershell
python -m src.hermes backup status
python -m src.hermes backup plan
python -m src.hermes backup restore-plan --backup-path .\data\backups\postgres\example.dump
```

Restore planning is blocked unless the artifact exists and the operator types
the confirmation phrase `RESTORE BAIRUI POSTGRES`.

Do not treat a local JSONL demo as production persistence readiness.

## 13. Third-Party Attribution Boundary

Third-party source and runtime references are allowed in internal engineering
documents, license notices, dependency metadata, and vendor runtime folders.
They are not allowed in public product labels, activation copy, console routes,
customer reports, setup text, or exported customer-facing contract fields.

Before a paid trial, review the third-party attribution inventory in
`docs/28-third-party-attribution-inventory.md` and confirm every enabled runtime
license is compatible with the planned customer deployment model.

## 14. Detailed Go/No-Go Checklist

Go only when all items are true:

- Customer-visible surfaces expose only `bairui`.
- `python -m src.hermes demo flow` succeeds.
- `/console` opens and core screens render.
- `.\scripts\smoke-test.ps1 -FullAcceptance` succeeds on Windows.
- `.\scripts\product-acceptance.ps1` succeeds.
- `.\scripts\config-doctor.ps1` returns actionable diagnostics.
- `.\scripts\check-public-brand.ps1` confirms customer UI and contract assets
  expose only the `bairui` brand.
- `/metrics`, `/errors`, and `/diagnostics/bundle` return redacted support data.
- Owner-token gating is enabled and tested for the trial environment.
- `python -m src.hermes admin-session` reports owner-token status without
  returning the token value.
- `python -m src.hermes delivery-status` is ready, or its only blocker is a
  consciously deferred external channel trial.
- `python -m src.hermes deployment-checklist --format markdown` has no required
  blocker and is attached to the operator handoff.
- `python -m src.hermes channels wecom-trial --text "bairui channel trial"
  --approve` has passed when the customer pilot requires a real enterprise
  group send.
- `artifacts/wecom-receipt.json` or `python -m src.hermes channels receipts`
  proves the real Enterprise WeCom send was archived without secret echo.
- Risky config fields require `APPLY BAIRUI CONFIG`.
- Demo evidence shows `will_send=false` and no automatic long-term memory write.
- Deployment writes `data/readiness.json`.
- PostgreSQL backup/restore is validated before real customer data.
- Third-party license and attribution review is complete with
  `docs/28-third-party-attribution-inventory.md` before paid delivery.

No-go when any customer data, external sending, memory promotion, model gateway
secret, parser runtime, backup/restore, or license boundary is unverified.
