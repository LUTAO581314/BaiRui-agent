param(
    [string]$OutputPath = "artifacts/postgres-production-verification.json",
    [string]$FailureSummaryPath = "artifacts/postgres-production-failure-summary.md",
    [string]$SampleBackupPath = "data/backups/postgres/sample-verification.dump",
    [switch]$RunMigration,
    [switch]$RequireDatabase
)

$ErrorActionPreference = "Stop"

function New-Check {
    param(
        [string]$Id,
        [string]$Name,
        [string]$Status,
        [string]$Evidence,
        [string]$NextStep
    )
    [pscustomobject]@{
        id = $Id
        name = $Name
        status = $Status
        evidence = $Evidence
        next_step = $NextStep
    }
}

function Invoke-HermesJson {
    param([string[]]$CliArgs)
    $output = & python -m src.hermes @CliArgs 2>&1 | Out-String
    $code = $LASTEXITCODE
    $payload = $null
    try {
        $payload = $output | ConvertFrom-Json
    }
    catch {
        return [pscustomobject]@{
            exit_code = $code
            ok = $false
            payload = $null
            error = "non-json output: $($output.Trim())"
        }
    }
    return [pscustomobject]@{
        exit_code = $code
        ok = $code -eq 0
        payload = $payload
        error = ""
    }
}

function Test-SecretSafe {
    param([string]$Text)
    if ($Text -match "postgresql://[^`"'\s]+:[^`"'\s]+@") {
        return $false
    }
    if ($Text -match "password|secret|token") {
        return $Text -match 'never printed|never returned|configured or missing|HERMES_DATABASE_URL|\$HERMES_DATABASE_URL'
    }
    return $true
}

function Select-EvidenceSummary {
    param(
        [object]$Payload,
        [string]$Kind
    )
    if ($null -eq $Payload) {
        return $null
    }
    if ($Kind -eq "migration") {
        return [ordered]@{
            status = $Payload.database.status
            detail = $Payload.database.detail
        }
    }
    if ($Kind -eq "backup_status") {
        return [ordered]@{
            status = $Payload.backup.status
            detail = $Payload.backup.detail
            backup_dir = $Payload.backup.backup_dir
            latest_backup = $Payload.backup.latest_backup
            restore_requires_confirmation = $Payload.backup.restore_requires_confirmation
        }
    }
    if ($Kind -eq "backup_plan") {
        return [ordered]@{
            status = $Payload.backup_plan.status
            database = $Payload.backup_plan.database
            backup_dir = $Payload.backup_plan.backup_dir
            command = $Payload.backup_plan.command
            secret_policy = $Payload.backup_plan.secret_policy
            creates_customer_data = $Payload.backup_plan.creates_customer_data
        }
    }
    if ($Kind -eq "restore_plan") {
        return [ordered]@{
            status = $Payload.restore_plan.status
            database = $Payload.restore_plan.database
            command = $Payload.restore_plan.command
            confirmation_phrase = $Payload.restore_plan.confirmation_phrase
            confirmed = $Payload.restore_plan.confirmed
            blockers = $Payload.restore_plan.blockers
            destructive = $Payload.restore_plan.destructive
            secret_policy = $Payload.restore_plan.secret_policy
        }
    }
    if ($Kind -eq "config_status") {
        return [ordered]@{
            status = $Payload.config_status.status
            database = ($Payload.config_status.items | Where-Object { $_.id -eq "database" } | Select-Object -First 1)
            secret_policy = $Payload.config_status.secret_policy
        }
    }
    return $Payload
}

function Write-FailureSummary {
    param(
        [object]$Report,
        [string]$Path
    )
    $actionable = @($Report.checks | Where-Object { @("failed", "blocked") -contains $_.status })
    $lines = @()
    $lines += "# bairui PostgreSQL Production Failure Summary"
    $lines += ""
    $lines += "- status: $($Report.status)"
    $lines += "- require_database: $($Report.require_database)"
    $lines += "- run_migration: $($Report.run_migration)"
    $lines += "- generated_at: $($Report.generated_at)"
    $lines += ""
    if ($actionable.Count -eq 0) {
        $lines += "No failed or blocked PostgreSQL checks were recorded."
    }
    else {
        $lines += "| Check | Status | Evidence | Next step |"
        $lines += "| --- | --- | --- | --- |"
        foreach ($check in $actionable) {
            $lines += "| $($check.id) | $($check.status) | $($check.evidence) | $($check.next_step) |"
        }
    }
    $parent = Split-Path -Parent $Path
    if ($parent) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    $lines -join "`n" | Set-Content -LiteralPath $Path -Encoding UTF8
}

