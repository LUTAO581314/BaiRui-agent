# bairui Commercial Go/No-Go Report

This is the final operator report for commercial trial readiness.

## 1. Decision Inputs

Run from a clean repository checkout:

```powershell
.\scripts\commercial-go-no-go.ps1
```

For a real customer handoff, require target-server evidence:

```powershell
.\scripts\commercial-go-no-go.ps1 -RequireServerEvidence -RequirePostgresEvidence
```

The report writes `artifacts/commercial-go-no-go.json`.

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
- frontend commercial closure hooks exist;
- server deployment verification passes;
- PostgreSQL production verification passes;
- handoff docs are present.

## 3. No-Go Criteria

No-go when any of these are still unverified:

- customer-facing brand leakage;
- secret leakage;
- missing deploy assets;
- frontend commercial closure missing;
- missing server deployment evidence;
- missing PostgreSQL production evidence;
- incomplete handoff docs.

## 4. Final Handoff

If the report status is `go`, attach:

- `artifacts/commercial-go-no-go.json`
- `artifacts/server-deployment-verification.json`
- `artifacts/postgres-production-verification.json`
- `artifacts/product-acceptance.json`
- `artifacts/commercial-handoff-bundle/manifest.json`

If any target-server or PostgreSQL artifact is missing, the decision is still
blocked even if local demo checks pass.
