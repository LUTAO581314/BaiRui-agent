# bairui Commercial Trial Handoff Pack

This pack is the customer-trial operator index. It does not replace the source
docs; it tells the operator what to open, what to run, and what evidence to
export before a bairui trial is handed to a customer.

## 1. First Activation Guide

Start here for every trial:

1. Open `/console`.
2. Choose an activation mode:
   - Local trial / demo.
   - Local production.
   - Server / domain production.
3. Open Settings and fill the mode-specific configuration profile.
4. Save configuration.
5. Confirm the automatic apply verification block shows `/config/status`,
   `/ready`, and `/runtime/readiness`.
6. Open Activation and confirm each startup layer is ready, partial with a
   visible next step, or blocked with a visible repair action.
7. Open Events and export diagnostics after the demo flow.

Required safety evidence:

- owner-token gate is visible;
- secret fields are write-only and never echoed;
- dangerous changes require `APPLY BAIRUI CONFIG`;
- channel drafts show `will_send=false`;
- real Enterprise WeCom channel trial uses `channels wecom-trial --approve`
  and records a receipt before the pilot is marked externally deliverable;
- memory candidates require explicit approval;
- public product copy shows only `bairui`.

In the console, open Settings -> Delivery check entry to see the same ordered
handoff commands, evidence paths, and links to this handoff pack and the
quickstart guide. Use Events from the same entry to export diagnostics after the
trial flow.

## 2. Windows Local Deployment Guide

Use Windows local deployment for laptop demos and internal trial rehearsals.

```powershell
python -m pip install -r requirements.txt
python -m src.hermes demo flow
python -m src.hermes serve
```

Open:

```text
http://127.0.0.1:8787/console
```

Run:

```powershell
.\scripts\smoke-test.ps1
.\scripts\smoke-test.ps1 -FullAcceptance
.\scripts\product-acceptance.ps1
.\scripts\check-server-prereqs.ps1 -Mode local
.\scripts\verify-server-deployment.ps1 -BaseUrl http://127.0.0.1:8787 -RequireReady
.\scripts\verify-postgres-production.ps1
.\scripts\commercial-go-no-go.ps1
.\scripts\export-commercial-handoff-bundle.ps1
.\scripts\config-doctor.ps1
.\scripts\check-public-brand.ps1
```

Windows handoff evidence:

- smoke-test output;
- product-acceptance output;
- server-prereq-check output;
- server-deployment-verification output;
- postgres-production-verification output;
- commercial-go-no-go output;
- commercial-handoff-bundle manifest;
- Settings security boundary checklist screenshot;
- Events diagnostics export;
- Events handoff pack export.

## 3. Server / Domain Deployment Guide

Use server / domain production only when the server identity, owner token,
PostgreSQL URL, data paths, DNS, HTTPS, and reverse proxy are controlled by the
operator.

Preparation:

1. Copy `infra/hermes/env.example` to a protected server-side path.
2. Set real values for model gateway, owner token, PostgreSQL, data paths, and
   platform identity.
3. Never commit secrets, customer data, runtime logs, QR state, generated media,
   or diagnostics bundles.
4. Run the preflight check:

```powershell
.\scripts\check-server-prereqs.ps1 -Mode domain -Domain bairui.example.com -RequireDocker -RequireEnv
```

5. Run the usable deployment script:

```bash
bash scripts/deploy-usable.sh
```

For Windows server preparation:

```powershell
.\scripts\deploy-usable.ps1 -Mode domain -Domain bairui.example.com
```

After the service is reachable, capture target-server evidence:

```powershell
.\scripts\verify-server-deployment.ps1 -BaseUrl https://bairui.example.com -RequireReady -RequirePostgreSQL
```

Or run the full server trial acceptance chain:

```powershell
.\scripts\run-server-trial-acceptance.ps1 -Mode domain -Domain bairui.example.com -BaseUrl https://bairui.example.com -RequireDocker -RequireEnv -RequirePostgres -IncludeDocs
```

Linux server equivalent:

```bash
MODE=domain DOMAIN=bairui.example.com BASE_URL=https://bairui.example.com REQUIRE_POSTGRES=1 INCLUDE_DOCS=1 bash scripts/run-server-trial-acceptance.sh
```

If the Linux server does not have PowerShell installed, use the native Bash
commercial gate:

```bash
REQUIRE_SERVER_EVIDENCE=1 REQUIRE_POSTGRES_EVIDENCE=1 REQUIRE_WECOM_TRIAL=1 bash scripts/commercial-go-no-go.sh
```

Then validate the production database:

```powershell
.\scripts\verify-postgres-production.ps1 -RequireDatabase -RunMigration
```

Finally run Go/No-Go with required server evidence:

```powershell
python -m src.hermes channels wecom-trial --text "bairui commercial channel trial"
python -m src.hermes channels wecom-trial --text "bairui commercial channel trial" --approve
python -m src.hermes channels receipts
.\scripts\commercial-go-no-go.ps1 -RequireServerEvidence -RequirePostgresEvidence -RequireWeComTrial
```

