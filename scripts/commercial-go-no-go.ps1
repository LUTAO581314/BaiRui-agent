param(
    [string]$OutputPath = "artifacts/commercial-go-no-go.json",
    [string]$ServerVerificationPath = "artifacts/server-deployment-verification.json",
    [string]$PostgresVerificationPath = "artifacts/postgres-production-verification.json",
    [switch]$RequireServerEvidence,
    [switch]$RequirePostgresEvidence,
    [switch]$SkipAcceptance
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

function Invoke-JsonCommand {
    param(
        [string]$Label,
        [scriptblock]$Command
    )
    try {
        $raw = & $Command | Out-String
        return [pscustomobject]@{
            ok = $true
            raw = $raw
            payload = ($raw | ConvertFrom-Json)
            error = ""
        }
    }
    catch {
        return [pscustomobject]@{
            ok = $false
            raw = ""
            payload = $null
            error = "$Label failed: $($_.Exception.Message)"
        }
    }
}

function Invoke-StatusCommand {
    param(
        [string]$Label,
        [scriptblock]$Command
    )
    try {
        $raw = & $Command 2>&1 | Out-String
        return [pscustomobject]@{
            ok = $true
            raw = $raw
            error = ""
        }
    }
    catch {
        return [pscustomobject]@{
            ok = $false
            raw = ""
            error = "$Label failed: $($_.Exception.Message)"
        }
    }
}

function Read-OptionalJson {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        return $null
    }
    try {
        return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
    }
    catch {
        return [pscustomobject]@{ status = "failed"; error = $_.Exception.Message }
    }
}

$checks = @()
$evidence = [ordered]@{}

$head = (git rev-parse --short HEAD 2>$null | Out-String).Trim()
if ($head) {
    $checks += New-Check "git_commit" "Git commit recorded" "passed" "HEAD=$head" "Use this commit in the customer handoff notes."
}
else {
    $checks += New-Check "git_commit" "Git commit recorded" "failed" "git HEAD unavailable" "Run from a Git checkout before commercial trial."
}

$brand = Invoke-StatusCommand "public brand scan" { .\scripts\check-public-brand.ps1 }
if ($brand.ok) {
    $checks += New-Check "public_brand" "Public brand boundary" "passed" "check-public-brand.ps1 passed" "Keep customer-facing UI limited to bairui."
}
else {
    $checks += New-Check "public_brand" "Public brand boundary" "failed" $brand.error "Remove non-bairui public brand exposure before trial."
}

$hygiene = Invoke-StatusCommand "repository hygiene" { .\scripts\check-repo-hygiene.ps1 }
if ($hygiene.ok) {
    $checks += New-Check "repo_hygiene" "Repository hygiene" "passed" "check-repo-hygiene.ps1 passed" "Keep secrets, runtime data, logs, and generated media out of Git."
}
else {
    $checks += New-Check "repo_hygiene" "Repository hygiene" "failed" $hygiene.error "Fix repository hygiene before trial."
}

$deployAssets = Invoke-StatusCommand "deployment assets" { .\scripts\check-deploy-assets.ps1 }
if ($deployAssets.ok) {
    $checks += New-Check "deploy_assets" "Deployment assets" "passed" "deployment scripts and templates are present" "Use preflight, deploy, verifier, and database proof on the target server."
}
else {
    $detail = if ($deployAssets.error) { $deployAssets.error } else { "deployment asset check did not return ok" }
    $checks += New-Check "deploy_assets" "Deployment assets" "failed" $detail "Restore missing deployment assets before trial."
}

if (-not $SkipAcceptance) {
    $acceptance = Invoke-JsonCommand "product acceptance" { .\scripts\product-acceptance.ps1 }
    $evidence["product_acceptance"] = $acceptance.payload
    if ($acceptance.ok -and $acceptance.payload.status -eq "passed") {
        $checks += New-Check "product_acceptance" "Product demo acceptance" "passed" "Command, Documents, Memory Review, Reports, Channels, CodeGraph, Settings, and owner gate passed local acceptance" "Attach the acceptance output to the trial handoff pack."
    }
    else {
        $detail = if ($acceptance.error) { $acceptance.error } else { "product acceptance did not pass" }
        $checks += New-Check "product_acceptance" "Product demo acceptance" "failed" $detail "Fix local product acceptance before any customer trial."
    }
}
else {
    $checks += New-Check "product_acceptance" "Product demo acceptance" "blocked" "skipped by operator" "Run without -SkipAcceptance before Go decision."
}