$checks = @()
$evidence = [ordered]@{}

$schema = Get-Content -LiteralPath "src/hermes/db.py" -Raw
$schemaRequirements = [ordered]@{
    jobs = "create table if not exists jobs"
    audit_logs = "create table if not exists audit_logs"
    source_refs = "create table if not exists source_refs"
    agent_sessions = "create table if not exists agent_sessions"
    agent_events = "create table if not exists agent_events"
    codegraph_repos = "create table if not exists codegraph_repos"
    codegraph_files = "create table if not exists codegraph_files"
    codegraph_symbols = "create table if not exists codegraph_symbols"
}

$missingSchema = @()
foreach ($key in $schemaRequirements.Keys) {
    if ($schema -notmatch [regex]::Escape($schemaRequirements[$key])) {
        $missingSchema += $key
    }
}
if ($missingSchema.Count -eq 0) {
    $checks += New-Check "schema_core_tables" "Core production schema coverage" "passed" "jobs, audit_logs, source_refs, agent sessions, and CodeGraph tables are present" "Run migration on the target PostgreSQL instance."
}
else {
    $checks += New-Check "schema_core_tables" "Core production schema coverage" "failed" "missing: $($missingSchema -join ', ')" "Add migrations for missing commercial product state before production."
}

if ($RunMigration) {
    $migrationResult = Invoke-HermesJson -CliArgs @("migrate")
    $evidence["migration"] = Select-EvidenceSummary $migrationResult.payload "migration"
    if ($migrationResult.ok) {
        $checks += New-Check "migration" "PostgreSQL migration command" "passed" "migration command returned ready" "Record this output in the database production proof."
    }
    else {
        $checks += New-Check "migration" "PostgreSQL migration command" "failed" "exit=$($migrationResult.exit_code); $($migrationResult.error)" "Configure HERMES_DATABASE_URL and PostgreSQL access, then rerun migration."
    }
}
elseif ($RequireDatabase) {
    $checks += New-Check "migration" "PostgreSQL migration command" "blocked" "real migration was not run" "Rerun with -RunMigration on the target PostgreSQL server."
}
else {
    $checks += New-Check "migration" "PostgreSQL migration command" "blocked" "dry-run mode; migration command not executed" "Use -RunMigration -RequireDatabase on a real server."
}

$backupStatus = Invoke-HermesJson -CliArgs @("backup", "status")
$evidence["backup_status"] = Select-EvidenceSummary $backupStatus.payload "backup_status"
if ($backupStatus.ok) {
    $checks += New-Check "backup_status" "Backup readiness status" "passed" "backup status command returned acceptable state" "Continue to backup plan validation."
}
elseif ($RequireDatabase) {
    $checks += New-Check "backup_status" "Backup readiness status" "failed" "exit=$($backupStatus.exit_code); $($backupStatus.error)" "Configure HERMES_DATABASE_URL before production backup validation."
}
else {
    $checks += New-Check "backup_status" "Backup readiness status" "blocked" "backup status requires configured PostgreSQL for production proof" "Use -RequireDatabase on a real server."
}

$backupPlan = Invoke-HermesJson -CliArgs @("backup", "plan")
$evidence["backup_plan"] = Select-EvidenceSummary $backupPlan.payload "backup_plan"
$backupText = $backupPlan.payload | ConvertTo-Json -Depth 20
if ($backupPlan.ok -and $backupText -match "pg_dump" -and $backupText -match '\$HERMES_DATABASE_URL' -and (Test-SecretSafe $backupText)) {
    $checks += New-Check "backup_plan" "Secret-safe backup plan" "passed" "pg_dump plan uses `$HERMES_DATABASE_URL without printing the database URL" "Run the command during the server backup validation window."
}
elseif ($RequireDatabase) {
    $checks += New-Check "backup_plan" "Secret-safe backup plan" "failed" "backup plan unavailable or secret policy failed" "Fix backup planning before production handoff."
}
else {
    $checks += New-Check "backup_plan" "Secret-safe backup plan" "blocked" "backup plan requires configured PostgreSQL for production proof" "Use -RequireDatabase on a real server."
}

