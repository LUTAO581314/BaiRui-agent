param(
    [ValidateSet("local", "domain")]
    [string]$Mode = "local",
    [string]$Domain = "",
    [string]$BaseUrl = "http://127.0.0.1:8787",
    [string]$OutputPath = "artifacts/server-trial-acceptance.json",
    [string]$FailureSummaryPath = "artifacts/server-trial-failure-summary.md",
    [string]$ReadinessFile = "data/readiness.json",
    [switch]$SkipDeploy,
    [switch]$SkipServerVerification,
    [switch]$SkipPostgres,
    [switch]$RequireDocker,
    [switch]$RequireEnv,
    [switch]$RequirePostgres,
    [switch]$IncludeDocs
)

$ErrorActionPreference = "Stop"

function New-Step {
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

function Invoke-AcceptanceStep {
    param(
        [string]$Id,
        [string]$Name,
        [scriptblock]$Command,
        [string]$EvidencePath,
        [string]$NextStep,
        [switch]$AllowBlocked
    )
    try {
        $raw = & $Command 2>&1 | Out-String
        $payload = $null
        if ($EvidencePath -and (Test-Path -LiteralPath $EvidencePath)) {
            try {
                $payload = Get-Content -LiteralPath $EvidencePath -Raw | ConvertFrom-Json
            }
            catch {
                $payload = [pscustomobject]@{ status = "failed"; error = $_.Exception.Message }
            }
        }
        $status = if ($payload -and $payload.status) { [string]$payload.status } else { "passed" }
        if ($status -eq "blocked" -and -not $AllowBlocked) {
            $status = "failed"
        }
        return [pscustomobject]@{
            step = New-Step $Id $Name $status $EvidencePath $NextStep
            raw = $raw
            payload = $payload
        }
    }
    catch {
        return [pscustomobject]@{
            step = New-Step $Id $Name "failed" $_.Exception.Message $NextStep
            raw = ""
            payload = $null
        }
    }
}

function Invoke-SkippedStep {
    param(
        [string]$Id,
        [string]$Name,
        [string]$Evidence,
        [string]$NextStep
    )
    return [pscustomobject]@{
        step = New-Step $Id $Name "skipped" $Evidence $NextStep
        raw = ""
        payload = $null
    }
}

function Write-FailureSummary {
    param(
        [object]$Report,
        [string]$Path
    )
    $actionable = @($Report.steps | Where-Object { @("failed", "blocked", "skipped") -contains $_.status })
    $lines = @()
    $lines += "# bairui Server Trial Failure Summary"
    $lines += ""
    $lines += "- status: $($Report.status)"
    $lines += "- base_url: $($Report.base_url)"
    $lines += "- deployment_mode: $($Report.deployment_mode)"
    $lines += "- generated_at: $($Report.generated_at)"
    $lines += ""
    if ($actionable.Count -eq 0) {
        $lines += "No failed, blocked, or skipped steps were recorded."
    }
    else {
        $lines += "| Step | Status | Evidence | Next step |"
        $lines += "| --- | --- | --- | --- |"
        foreach ($step in $actionable) {
            $lines += "| $($step.id) | $($step.status) | $($step.evidence) | $($step.next_step) |"
        }
    }
    $parent = Split-Path -Parent $Path
    if ($parent) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    $lines -join "`n" | Set-Content -LiteralPath $Path -Encoding UTF8
}

$steps = @()
$evidence = [ordered]@{}

$preflightArgs = @{
    Mode = $Mode
    OutputPath = "artifacts/server-prereq-check.json"
}
if ($Mode -eq "domain") {
    $preflightArgs["Domain"] = $Domain
}
if ($RequireDocker) { $preflightArgs["RequireDocker"] = $true }
if ($RequireEnv) { $preflightArgs["RequireEnv"] = $true }

$preflight = Invoke-AcceptanceStep `
    -Id "preflight" `
    -Name "Server prerequisite preflight" `
    -Command { & .\scripts\check-server-prereqs.ps1 @preflightArgs } `
    -EvidencePath "artifacts/server-prereq-check.json" `
    -NextStep "Fix failed prerequisite checks before deploying."
$steps += $preflight.step
$evidence["preflight"] = $preflight.payload

if ($SkipDeploy) {
    $deploy = Invoke-SkippedStep "deploy" "Usable deployment" "skipped by operator" "Run deploy-usable.ps1 or deploy-usable.sh on the target server."
}
else {
    $deployArgs = @{
        Mode = $Mode
        HermesLocalUrl = $BaseUrl
        ReadinessFile = $ReadinessFile
    }
    if ($Mode -eq "domain") {
        $deployArgs["Domain"] = $Domain
    }
    $deploy = Invoke-AcceptanceStep `
        -Id "deploy" `
        -Name "Usable deployment" `
        -Command { & .\scripts\deploy-usable.ps1 @deployArgs } `
        -EvidencePath $ReadinessFile `
        -NextStep "Inspect Docker, service logs, ports, reverse proxy, and readiness output."
}
$steps += $deploy.step
$evidence["deploy"] = $deploy.payload