$frontendFiles = @(
    "web/bairui-console/app.js",
    "web/bairui-console/styles.css"
)
$frontendText = ($frontendFiles | ForEach-Object { Get-Content -LiteralPath $_ -Raw }) -join "`n"
$requiredFrontend = @(
    "renderCommercialTrialFlow",
    "Documents -> Memory Review -> Reports -> Channels -> Events",
    "renderActivationModeSelector",
    "renderSettingsSecurityAcceptance",
    "renderHandoffPackSummary",
    "will_send=false",
    "long_term_memory_auto_write: false"
)
$missingFrontend = @($requiredFrontend | Where-Object { $frontendText -notmatch [regex]::Escape($_) })
if ($missingFrontend.Count -eq 0) {
    $checks += New-Check "frontend_closure" "Frontend commercial closure" "passed" "activation mode, security acceptance, trial flow, no-send, memory review, and handoff UI hooks are present" "Do visual QA on the target browser before customer use."
}
else {
    $checks += New-Check "frontend_closure" "Frontend commercial closure" "failed" "missing UI hooks: $($missingFrontend -join ', ')" "Restore required frontend commercial closure hooks."
}

$serverEvidence = Read-OptionalJson $ServerVerificationPath
$evidence["server_deployment"] = $serverEvidence
if ($serverEvidence -and $serverEvidence.status -eq "passed") {
    $checks += New-Check "server_verification" "Server deployment verification" "passed" "server verification report passed: $ServerVerificationPath" "Keep this report with the handoff package."
}
elseif ($RequireServerEvidence) {
    $detail = if ($serverEvidence) { "status=$($serverEvidence.status)" } else { "missing: $ServerVerificationPath" }
    $checks += New-Check "server_verification" "Server deployment verification" "failed" $detail "Run verify-server-deployment.ps1 on the target server."
}
else {
    $checks += New-Check "server_verification" "Server deployment verification" "blocked" "not required for local dry-run; evidence missing or not passed" "Use -RequireServerEvidence for real customer Go/No-Go."
}

$postgresEvidence = Read-OptionalJson $PostgresVerificationPath
$evidence["postgres_production"] = $postgresEvidence
if ($postgresEvidence -and $postgresEvidence.status -eq "passed" -and $postgresEvidence.require_database -eq $true) {
    $checks += New-Check "postgres_verification" "PostgreSQL production verification" "passed" "database production proof passed with RequireDatabase" "Keep backup and restore evidence with the handoff package."
}
elseif ($RequirePostgresEvidence) {
    $detail = if ($postgresEvidence) { "status=$($postgresEvidence.status); require_database=$($postgresEvidence.require_database)" } else { "missing: $PostgresVerificationPath" }
    $checks += New-Check "postgres_verification" "PostgreSQL production verification" "failed" $detail "Run verify-postgres-production.ps1 -RequireDatabase -RunMigration on the target server."
}
else {
    $checks += New-Check "postgres_verification" "PostgreSQL production verification" "blocked" "not required for local dry-run; production database evidence missing or dry-run only" "Use -RequirePostgresEvidence for real customer Go/No-Go."
}

$docs = @(
    "docs/29-commercial-trial-handoff-pack.md",
    "docs/30-server-deployment-acceptance-report.md",
    "docs/31-postgresql-production-verification.md"
)
$missingDocs = @($docs | Where-Object { -not (Test-Path -LiteralPath $_) })
if ($missingDocs.Count -eq 0) {
    $checks += New-Check "handoff_docs" "Commercial handoff documents" "passed" "handoff, server acceptance, and PostgreSQL verification docs are present" "Use these documents as the operator checklist."
}
else {
    $checks += New-Check "handoff_docs" "Commercial handoff documents" "failed" "missing: $($missingDocs -join ', ')" "Restore missing handoff documents."
}

$failed = @($checks | Where-Object { $_.status -eq "failed" })
$blocked = @($checks | Where-Object { $_.status -eq "blocked" })
$status = if ($failed.Count) { "no_go" } elseif ($blocked.Count) { "blocked" } else { "go" }

$report = [pscustomobject]@{
    service = "bairui"
    mode = "commercial_go_no_go"
    status = $status
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    git_commit = $head
    require_server_evidence = [bool]$RequireServerEvidence
    require_postgres_evidence = [bool]$RequirePostgresEvidence
    checks = $checks
    evidence = $evidence
    decision = [pscustomobject]@{
        go = $status -eq "go"
        failed_count = $failed.Count
        blocked_count = $blocked.Count
        next_step = if ($status -eq "go") { "Customer trial can proceed with the attached evidence." } elseif ($failed.Count) { "Fix failed checks before trial." } else { "Collect blocked target-server evidence before real customer trial." }
    }
}

$parent = Split-Path -Parent $OutputPath
if ($parent) {
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
}
$json = $report | ConvertTo-Json -Depth 40
$json | Set-Content -LiteralPath $OutputPath -Encoding UTF8
$json

if ($status -eq "no_go") {
    throw "bairui commercial Go/No-Go failed"
}
