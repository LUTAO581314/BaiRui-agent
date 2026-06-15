# bairui Server Deployment Acceptance Report

This report is the operator template for Step 2 commercial trial validation. It
turns a target-server deployment into repeatable evidence instead of a manual
screen check.

## 1. Target

- Deployment mode: local / domain
- Target base URL:
- Target commit:
- Operator:
- Date:
- Server notes:

## 2. Preflight

Run before deployment:

```powershell
.\scripts\check-server-prereqs.ps1 -Mode local
```

For domain production:

```powershell
.\scripts\check-server-prereqs.ps1 -Mode domain -Domain bairui.example.com -RequireDocker -RequireEnv
```

Attach:

- `artifacts/server-prereq-check.json`
- Docker / Compose version evidence
- Python version evidence
- Git commit evidence
- `.env` presence evidence without secret values
- DNS result when domain mode is used
- writable path evidence for `data`, `logs`, and `obsidian-vault`

No-go when the preflight report contains `failed` checks. `blocked` checks must
be reviewed by the operator and either fixed or explicitly accepted for a local
rehearsal.

## 3. Deployment

Run one usable deployment path:

```powershell
.\scripts\deploy-usable.ps1 -Mode local
```

or:

```bash
bash scripts/deploy-usable.sh
```

For domain production:

```powershell
.\scripts\deploy-usable.ps1 -Mode domain -Domain bairui.example.com
```

or:

```bash
MODE=domain DOMAIN=bairui.example.com bash scripts/deploy-usable.sh
```

Attach:

- deploy command output
- generated `data/readiness.json`
- `/console` screenshot after Activation, Settings, and Events are opened

## 4. Post-Deployment Verification

Run after the service is reachable:

```powershell
.\scripts\verify-server-deployment.ps1 -BaseUrl http://127.0.0.1:8787 -RequireReady
```

For domain production with PostgreSQL:

```powershell
.\scripts\verify-server-deployment.ps1 -BaseUrl https://bairui.example.com -RequireReady -RequirePostgreSQL
```

Attach:

- `artifacts/server-deployment-verification.json`
- endpoint evidence for `/health`, `/ready`, `/runtime/readiness`,
  `/frontend/contract`, `/metrics`, and `/errors`
- `/console` reachability evidence
- Demo Flow evidence with `no_external_send=true`
- Demo Flow evidence with `no_auto_memory_write=true`
- owner-token gate evidence
- Settings secret policy evidence
- PostgreSQL visibility evidence when required

## 5. PostgreSQL Production Verification

Run after `HERMES_DATABASE_URL` is configured on the target server:

```powershell
.\scripts\verify-postgres-production.ps1 -RequireDatabase -RunMigration
```

Attach:

- `artifacts/postgres-production-verification.json`
- migration evidence;
- backup status evidence;
- secret-safe backup plan evidence;
- blocked restore-plan evidence;
- confirmed restore-plan evidence;
- Settings database visibility evidence;
- secret redaction evidence.

## 6. Failure Log

Record every failure and the fix:

| Time | Check | Status | Evidence | Fix | Retest |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |

Common failure classes:

- Docker or Compose unavailable.
- `.env` missing or incomplete.
- Port already occupied.
- DNS does not resolve to the target server.
- `/ready` is partial or blocked.
- Demo Flow is partial because an optional runtime or channel is not configured.
- PostgreSQL evidence is missing when production database mode is required.
- Owner-token gate is not visible or secret policy is unclear.

## 7. Acceptance Decision

Go only when:

- preflight has no `failed` checks;
- deployment command finishes;
- `data/readiness.json` exists;
- server verification status is `passed`;
- PostgreSQL production verification status is `passed` when database-backed
  production is required;
- `/console` opens on the target machine or domain;
- Settings can show owner-token, secret policy, path scope, and readiness;
- PostgreSQL evidence is present when production database mode is required;
- the operator has exported Events diagnostics and the trial handoff pack.

No-go when customer data, secrets, external sending, memory promotion,
PostgreSQL migration, backup/restore, diagnostics, or public-brand boundaries
are unverified.