if ($SkipServerVerification) {
    $serverVerify = Invoke-SkippedStep "server_verification" "Post-deployment server verification" "skipped by operator" "Run verify-server-deployment.ps1 against the target server before customer handoff."
}
else {
    $verifyArgs = @{
        BaseUrl = $BaseUrl
        ReadinessFile = $ReadinessFile
        OutputPath = "artifacts/server-deployment-verification.json"
        RequireReady = $true
    }
    if ($RequirePostgres) { $verifyArgs["RequirePostgreSQL"] = $true }
    $serverVerify = Invoke-AcceptanceStep `
        -Id "server_verification" `
        -Name "Post-deployment server verification" `
        -Command { & .\scripts\verify-server-deployment.ps1 @verifyArgs } `
        -EvidencePath "artifacts/server-deployment-verification.json" `
        -NextStep "Fix failed endpoints, console routing, owner gate, config status, or PostgreSQL visibility."
}
$steps += $serverVerify.step
$evidence["server_verification"] = $serverVerify.payload

if ($SkipPostgres) {
    $postgres = Invoke-SkippedStep "postgres_verification" "PostgreSQL production verification" "skipped by operator" "Run verify-postgres-production.ps1 -RequireDatabase -RunMigration on the target database."
}
else {
    $postgresArgs = @{
        OutputPath = "artifacts/postgres-production-verification.json"
    }
    if ($RequirePostgres) {
        $postgresArgs["RequireDatabase"] = $true
        $postgresArgs["RunMigration"] = $true
    }
    $postgres = Invoke-AcceptanceStep `
        -Id "postgres_verification" `
        -Name "PostgreSQL production verification" `
        -Command { & .\scripts\verify-postgres-production.ps1 @postgresArgs } `
        -EvidencePath "artifacts/postgres-production-verification.json" `
        -NextStep "Fix migration, backup, restore guardrail, or database visibility evidence." `
        -AllowBlocked:(!$RequirePostgres)
}
$steps += $postgres.step
$evidence["postgres_verification"] = $postgres.payload

$goArgs = @{
    OutputPath = "artifacts/commercial-go-no-go.json"
}
if (-not $SkipDeploy -and -not $SkipServerVerification) { $goArgs["RequireServerEvidence"] = $true }
if ($RequirePostgres -and -not $SkipPostgres) { $goArgs["RequirePostgresEvidence"] = $true }
$goNoGo = Invoke-AcceptanceStep `
    -Id "commercial_go_no_go" `
    -Name "Commercial Go/No-Go" `
    -Command { & .\scripts\commercial-go-no-go.ps1 @goArgs } `
    -EvidencePath "artifacts/commercial-go-no-go.json" `
    -NextStep "Resolve failed or blocked final gate checks before customer handoff." `
    -AllowBlocked:($SkipDeploy -or $SkipServerVerification -or $SkipPostgres -or -not $RequirePostgres)
$steps += $goNoGo.step
$evidence["commercial_go_no_go"] = $goNoGo.payload

$bundleArgs = @{
    OutputDir = "artifacts/commercial-handoff-bundle"
}
if ($IncludeDocs) { $bundleArgs["IncludeDocs"] = $true }
$bundle = Invoke-AcceptanceStep `
    -Id "handoff_bundle" `
    -Name "Commercial handoff bundle" `
    -Command { & .\scripts\export-commercial-handoff-bundle.ps1 @bundleArgs } `
    -EvidencePath "artifacts/commercial-handoff-bundle/manifest.json" `
    -NextStep "Attach the bundle manifest and selected report JSON to the operator handoff."
$steps += $bundle.step
$evidence["handoff_bundle"] = $bundle.payload

$failed = @($steps | Where-Object { $_.status -eq "failed" })
$blocked = @($steps | Where-Object { $_.status -eq "blocked" })
$skipped = @($steps | Where-Object { $_.status -eq "skipped" })
$status = if ($failed.Count) { "failed" } elseif ($blocked.Count -or $skipped.Count) { "blocked" } else { "passed" }

$report = [pscustomobject]@{
    service = "bairui"
    mode = "server_trial_acceptance"
    status = $status
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    deployment_mode = $Mode
    domain = $Domain
    base_url = $BaseUrl.TrimEnd("/")
    readiness_file = $ReadinessFile
    require_postgres = [bool]$RequirePostgres
    skip_deploy = [bool]$SkipDeploy
    skip_server_verification = [bool]$SkipServerVerification
    skip_postgres = [bool]$SkipPostgres
    failure_summary_path = $FailureSummaryPath
    steps = $steps
    evidence = $evidence
    decision = [pscustomobject]@{
        ready_for_customer_trial = $status -eq "passed"
        failed_count = $failed.Count
        blocked_count = $blocked.Count
        skipped_count = $skipped.Count
        next_step = if ($status -eq "passed") { "Customer trial can proceed with this evidence bundle." } elseif ($failed.Count) { "Fix failed server acceptance steps and rerun." } else { "Run skipped or blocked target-server/database steps before real customer handoff." }
    }
}

$parent = Split-Path -Parent $OutputPath
if ($parent) {
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
}
$json = $report | ConvertTo-Json -Depth 60
$json | Set-Content -LiteralPath $OutputPath -Encoding UTF8
Write-FailureSummary -Report $report -Path $FailureSummaryPath
$json

if ($status -eq "failed") {
    throw "bairui server trial acceptance failed"
}
