param(
    [string]$OutputDir = "artifacts/commercial-handoff-bundle",
    [string[]]$EvidencePaths = @(
        "artifacts/product-acceptance.json",
        "artifacts/server-deployment-verification.json",
        "artifacts/postgres-production-verification.json",
        "artifacts/commercial-go-no-go.json"
    ),
    [switch]$SkipLocalEvidenceGeneration,
    [switch]$IncludeDocs
)

$ErrorActionPreference = "Stop"

function New-ArtifactRecord {
    param(
        [string]$Name,
        [string]$SourcePath,
        [bool]$Present,
        [string]$Status,
        [string]$Note
    )
    [pscustomobject]@{
        name = $Name
        source_path = $SourcePath
        present = $Present
        status = $Status
        note = $Note
    }
}

function Copy-SafeFile {
    param(
        [string]$SourcePath,
        [string]$DestinationPath
    )
    $parent = Split-Path -Parent $DestinationPath
    if ($parent) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    Copy-Item -LiteralPath $SourcePath -Destination $DestinationPath -Force
}

function Read-JsonSafely {
    param([string]$Path)
    try {
        return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
    }
    catch {
        return [pscustomobject]@{
            status = "failed"
            error = $_.Exception.Message
        }
    }
}

function Test-SafeEvidencePath {
    param([string]$Path)
    $leaf = (Split-Path -Leaf $Path).ToLowerInvariant()
    $normalized = $Path.Replace("\", "/").ToLowerInvariant()
    if ($leaf -eq ".env" -or $normalized -match "/\.env($|[./])") {
        return $false
    }
    if ($leaf -match "\.(log|dump|sqlite|db|pem|key)$") {
        return $false
    }
    if ($normalized -match "(secret|password|token|customer-data|runtime-data|qr-state)") {
        return $false
    }
    return $true
}

$outputRoot = [System.IO.Path]::GetFullPath($OutputDir)
New-Item -ItemType Directory -Force -Path $outputRoot | Out-Null

if (-not $SkipLocalEvidenceGeneration) {
    $productAcceptancePath = "artifacts/product-acceptance.json"
    $goNoGoPath = "artifacts/commercial-go-no-go.json"
    & .\scripts\product-acceptance.ps1 -OutputPath $productAcceptancePath | Out-Null
    & .\scripts\commercial-go-no-go.ps1 -OutputPath $goNoGoPath | Out-Null
}

$records = @()
$copied = @()

foreach ($path in $EvidencePaths) {
    $full = [System.IO.Path]::GetFullPath($path)
    $name = Split-Path -Leaf $full
    if (-not (Test-SafeEvidencePath $path)) {
        $records += New-ArtifactRecord -Name $name -SourcePath $path -Present $false -Status "rejected" -Note "unsafe evidence path rejected"
        continue
    }
    if (Test-Path -LiteralPath $full) {
        $target = Join-Path $outputRoot $name
        Copy-SafeFile -SourcePath $full -DestinationPath $target
        $copied += $name

        $payload = Read-JsonSafely $full
        $status = if ($payload.status) { [string]$payload.status } else { "present" }
        $records += New-ArtifactRecord -Name $name -SourcePath $path -Present $true -Status $status -Note "copied to bundle"
    }
    else {
        $records += New-ArtifactRecord -Name $name -SourcePath $path -Present $false -Status "missing" -Note "evidence not yet collected"
    }
}

$docs = @(
    "docs/27-commercial-trial-delivery-quickstart.md",
    "docs/29-commercial-trial-handoff-pack.md",
    "docs/30-server-deployment-acceptance-report.md",
    "docs/31-postgresql-production-verification.md",
    "docs/32-commercial-go-no-go-report.md"
)

if ($IncludeDocs) {
    foreach ($doc in $docs) {
        if (Test-Path -LiteralPath $doc) {
            $target = Join-Path $outputRoot ("docs\" + (Split-Path -Leaf $doc))
            Copy-SafeFile -SourcePath $doc -DestinationPath $target
        }
    }
}

$gitCommit = (git rev-parse --short HEAD 2>$null | Out-String).Trim()
$manifest = [pscustomobject]@{
    service = "bairui"
    mode = "commercial_handoff_bundle"
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    git_commit = $gitCommit
    bundle_dir = $outputRoot
    local_evidence_generated = -not [bool]$SkipLocalEvidenceGeneration
    include_docs = [bool]$IncludeDocs
    artifacts = $records
    docs = $docs
    summary = [pscustomobject]@{
        present_count = @($records | Where-Object { $_.present }).Count
        missing_count = @($records | Where-Object { -not $_.present }).Count
        blocked = @($records | Where-Object { @("missing", "blocked", "failed", "no_go", "rejected") -contains $_.status }).Count -gt 0
    }
}

$manifestPath = Join-Path $outputRoot "manifest.json"
$manifest | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $manifestPath -Encoding UTF8

$readme = @"
# bairui Commercial Handoff Bundle

This folder contains operator-safe evidence for a bairui commercial trial.

Included evidence:

$((($records | ForEach-Object { "- $($_.name): $($_.status)" }) -join "`n"))

Rules:

- Do not place `.env`, secrets, customer data, raw logs, or runtime dumps here.
- Re-run the verifier scripts when a required artifact is missing.
- Use this bundle together with the handoff pack and Go/No-Go report.
"@

$readme | Set-Content -LiteralPath (Join-Path $outputRoot "README.md") -Encoding UTF8

$manifest | ConvertTo-Json -Depth 20
