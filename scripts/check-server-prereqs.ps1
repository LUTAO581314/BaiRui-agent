param(
    [ValidateSet("local", "domain")]
    [string]$Mode = "local",
    [string]$Domain = "",
    [int]$Port = 8787,
    [string]$OutputPath = "artifacts/server-prereq-check.json",
    [switch]$RequireEnv,
    [switch]$RequireDocker
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

function Test-CommandAvailable {
    param([string]$Name)
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    return $null -ne $command
}

function Get-CommandVersion {
    param(
        [string]$Name,
        [string[]]$Args
    )
    try {
        $output = & $Name @Args 2>&1 | Out-String
        return ($output.Trim() -split "`r?`n")[0]
    }
    catch {
        return $_.Exception.Message
    }
}

function Test-PathPresent {
    param(
        [string]$Path,
        [string]$Id,
        [string]$Name,
        [string]$NextStep
    )
    if (Test-Path -LiteralPath $Path) {
        return New-Check $Id $Name "passed" "present: $Path" "Keep this file in the deployment source checkout."
    }
    return New-Check $Id $Name "failed" "missing: $Path" $NextStep
}

$checks = @()

foreach ($asset in @(
    @{ Path = "docker-compose.production.yml"; Id = "compose_file"; Name = "Docker Compose production file" },
    @{ Path = ".env.example"; Id = "root_env_example"; Name = "Root environment template" },
    @{ Path = "infra/hermes/env.example"; Id = "server_env_example"; Name = "Server environment template" },
    @{ Path = "scripts/deploy-usable.ps1"; Id = "windows_deploy_script"; Name = "Windows usable deploy script" },
    @{ Path = "scripts/deploy-usable.sh"; Id = "linux_deploy_script"; Name = "Linux usable deploy script" },
    @{ Path = "scripts/verify-server-deployment.ps1"; Id = "server_verifier"; Name = "Server deployment verifier" }
)) {
    $checks += Test-PathPresent $asset.Path $asset.Id $asset.Name "Restore deployment assets from the bairui repository before trying a server deployment."
}

if (Test-CommandAvailable "git") {
    $checks += New-Check "git" "Git CLI" "passed" (Get-CommandVersion "git" @("--version")) "Use Git to record the exact deployed commit."
}
else {
    $checks += New-Check "git" "Git CLI" "failed" "git not found" "Install Git before pulling or updating the source checkout."
}

if (Test-CommandAvailable "python") {
    $version = Get-CommandVersion "python" @("--version")
    $checks += New-Check "python" "Python runtime" "passed" $version "Use this Python runtime for bairui CLI checks."
}
else {
    $checks += New-Check "python" "Python runtime" "failed" "python not found" "Install Python 3.11+ before running bairui."
}

$dockerAvailable = Test-CommandAvailable "docker"
if ($dockerAvailable) {
    $dockerVersion = Get-CommandVersion "docker" @("--version")
    $checks += New-Check "docker" "Docker CLI" "passed" $dockerVersion "Use Docker for PostgreSQL, Sonic, and production compose."
    try {
        $composeVersion = docker compose version 2>&1 | Out-String
        if ($LASTEXITCODE -eq 0) {
            $checks += New-Check "docker_compose" "Docker Compose plugin" "passed" (($composeVersion.Trim() -split "`r?`n")[0]) "Use docker compose for deploy-usable."
        }
        elseif (Test-CommandAvailable "docker-compose") {
            $checks += New-Check "docker_compose" "Docker Compose standalone" "passed" (Get-CommandVersion "docker-compose" @("--version")) "Standalone docker-compose is available as fallback."
        }
        else {
            $checks += New-Check "docker_compose" "Docker Compose" "failed" "Docker is installed but compose is unavailable" "Install the Docker Compose plugin or docker-compose."
        }
    }
    catch {
        if (Test-CommandAvailable "docker-compose") {
            $checks += New-Check "docker_compose" "Docker Compose standalone" "passed" (Get-CommandVersion "docker-compose" @("--version")) "Standalone docker-compose is available as fallback."
        }
        else {
            $checks += New-Check "docker_compose" "Docker Compose" "failed" $_.Exception.Message "Install the Docker Compose plugin or docker-compose."
        }
    }
}
elseif ($RequireDocker) {
    $checks += New-Check "docker" "Docker CLI" "failed" "docker not found" "Install Docker before running production compose."
    $checks += New-Check "docker_compose" "Docker Compose" "failed" "docker not found" "Install Docker Compose before running production compose."
}
else {
    $checks += New-Check "docker" "Docker CLI" "skipped" "docker not found" "Use -RequireDocker for strict server deployment checks."
    $checks += New-Check "docker_compose" "Docker Compose" "skipped" "docker not found" "Use -RequireDocker for strict server deployment checks."
}

if (Test-Path -LiteralPath ".env") {
    $envText = Get-Content -LiteralPath ".env" -Raw
    $requiredNames = @("POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD", "HERMES_HOST", "HERMES_PORT")
    $missing = @($requiredNames | Where-Object { $envText -notmatch "(?m)^$([regex]::Escape($_))=" })
    if ($missing.Count -eq 0) {
        $checks += New-Check "env_file" "Runtime .env file" "passed" ".env exists with required names; values not printed" "Keep .env protected and never commit it."
    }
    elseif ($RequireEnv) {
        $checks += New-Check "env_file" "Runtime .env file" "failed" "missing names: $($missing -join ', ')" "Copy .env.example to .env and fill required values."
    }
    else {
        $checks += New-Check "env_file" "Runtime .env file" "blocked" "missing names: $($missing -join ', ')" "Copy .env.example to .env before strict server deployment."
    }
}
elseif ($RequireEnv) {
    $checks += New-Check "env_file" "Runtime .env file" "failed" ".env missing" "Copy .env.example to .env and fill protected server values."
}
else {
    $checks += New-Check "env_file" "Runtime .env file" "blocked" ".env missing" "deploy-usable can generate local defaults; production should prepare .env first."
}

foreach ($dir in @("data", "logs", "obsidian-vault")) {
    try {
        if (-not (Test-Path -LiteralPath $dir)) {
            $checks += New-Check "writable_$dir" "$dir writable path" "blocked" "missing: $dir" "Run deploy-usable or create this mounted path before strict production deployment."
            continue
        }
        $probe = Join-Path $dir (".bairui-write-probe-" + [Guid]::NewGuid().ToString("N"))
        "probe" | Set-Content -LiteralPath $probe -Encoding UTF8
        Remove-Item -LiteralPath $probe -Force
        $checks += New-Check "writable_$dir" "$dir writable path" "passed" "write probe succeeded: $dir" "Keep this path mounted and backed up as appropriate."
    }
    catch {
        $checks += New-Check "writable_$dir" "$dir writable path" "failed" $_.Exception.Message "Fix directory permissions or mount policy before deployment."
    }
}

try {
    $drive = Get-PSDrive -Name (Get-Location).Path.Substring(0, 1) -ErrorAction Stop
    $freeGb = [math]::Round($drive.Free / 1GB, 2)
    if ($freeGb -ge 5) {
        $checks += New-Check "disk_free" "Disk free space" "passed" "$freeGb GB free on $($drive.Name):" "Monitor disk usage after PostgreSQL and document ingestion start."
    }
    else {
        $checks += New-Check "disk_free" "Disk free space" "blocked" "$freeGb GB free on $($drive.Name):" "Reserve at least 5 GB for a trial and much more for production data."
    }
}
catch {
    $checks += New-Check "disk_free" "Disk free space" "blocked" $_.Exception.Message "Check server disk capacity manually."
}

try {
    $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($listener) {
        $checks += New-Check "port_$Port" "Port $Port availability" "blocked" "already listening on port $Port" "Stop the existing service or choose a different HERMES_PORT."
    }
    else {
        $checks += New-Check "port_$Port" "Port $Port availability" "passed" "no listener detected on port $Port" "Use this port for local bairui runtime binding."
    }
}
catch {
    $checks += New-Check "port_$Port" "Port $Port availability" "blocked" $_.Exception.Message "Check port availability manually on this host."
}

if ($Mode -eq "domain") {
    if ([string]::IsNullOrWhiteSpace($Domain)) {
        $checks += New-Check "domain_value" "Domain value" "failed" "domain mode selected without -Domain" "Pass -Domain, for example bairui.example.com."
    }
    else {
        try {
            $addresses = [System.Net.Dns]::GetHostAddresses($Domain)
            if ($addresses.Count -gt 0) {
                $checks += New-Check "domain_dns" "Domain DNS resolution" "passed" "$Domain -> $($addresses.IPAddressToString -join ', ')" "Verify the resolved address is the target server before switching traffic."
            }
            else {
                $checks += New-Check "domain_dns" "Domain DNS resolution" "failed" "no addresses returned for $Domain" "Fix DNS before domain production deployment."
            }
        }
        catch {
            $checks += New-Check "domain_dns" "Domain DNS resolution" "failed" $_.Exception.Message "Fix DNS before domain production deployment."
        }
    }
}
else {
    $checks += New-Check "domain_dns" "Domain DNS resolution" "skipped" "local mode" "Use -Mode domain -Domain <name> for domain production checks."
}

$failed = @($checks | Where-Object { $_.status -eq "failed" })
$overall = $(if ($failed.Count -eq 0) { "passed" } else { "failed" })

$report = [pscustomobject]@{
    service = "bairui"
    mode = "server_prereq_check"
    status = $overall
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    deployment_mode = $Mode
    domain = $Domain
    port = $Port
    require_env = [bool]$RequireEnv
    require_docker = [bool]$RequireDocker
    checks = $checks
}

$parent = Split-Path -Parent $OutputPath
if ($parent) {
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
}
$json = $report | ConvertTo-Json -Depth 20
$json | Set-Content -LiteralPath $OutputPath -Encoding UTF8
$json

if ($overall -ne "passed") {
    throw "bairui server prerequisite check failed"
}
