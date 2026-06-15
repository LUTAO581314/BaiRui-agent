param(
    [string]$BaseUrl = "http://127.0.0.1:8787",
    [string]$ReadinessFile = "data/readiness.json",
    [string]$OutputPath = "artifacts/server-deployment-verification.json",
    [switch]$RequireReady,
    [switch]$RequirePostgreSQL
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

function Invoke-JsonEndpoint {
    param(
        [string]$Path,
        [string]$Method = "GET",
        [object]$Body = $null
    )
    $url = "$($BaseUrl.TrimEnd('/'))$Path"
    try {
        $params = @{
            Uri = $url
            Method = $Method
            TimeoutSec = 20
        }
        if ($null -ne $Body) {
            $params.Body = ($Body | ConvertTo-Json -Depth 10)
            $params.ContentType = "application/json"
        }
        $payload = Invoke-RestMethod @params
        return [pscustomobject]@{
            ok = $true
            url = $url
            body = $payload
            error = ""
        }
    }
    catch {
        return [pscustomobject]@{
            ok = $false
            url = $url
            body = $null
            error = $_.Exception.Message
        }
    }
}

function Get-EndpointStatus {
    param(
        [string]$Name,
        [string]$Path,
        [string]$ExpectedStatus = ""
    )
    $result = Invoke-JsonEndpoint -Path $Path
    if (-not $result.ok) {
        return New-Check "endpoint_$Name" "$Path endpoint" "failed" $result.error "Fix the bairui service, reverse proxy, firewall, or base URL, then rerun this verifier."
    }

    if ($ExpectedStatus) {
        $actual = $result.body.status
        if ($actual -ne $ExpectedStatus) {
            return New-Check "endpoint_$Name" "$Path endpoint" "blocked" "reachable but status=$actual" "Open the endpoint body and fix the listed blockers before customer handoff."
        }
    }

    return New-Check "endpoint_$Name" "$Path endpoint" "passed" "reachable: $($result.url)" "Keep this endpoint in the handoff evidence bundle."
}

$checks = @()
$endpointResults = [ordered]@{}
foreach ($endpoint in @(
    @{ Name = "health"; Path = "/health"; Expected = "ok" },
    @{ Name = "ready"; Path = "/ready"; Expected = "" },
    @{ Name = "runtime_readiness"; Path = "/runtime/readiness"; Expected = "" },
    @{ Name = "frontend_contract"; Path = "/frontend/contract"; Expected = "" },
    @{ Name = "metrics"; Path = "/metrics"; Expected = "" },
    @{ Name = "errors"; Path = "/errors"; Expected = "" }
)) {
    $result = Invoke-JsonEndpoint -Path $endpoint.Path
    $endpointResults[$endpoint.Name] = $result
    $checks += Get-EndpointStatus -Name $endpoint.Name -Path $endpoint.Path -ExpectedStatus $endpoint.Expected
}

$consoleUrl = "$($BaseUrl.TrimEnd('/'))/console"
try {
    $consoleResponse = Invoke-WebRequest -Uri $consoleUrl -TimeoutSec 20 -UseBasicParsing
    if ($consoleResponse.StatusCode -ge 200 -and $consoleResponse.StatusCode -lt 400) {
        $checks += New-Check "console" "/console web console" "passed" "reachable: $consoleUrl" "Capture a screenshot after Activation, Settings, and Events are opened."
    }
    else {
        $checks += New-Check "console" "/console web console" "failed" "HTTP $($consoleResponse.StatusCode)" "Fix static console routing before customer handoff."
    }
}
catch {
    $checks += New-Check "console" "/console web console" "failed" $_.Exception.Message "Fix static console routing, reverse proxy, or base URL."
}

$demoFlow = Invoke-JsonEndpoint -Path "/demo/flow" -Method "POST" -Body @{}
$endpointResults["demo_flow"] = $demoFlow
if ($demoFlow.ok -and @("completed", "partial") -contains $demoFlow.body.demo_flow.status) {
    $safeSend = $demoFlow.body.demo_flow.checkpoints.no_external_send -eq $true
    $safeMemory = $demoFlow.body.demo_flow.checkpoints.no_auto_memory_write -eq $true
    if ($safeSend -and $safeMemory) {
        $demoStatus = $demoFlow.body.demo_flow.status
        if ($RequireReady -and $demoStatus -ne "completed") {
            $checks += New-Check "demo_flow" "Demo Flow safety closure" "blocked" "status=$demoStatus with no_external_send=true and no_auto_memory_write=true" "Resolve the visible partial blockers before final customer handoff."
        }
        else {
            $checks += New-Check "demo_flow" "Demo Flow safety closure" "passed" "status=$demoStatus with no_external_send=true and no_auto_memory_write=true" "Export this result with the server verification report."
        }
    }
    else {
        $checks += New-Check "demo_flow" "Demo Flow safety closure" "failed" "safety checkpoints were not both true" "Do not hand off until external-send and memory-write safety checkpoints pass."
    }
}
else {
    $checks += New-Check "demo_flow" "Demo Flow safety closure" "failed" $demoFlow.error "Run deploy-usable again and inspect Events or server logs."
}

$adminSession = Invoke-JsonEndpoint -Path "/admin/session"
$endpointResults["admin_session"] = $adminSession
if ($adminSession.ok) {
    $session = $adminSession.body.admin_session
    if ($session.secret_policy -match "never returned") {
        $checks += New-Check "owner_gate" "Owner-token admin gate" "passed" "token_configured=$($session.token_configured); authenticated=$($session.authenticated); secret policy present" "Verify the browser can save the owner token locally in Settings."
    }
    else {
        $checks += New-Check "owner_gate" "Owner-token admin gate" "failed" "secret policy missing or unclear" "Fix admin session response before customer handoff."
    }
}
else {
    $checks += New-Check "owner_gate" "Owner-token admin gate" "failed" $adminSession.error "Check /admin/session routing and backend startup."
}

$configStatus = Invoke-JsonEndpoint -Path "/config/status"
$endpointResults["config_status"] = $configStatus
if ($configStatus.ok) {
    $configItems = @($configStatus.body.config_status.items)
    $status = $configStatus.body.config_status.status
    $secretPolicy = $configStatus.body.config_status.secret_policy
    if ($secretPolicy -match "never returned") {
        $checks += New-Check "config_status" "Settings configuration diagnostics" "passed" "status=$status; secret policy present" "Use Settings to resolve remaining partial or blocked items."
    }
    else {
        $checks += New-Check "config_status" "Settings configuration diagnostics" "failed" "secret policy missing" "Fix config diagnostics before exposing Settings to a customer."
    }

    $modelGateway = $configItems | Where-Object { $_.id -eq "model_gateway" } | Select-Object -First 1
    if ($modelGateway) {
        $gatewayBase = $modelGateway.fields.base_url
        $gatewayModel = $modelGateway.fields.model
        $gatewayKey = $modelGateway.fields.api_key
        if ($gatewayBase -and $gatewayModel -and $gatewayBase -ne "missing_config" -and $gatewayModel -ne "missing_config" -and $gatewayKey -eq "configured") {
            $checks += New-Check "model_configuration" "Model gateway configuration visibility" "passed" "base_url=$gatewayBase; model=$gatewayModel; api_key=configured" "Keep the model gateway visible in Settings and do not echo secret values."
        }
        else {
            $checks += New-Check "model_configuration" "Model gateway configuration visibility" "blocked" "model gateway is visible but not fully configured" "Fill model base URL, model name, and API key in Settings before customer handoff."
        }
    }
    else {
        $checks += New-Check "model_configuration" "Model gateway configuration visibility" "failed" "model_gateway item missing from config/status" "Restore config/status model gateway diagnostics."
    }

    $pathItems = @($configItems | Where-Object { $_.id -in @("data_dir", "document_output_dir", "memory_vault", "codegraph_root") })
    if ($pathItems.Count -eq 4) {
        $pathsReady = @($pathItems | Where-Object { $_.status -in @("ready", "configured") })
        if ($pathsReady.Count -eq 4) {
            $checks += New-Check "path_visibility" "Filesystem path visibility" "passed" "data, documents, memory vault, and CodeGraph paths are visible in config/status" "Keep all writable paths inside the allowed bairui scope."
        }
        else {
            $checks += New-Check "path_visibility" "Filesystem path visibility" "blocked" "one or more required paths are missing or blocked" "Fix writable path roots before customer handoff."
        }
    }
    else {
        $checks += New-Check "path_visibility" "Filesystem path visibility" "failed" "missing one or more required path items" "Restore config/status path diagnostics."
    }

    $checklistText = $configStatus.body.config_status.checklist.markdown
    if ($checklistText -match "allowed bairui path scope|bairui scope") {
        $checks += New-Check "path_scope_policy" "Filesystem path scope policy" "passed" "config/status checklist includes path scope policy" "Keep server paths inside the documented bairui path scope."
    }
    else {
        $checks += New-Check "path_scope_policy" "Filesystem path scope policy" "failed" "path scope policy missing from config/status checklist" "Restore Settings path scope guidance before deployment."
    }
}
else {
    $checks += New-Check "config_status" "Settings configuration diagnostics" "failed" $configStatus.error "Check /config/status route and server logs."
    $checks += New-Check "model_configuration" "Model gateway configuration visibility" "failed" "config/status unavailable" "Check /config/status route and server logs."
    $checks += New-Check "path_visibility" "Filesystem path visibility" "failed" "config/status unavailable" "Check /config/status route and server logs."
    $checks += New-Check "path_scope_policy" "Filesystem path scope policy" "failed" "config/status unavailable" "Check /config/status route and server logs."
}

if (Test-Path -LiteralPath $ReadinessFile) {
    try {
        $readiness = Get-Content -LiteralPath $ReadinessFile -Raw | ConvertFrom-Json
        $checks += New-Check "readiness_file" "readiness.json evidence" "passed" "status=$($readiness.status); console_url=$($readiness.console_url)" "Attach this file to the deployment handoff report."
    }
    catch {
        $checks += New-Check "readiness_file" "readiness.json evidence" "failed" $_.Exception.Message "Regenerate readiness.json with deploy-usable."
    }
}
else {
    $checks += New-Check "readiness_file" "readiness.json evidence" "blocked" "missing: $ReadinessFile" "Run deploy-usable or set -ReadinessFile to the target evidence path."
}

$postgresEvidence = "not_checked"
$postgresStatus = "skipped"
$postgresNextStep = "Set -RequirePostgreSQL after the target server is configured for database-backed production."
if ($configStatus.ok) {
    $bodyText = $configStatus.body | ConvertTo-Json -Depth 20
    if ($bodyText -match "postgres|PostgreSQL|database") {
        $postgresEvidence = "configuration diagnostics include database/PostgreSQL evidence"
        $postgresStatus = "passed"
        $postgresNextStep = "Continue with migration, backup, and restore validation."
    }
    elseif ($RequirePostgreSQL) {
        $postgresEvidence = "configuration diagnostics did not expose PostgreSQL readiness evidence"
        $postgresStatus = "failed"
        $postgresNextStep = "Configure PostgreSQL and make database readiness visible before commercial handoff."
    }
}
elseif ($RequirePostgreSQL) {
    $postgresEvidence = "config status unavailable"
    $postgresStatus = "failed"
    $postgresNextStep = "Fix /config/status first, then rerun with -RequirePostgreSQL."
}
$checks += New-Check "postgresql_visibility" "PostgreSQL readiness visibility" $postgresStatus $postgresEvidence $postgresNextStep

$blockingStatuses = @("failed")
if ($RequireReady) {
    $blockingStatuses += "blocked"
}
$blocked = @($checks | Where-Object { $blockingStatuses -contains $_.status })
$overall = $(if ($blocked.Count -eq 0) { "passed" } else { "failed" })

$report = [pscustomobject]@{
    service = "bairui"
    mode = "server_deployment_verification"
    status = $overall
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    base_url = $BaseUrl.TrimEnd("/")
    readiness_file = $ReadinessFile
    require_ready = [bool]$RequireReady
    require_postgresql = [bool]$RequirePostgreSQL
    checks = $checks
    endpoints = $endpointResults
}

$parent = Split-Path -Parent $OutputPath
if ($parent) {
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
}
$json = $report | ConvertTo-Json -Depth 30
$json | Set-Content -LiteralPath $OutputPath -Encoding UTF8
$json

if ($overall -ne "passed") {
    throw "bairui server deployment verification failed"
}
