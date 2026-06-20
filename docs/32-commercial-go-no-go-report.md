# bairui Commercial Go/No-Go Report

This is the final operator report for commercial trial readiness.

## 1. Decision Inputs

Run from a clean repository checkout:

```powershell
.\scripts\commercial-go-no-go.ps1
```

For console-friendly output while keeping full evidence in JSON:

```powershell
.\scripts\commercial-go-no-go.ps1 -SummaryOnly
```

For a real customer handoff, require target-server evidence:

```powershell
.\scripts\commercial-go-no-go.ps1 -RequireServerEvidence -RequirePostgresEvidence
```

For a customer pilot that includes real outbound enterprise group delivery,
configure the enterprise group Bot Key, run the governed channel trial, and require that
evidence in Go/No-Go:

```powershell
python -m src.hermes channels wecom-trial --text "bairui commercial channel trial"
python -m src.hermes channels wecom-trial --text "bairui commercial channel trial" --approve
python -m src.hermes document parse memory-trial
.\scripts\commercial-go-no-go.ps1 -RequireServerEvidence -RequirePostgresEvidence -RequireWeComTrial
```

Operator shortcut for the real Enterprise WeCom receipt:

```powershell
.\scripts\run-wecom-channel-trial.ps1 -BotKey "<enterprise-wecom-bot-key>" -Text "bairui commercial channel trial"
```

Linux equivalent:

```bash
REQUIRE_DATABASE=1 RUN_MIGRATION=1 bash scripts/verify-postgres-production.sh
BOT_KEY="<enterprise-wecom-bot-key>" TEXT="bairui commercial channel trial" bash scripts/run-wecom-channel-trial.sh
```

Linux server equivalent:

```bash
REQUIRE_SERVER_EVIDENCE=1 REQUIRE_POSTGRES_EVIDENCE=1 REQUIRE_WECOM_TRIAL=1 bash scripts/commercial-go-no-go.sh
```

Linux summary-only equivalent:

```bash
SUMMARY_ONLY=1 bash scripts/commercial-go-no-go.sh
```

The report writes `artifacts/commercial-go-no-go.json`.
It also writes `artifacts/deployment-checklist.json` and
`artifacts/deployment-checklist.md` so the operator can see missing activation
and server configuration without reading raw logs.

After the report exists, export the operator-safe evidence bundle:

```powershell
.\scripts\export-commercial-handoff-bundle.ps1 -IncludeDocs
```

The bundle writes `artifacts/commercial-handoff-bundle/manifest.json` and
regenerates local product acceptance and Go/No-Go evidence by default.

## 2. Go Criteria

Go only when:

- `check-public-brand.ps1` passes;
- `check-repo-hygiene.ps1` passes;
- `check-deploy-assets.ps1` passes;
- `product-acceptance.ps1` passes;
- document memory trial passes with completed ingest, memory review, graph sync,
  report, and source references;
- frontend commercial closure hooks exist;
- server deployment verification passes;
- PostgreSQL production verification passes;
- enterprise group bot channel trial passes when real outbound delivery is part of
  the customer pilot;
- handoff docs are present.

## 3. No-Go Criteria

No-go when any of these are still unverified:

- customer-facing brand leakage;
- secret leakage;
- missing deploy assets;
- frontend commercial closure missing;
- missing server deployment evidence;
- missing PostgreSQL production evidence;
- missing enterprise group bot trial evidence when external sending is required;
- failed document memory trial evidence;
- incomplete handoff docs.

## 4. Final Handoff

If the report status is `go`, attach:

- `artifacts/commercial-go-no-go.json`
- `artifacts/deployment-checklist.json`
- `artifacts/deployment-checklist.md`
- `artifacts/delivery-status.json`
- `artifacts/wecom-trial.json`
- `artifacts/wecom-receipt.json`
- `artifacts/server-deployment-verification.json`
- `artifacts/postgres-production-verification.json`
- `artifacts/postgres-production-failure-summary.md` when PostgreSQL checks are
  failed or blocked
- `artifacts/product-acceptance.json`
- `artifacts/commercial-handoff-bundle/manifest.json`

If any target-server or PostgreSQL artifact is missing, the decision is still
blocked even if local demo checks pass.