Export the operator handoff bundle:

```powershell
.\scripts\export-commercial-handoff-bundle.ps1 -IncludeDocs
```

Verify:

- `GET /health`
- `GET /ready`
- `GET /runtime/readiness`
- `GET /frontend/contract`
- `GET /metrics`
- `GET /errors`
- `GET /diagnostics/bundle`
- `python -m src.hermes delivery-status`
- `python -m src.hermes channels wecom-trial --text "bairui channel trial"`
- `python -m src.hermes channels wecom-trial --text "bairui channel trial" --approve`
- `artifacts/server-prereq-check.json`
- `artifacts/server-trial-acceptance.json`
- `artifacts/server-trial-failure-summary.md`
- `artifacts/server-trial-execution-plan.md`
- `data/readiness.json`
- `artifacts/server-deployment-verification.json`
- `artifacts/postgres-production-verification.json`
- `artifacts/postgres-production-failure-summary.md`
- `artifacts/delivery-status.json`
- `artifacts/wecom-trial.json`
- `artifacts/wecom-receipt.json`
- `artifacts/commercial-go-no-go.json`
- `artifacts/commercial-handoff-bundle/manifest.json`

Do not mark server deployment ready until `/console`, owner-token protected
actions, Settings config apply, PostgreSQL readiness, and Events diagnostics
all work on the target server.

## 4. Common Error Handling

`owner_token_required`

- Fix: save the owner token in Settings or send `X-Bairui-Owner-Token`.
- Evidence: Settings local admin identity block.

`confirmation_required`

- Fix: type `APPLY BAIRUI CONFIG` only after reviewing the dangerous fields.
- Evidence: Settings apply result and audit event.

`missing_config`

- Fix: use Activation and Settings to identify the missing runtime or path.
- Evidence: `/runtime/readiness` and Settings configuration profile.

Enterprise WeCom trial blocked

- Fix: configure `WECOM_BOT_KEY` in Settings or the protected server
  environment. Do not put the Bot Key into target JSON.
- Evidence: `python -m src.hermes channels wecom-trial --text "bairui channel trial"`
  creates an approval without external send.
- Final evidence: rerun with `--approve`, confirm the group received the
  message, and keep the recorded `delivery_status` / `external_message_id`.

Path scope error

- Fix: move the path inside the bairui workspace, configured data/log/vault
  roots, `~/bairui`, or `~/.bairui`.
- Evidence: Settings security boundary checklist.

PostgreSQL unavailable

- Fix: verify server address, credentials, database, migration status, and
  Python driver.
- Evidence: Settings data persistence operations and backup plan.

## 5. Commercial Trial Checklist

Go only when every item is true:

- GitHub CI is green.
- `.\scripts\check-public-brand.ps1` passes.
- `/console` opens on the target machine.
- Activation mode is selected.
- Settings config can be saved and automatically verified.
- Owner-token write gate is visible and tested.
- PostgreSQL migration and backup plan are visible.
- PostgreSQL production verification report is saved.
- `python -m src.hermes delivery-status` is ready for the target server.
- Enterprise WeCom external-send trial has passed when the pilot includes real
  outbound social delivery.
- Events can load metrics, errors, and diagnostics.
- Server prerequisite report is saved for the operator.
- Server trial acceptance report is saved for the operator when the runner is
  used.
- Server deployment verification report is saved for the operator.
- Commercial Go/No-Go report is `go`.
- Commercial handoff bundle manifest is saved for the operator.
- Documents -> Memory Review -> Reports -> Channels -> Events demo evidence is
  available.
- Events handoff pack export is saved for the operator.
- Third-party attribution review has been checked in
  `docs/28-third-party-attribution-inventory.md`.

No-go when any customer data, external sending, memory promotion, model gateway
secret, parser runtime, backup/restore, or license boundary is unverified.

## 6. Evidence Exports

Use these console exports for trial handoff:

- Documents: Export Ingest Pack.
- Memory Review: Export Memory or Export Candidate.
- Reports: Export Reports or Export Delivery.
- Channels: Export Queue or Export Approval.
- Events: Export Diagnostics and Export Handoff Pack.

Exports are customer-safe JSON. They must not include model API keys, owner
tokens, PostgreSQL URLs, passwords, authorization headers, or local file
contents.

Use the CLI handoff bundle after the reports exist:

```powershell
.\scripts\export-commercial-handoff-bundle.ps1 -IncludeDocs
```

The bundle writes `artifacts/commercial-handoff-bundle/manifest.json`. By
default it regenerates local product acceptance and Go/No-Go reports, then
copies selected report JSON and optional documentation snapshots. It must not
contain `.env`, secrets, customer files, raw logs, QR state, generated media, or
runtime dumps.
