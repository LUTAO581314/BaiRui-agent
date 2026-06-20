param(
    [string]$OutputPath = "artifacts/commercial-go-no-go.json",
    [string]$ServerVerificationPath = "artifacts/server-deployment-verification.json",
    [string]$PostgresVerificationPath = "artifacts/postgres-production-verification.json",
    [string]$DeploymentChecklistPath = "artifacts/deployment-checklist.json",
    [string]$DeploymentChecklistMarkdownPath = "artifacts/deployment-checklist.md",
    [string]$DeliveryStatusPath = "artifacts/delivery-status.json",
    [string]$WeComTrialPath = "artifacts/wecom-trial.json",
    [string]$WeComReceiptPath = "artifacts/wecom-receipt.json",
    [switch]$RequireServerEvidence,
    [switch]$RequirePostgresEvidence,
    [switch]$RequireWeComTrial,
    [switch]$SkipAcceptance,
    [switch]$SummaryOnly
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

$deploymentChecklist = Invoke-JsonCommand "deployment checklist" { python -m src.hermes deployment-checklist }
$evidence["deployment_checklist"] = $deploymentChecklist.payload
if ($deploymentChecklist.payload) {
    $checklistParent = Split-Path -Parent $DeploymentChecklistPath
    if ($checklistParent) {
        New-Item -ItemType Directory -Force -Path $checklistParent | Out-Null
    }
    $deploymentChecklist.payload | ConvertTo-Json -Depth 40 | Set-Content -LiteralPath $DeploymentChecklistPath -Encoding UTF8
    $markdown = $deploymentChecklist.payload.deployment_checklist.markdown
    if ($markdown) {
        $markdownParent = Split-Path -Parent $DeploymentChecklistMarkdownPath
        if ($markdownParent) {
            New-Item -ItemType Directory -Force -Path $markdownParent | Out-Null
        }
        $markdown | Set-Content -LiteralPath $DeploymentChecklistMarkdownPath -Encoding UTF8
    }
}
if ($deploymentChecklist.ok -and $deploymentChecklist.payload.deployment_checklist.status -ne "blocked") {
    $checks += New-Check "deployment_checklist" "Deployment checklist" "passed" "checklist=$DeploymentChecklistPath; markdown=$DeploymentChecklistMarkdownPath; status=$($deploymentChecklist.payload.deployment_checklist.status)" "Attach the checklist to the operator handoff."
}
else {
    $detail = if ($deploymentChecklist.error) { $deploymentChecklist.error } elseif ($deploymentChecklist.payload) { "status=$($deploymentChecklist.payload.deployment_checklist.status); missing_required=$($deploymentChecklist.payload.deployment_checklist.missing_required -join ',')" } else { "deployment checklist evidence missing" }
    $checks += New-Check "deployment_checklist" "Deployment checklist" "blocked" $detail "Fill required activation/configuration values, then rerun deployment-checklist."
}

$modelProbe = Invoke-JsonCommand "model gateway probe" { python -m src.hermes model-gateway probe }
$evidence["model_gateway_probe"] = $modelProbe.payload
$modelProbePayload = if ($modelProbe.payload) { $modelProbe.payload.model_gateway_probe } else { $null }
if ($modelProbe.ok -and $modelProbePayload.status -eq "ready" -and $modelProbePayload.chat_status -eq "completed" -and $modelProbePayload.secret_echo -eq $false) {
    $checks += New-Check "model_gateway_probe" "Model gateway chat probe" "passed" "model=$($modelProbePayload.model); base_url=$($modelProbePayload.base_url); chat_status=$($modelProbePayload.chat_status)" "Keep this probe evidence with activation and handoff outputs."
}
else {
    $detail = if ($modelProbe.error) { $modelProbe.error } elseif ($modelProbePayload) { "status=$($modelProbePayload.status); chat_status=$($modelProbePayload.chat_status); error=$($modelProbePayload.error)" } else { "model gateway probe evidence missing" }
    $checks += New-Check "model_gateway_probe" "Model gateway chat probe" "blocked" $detail "Configure model gateway and run python -m src.hermes model-gateway probe until it returns ready."
}

$deliveryStatus = Invoke-JsonCommand "delivery status" { python -m src.hermes delivery-status }
$evidence["delivery_status"] = $deliveryStatus.payload
if ($deliveryStatus.payload) {
    $deliveryParent = Split-Path -Parent $DeliveryStatusPath
    if ($deliveryParent) {
        New-Item -ItemType Directory -Force -Path $deliveryParent | Out-Null
    }
    $deliveryStatus.payload | ConvertTo-Json -Depth 40 | Set-Content -LiteralPath $DeliveryStatusPath -Encoding UTF8
}
$deliveryPayload = if ($deliveryStatus.payload) { $deliveryStatus.payload.delivery_status } else { $null }
if ($deliveryStatus.ok -and $deliveryPayload.status -eq "ready") {
    $checks += New-Check "delivery_status" "Commercial delivery status" "passed" "delivery-status=$DeliveryStatusPath; status=ready" "Keep this delivery status with the handoff evidence."
}
else {
    $detail = if ($deliveryStatus.error) { $deliveryStatus.error } elseif ($deliveryPayload) { "status=$($deliveryPayload.status); blockers=$($deliveryPayload.blockers -join ',')" } else { "delivery status evidence missing" }
    $checks += New-Check "delivery_status" "Commercial delivery status" "blocked" $detail "Resolve delivery blockers, then rerun delivery-status."
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
    "web/bairui-console/app-shell.js",
    "web/bairui-console/chat.js",
    "web/bairui-console/api-client.js",
    "web/bairui-console/person-card.js",
    "web/bairui-console/wechat-popup.js",
    "web/bairui-console/acui/bootstrap.js",
    "web/bairui-console/styles.css"
)
$frontendText = ($frontendFiles | ForEach-Object { Get-Content -LiteralPath $_ -Raw }) -join "`n"
$requiredFrontend = @(
    "renderBrainUiApp",
    "initChat",
    "ownerAuthHeaders",
    "X-Bairui-Owner-Token",
    "buildBairuiGraphRows",
    "/document/memory-candidates",
    "/reports",
    "/source-refs",
    "/audit",
    "long_term_memory_auto_write: false",
    "external_send_performed: false",
    "ENTITY_CARD_KIND",
    "bairui Agent",
    "BAIRUI_ENABLE_ACUI_WS"
)
$missingFrontend = @($requiredFrontend | Where-Object { $frontendText -notmatch [regex]::Escape($_) })
if ($missingFrontend.Count -eq 0) {
    $checks += New-Check "frontend_closure" "Frontend commercial closure" "passed" "bairui console shell, chat bridge, memory graph, entity card, channel approval boundary, owner token, and ACUI safety gate are present" "Do visual QA on the target browser before customer use."
}
else {
    $checks += New-Check "frontend_closure" "Frontend commercial closure" "failed" "missing UI hooks: $($missingFrontend -join ', ')" "Restore required bairui frontend closure hooks."
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

$wecomTrial = Invoke-JsonCommand "Enterprise group bot trial" { python -m src.hermes channels wecom-trial --text "bairui commercial go/no-go channel trial" --approve }
$evidence["wecom_trial"] = $wecomTrial.payload
if ($wecomTrial.payload) {
    $wecomParent = Split-Path -Parent $WeComTrialPath
    if ($wecomParent) {
        New-Item -ItemType Directory -Force -Path $wecomParent | Out-Null
    }
    $wecomTrial.payload | ConvertTo-Json -Depth 40 | Set-Content -LiteralPath $WeComTrialPath -Encoding UTF8
}
$wecomReview = if ($wecomTrial.payload) { $wecomTrial.payload.wecom_trial.review } else { $null }
$wecomEvidence = if ($wecomReview) { $wecomReview.delivery_evidence } else { $null }
$wecomReceiptSource = if ($wecomEvidence) { [string]$wecomEvidence.receipt_path } else { "" }
$wecomReceipt = $null
if (-not [string]::IsNullOrWhiteSpace($wecomReceiptSource) -and (Test-Path -LiteralPath $wecomReceiptSource)) {
    $wecomReceipt = Read-OptionalJson $wecomReceiptSource
    $receiptParent = Split-Path -Parent $WeComReceiptPath
    if ($receiptParent) {
        New-Item -ItemType Directory -Force -Path $receiptParent | Out-Null
    }
    Copy-Item -LiteralPath $wecomReceiptSource -Destination $WeComReceiptPath -Force
}
$evidence["wecom_receipt"] = $wecomReceipt
$wecomPassed = $wecomTrial.ok `
    -and $wecomTrial.payload.wecom_trial.status -eq "reviewed" `
    -and $wecomReview.will_send -eq $true `
    -and $wecomReview.delivery_status -eq "sent" `
    -and -not [string]::IsNullOrWhiteSpace([string]$wecomReview.external_message_id) `
    -and $wecomEvidence `
    -and $wecomEvidence.secret_echo -eq $false `
    -and $wecomReceipt `
    -and $wecomReceipt.secret_echo -eq $false `
    -and $wecomReceipt.delivery_status -eq "sent" `
    -and -not [string]::IsNullOrWhiteSpace([string]$wecomReceipt.external_message_id)
if ($wecomPassed) {
    $checks += New-Check "wecom_trial" "Enterprise group bot channel trial" "passed" "enterprise-group trial dispatched and recorded receipt: external_message_id=$($wecomReview.external_message_id); receipt=$WeComReceiptPath" "Verify the enterprise group received the message and keep the receipt with the handoff package."
}
elseif ($RequireWeComTrial) {
    $detail = if ($wecomTrial.error) { $wecomTrial.error } elseif ($wecomTrial.payload) { "status=$($wecomTrial.payload.wecom_trial.status); next=$($wecomTrial.payload.wecom_trial.next_step)" } else { "wecom trial evidence missing" }
    $checks += New-Check "wecom_trial" "Enterprise group bot channel trial" "failed" $detail "Configure the enterprise group Bot Key, rerun channels wecom-trial --approve, and confirm the external group receipt."
}
else {
    $detail = if ($wecomTrial.payload) { "status=$($wecomTrial.payload.wecom_trial.status); next=$($wecomTrial.payload.wecom_trial.next_step)" } else { "not required for local dry-run" }
    $checks += New-Check "wecom_trial" "Enterprise group bot channel trial" "blocked" $detail "Use -RequireWeComTrial for real customer Go/No-Go after the enterprise group Bot Key is configured."
}

$documentMemoryTrial = Invoke-JsonCommand "Document memory trial" { python -m src.hermes document parse memory-trial --text "bairui commercial go/no-go document memory trial verifies ingest, review, graph sync, report, and source references." }
$evidence["document_memory_trial"] = $documentMemoryTrial.payload
if ($documentMemoryTrial.ok -and $documentMemoryTrial.payload.document_memory_trial.status -eq "completed") {
    $trialEvidence = $documentMemoryTrial.payload.document_memory_trial.evidence
    $checks += New-Check "document_memory_trial" "Document memory closure trial" "passed" "current_stage=$($trialEvidence.current_stage); candidates=$($trialEvidence.candidate_count); reviews=$($trialEvidence.review_count); source_refs=$($trialEvidence.source_ref_count); reports=$($trialEvidence.report_count)" "Keep the generated report and source references with the handoff evidence."
}
else {
    $detail = if ($documentMemoryTrial.error) { $documentMemoryTrial.error } elseif ($documentMemoryTrial.payload) { "status=$($documentMemoryTrial.payload.document_memory_trial.status); next=$($documentMemoryTrial.payload.document_memory_trial.next_step)" } else { "document memory trial evidence missing" }
    $checks += New-Check "document_memory_trial" "Document memory closure trial" "failed" $detail "Run python -m src.hermes document parse memory-trial and fix document ingestion, memory review, graph sync, report, or source reference blockers."
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
if ($SummaryOnly) {
    $summary = [pscustomobject]@{
        service = $report.service
        mode = $report.mode
        status = $report.status
        output_path = $OutputPath
        checks = @($checks | ForEach-Object { [pscustomobject]@{ id = $_.id; status = $_.status; evidence = $_.evidence } })
        decision = $report.decision
    }
    $summary | ConvertTo-Json -Depth 20
}
else {
    $json
}

if ($status -eq "no_go") {
    throw "bairui commercial Go/No-Go failed"
}