$sampleBackup = [System.IO.Path]::GetFullPath($SampleBackupPath)
$sampleParent = Split-Path -Parent $sampleBackup
if ($sampleParent) {
    New-Item -ItemType Directory -Force -Path $sampleParent | Out-Null
}
"verification only" | Set-Content -LiteralPath $sampleBackup -Encoding UTF8

try {
    $blockedRestore = Invoke-HermesJson -CliArgs @("backup", "restore-plan", "--backup-path", $sampleBackup)
    $readyRestore = Invoke-HermesJson -CliArgs @("backup", "restore-plan", "--backup-path", $sampleBackup, "--confirm-restore", "RESTORE BAIRUI POSTGRES")
    $evidence["restore_plan_blocked"] = Select-EvidenceSummary $blockedRestore.payload "restore_plan"
    $evidence["restore_plan_confirmed"] = Select-EvidenceSummary $readyRestore.payload "restore_plan"

    $blockedText = $blockedRestore.payload | ConvertTo-Json -Depth 20
    $readyText = $readyRestore.payload | ConvertTo-Json -Depth 20
    $blockedOk = $blockedText -match "RESTORE BAIRUI POSTGRES" -and $blockedText -match "blocked"
    $readyOk = $readyText -match "pg_restore" -and $readyText -match '\$HERMES_DATABASE_URL' -and $readyText -match '"destructive":\s*true'
    $secretOk = (Test-SecretSafe $blockedText) -and (Test-SecretSafe $readyText)

    if ($blockedOk -and $readyOk -and $secretOk) {
        $checks += New-Check "restore_guardrail" "Restore guardrail and confirmation" "passed" "restore is blocked without typed confirmation and uses pg_restore with `$HERMES_DATABASE_URL" "Run restore only on a disposable test database before production use."
    }
    else {
        $checks += New-Check "restore_guardrail" "Restore guardrail and confirmation" "failed" "restore plan did not prove confirmation, destructive flag, or secret policy" "Fix restore guardrails before production handoff."
    }
}
finally {
    Remove-Item -LiteralPath $sampleBackup -Force -ErrorAction SilentlyContinue
}

$settingsEvidence = Invoke-HermesJson -CliArgs @("config-status")
$evidence["config_status"] = Select-EvidenceSummary $settingsEvidence.payload "config_status"
$settingsText = $settingsEvidence.payload | ConvertTo-Json -Depth 20
if ($settingsText -match '"database"' -and $settingsText -match "never returned|configured or missing|secret") {
    $checks += New-Check "settings_database_visibility" "Settings database visibility" "passed" "Settings diagnostics expose database state without returning secrets" "Confirm the same state is visible in Settings on the target server."
}
else {
    $checks += New-Check "settings_database_visibility" "Settings database visibility" "failed" "database state or secret policy missing from config status" "Fix Settings database diagnostics before trial handoff."
}

$serializedEvidence = $evidence | ConvertTo-Json -Depth 30
if (Test-SecretSafe $serializedEvidence) {
    $checks += New-Check "secret_redaction" "Database secret redaction" "passed" "database URL/password were not printed in verification evidence" "Keep raw database credentials only in protected environment files."
}
else {
    $checks += New-Check "secret_redaction" "Database secret redaction" "failed" "verification evidence appears to contain raw database credentials" "Remove secret output before customer handoff."
}

$blockingStatuses = @("failed")
if ($RequireDatabase) {
    $blockingStatuses += "blocked"
}
$blocked = @($checks | Where-Object { $blockingStatuses -contains $_.status })
$overall = $(if ($blocked.Count -eq 0) { "passed" } else { "failed" })

$report = [pscustomobject]@{
    service = "bairui"
    mode = "postgres_production_verification"
    status = $overall
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    require_database = [bool]$RequireDatabase
    run_migration = [bool]$RunMigration
    failure_summary_path = $FailureSummaryPath
    checks = $checks
    evidence = $evidence
}

$parent = Split-Path -Parent $OutputPath
if ($parent) {
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
}
$json = $report | ConvertTo-Json -Depth 40
$json | Set-Content -LiteralPath $OutputPath -Encoding UTF8
Write-FailureSummary -Report $report -Path $FailureSummaryPath
$json

if ($overall -ne "passed") {
    throw "bairui PostgreSQL production verification failed"
}
