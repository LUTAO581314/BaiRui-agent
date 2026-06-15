# bairui PostgreSQL Production Verification

This document is the Step 3 operator proof for PostgreSQL migration, backup,
and restore readiness. It complements the server deployment acceptance report.

## 1. Purpose

The production database is accepted only when the operator can prove:

- migration schema coverage is present;
- migration has run on the target PostgreSQL server;
- core product tables are available;
- backup planning is secret-safe;
- restore planning is destructive and confirmation-gated;
- Settings shows database, migration, backup, and restore guardrails clearly;
- evidence exports do not print the database URL or password.

## 2. Dry-Run Verification

Run this before touching a real database:

```powershell
.\scripts\verify-postgres-production.ps1
```

Expected output:

- `artifacts/postgres-production-verification.json`
- `artifacts/postgres-production-failure-summary.md`
- schema coverage checks;
- backup status and plan checks;
- restore-plan blocked and confirmed checks;
- Settings database visibility check;
- secret redaction check.

In dry-run mode, migration and database-backed backup checks may be `blocked`.
That is acceptable for local rehearsal, but not for production proof.
Use `artifacts/postgres-production-failure-summary.md` to see each failed or
blocked database check with its evidence and next repair action.

## 3. Target PostgreSQL Verification

Run this on the target server after `HERMES_DATABASE_URL` is configured in a
protected environment file:

```powershell
.\scripts\verify-postgres-production.ps1 -RequireDatabase -RunMigration
```

Required evidence:

- migration check is `passed`;
- backup status is `ready` or `not_ready`;
- backup plan contains `pg_dump`;
- backup plan uses `$HERMES_DATABASE_URL`;
- restore plan is blocked without `RESTORE BAIRUI POSTGRES`;
- confirmed restore plan contains `pg_restore`;
- confirmed restore plan is marked `destructive=true`;
- Settings database visibility check is `passed`;
- secret redaction check is `passed`.

If any check is failed or blocked, start from
`artifacts/postgres-production-failure-summary.md` before editing scripts or
configuration.

## 4. Manual Backup Command

The script does not run `pg_dump` automatically. It prints and verifies the
operator-safe plan. Run the generated command only on the server:

```bash
pg_dump --format=custom --no-owner --no-privileges --file "<output.dump>" "$HERMES_DATABASE_URL"
```

After a real backup artifact exists, rerun:

```powershell
python -m src.hermes backup status
python -m src.hermes backup restore-plan --backup-path ./data/backups/postgres/<artifact>.dump
python -m src.hermes backup restore-plan --backup-path ./data/backups/postgres/<artifact>.dump --confirm-restore "RESTORE BAIRUI POSTGRES"
```

## 5. Restore Test Rule

Never test restore against the live customer database first.

Restore proof requires:

1. Create a disposable PostgreSQL test database.
2. Point `HERMES_DATABASE_URL` to the disposable database.
3. Run the confirmed restore plan.
4. Run `python -m src.hermes migrate`.
5. Open Settings and confirm database status.
6. Run Documents -> Memory Review -> Reports -> Channels -> Events demo flow.

## 6. Acceptance

Go only when:

- `artifacts/postgres-production-verification.json` status is `passed` with
  `-RequireDatabase -RunMigration`;
- `artifacts/postgres-production-failure-summary.md` contains no failed or
  blocked database checks;
- a real backup artifact exists in the protected backup path;
- restore has been tested on a disposable database;
- Settings shows database and backup status without secret values;
- diagnostics and Events exports do not contain database credentials.

No-go when any migration, backup, restore, Settings visibility, or secret
redaction check is failed or unverified.
