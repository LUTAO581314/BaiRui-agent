param(
    [ValidateSet("local", "domain")]
    [string] $Mode = "local",
    [string] $Domain = "",
    [int] $TimeoutSeconds = 120
)

$ErrorActionPreference = "Stop"

function Write-Step($Message) {
    Write-Host "== $Message =="
}

function New-Secret {
    $bytes = New-Object byte[] 24
    [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    return ([BitConverter]::ToString($bytes) -replace "-", "").ToLowerInvariant()
}

function Ensure-EnvFile {
    if (-not (Test-Path -LiteralPath ".env")) {
        if (-not (Test-Path -LiteralPath ".env.example")) {
            throw ".env.example is missing"
        }
        Copy-Item -LiteralPath ".env.example" -Destination ".env"
    }
}

function Ensure-EnvValue($Name, $Value) {
    $content = Get-Content -LiteralPath ".env" -Raw
    if ($content -match "(?m)^$([regex]::Escape($Name))=") {
        if ($content -match "(?m)^$([regex]::Escape($Name))=\s*$") {
            $content = $content -replace "(?m)^$([regex]::Escape($Name))=.*$", "$Name=$Value"
            Set-Content -LiteralPath ".env" -Value $content -NoNewline
        }
        return
    }
    Add-Content -LiteralPath ".env" -Value "$Name=$Value"
}

function Invoke-Compose([string[]] $Arguments) {
    $docker = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $docker) {
        throw "Docker is required for one-command usable deployment."
    }
    & docker compose version *> $null
    if ($LASTEXITCODE -eq 0) {
        & docker compose -f docker-compose.production.yml @Arguments
        if ($LASTEXITCODE -ne 0) { throw "docker compose failed" }
        return
    }
    $legacy = Get-Command docker-compose -ErrorAction SilentlyContinue
    if (-not $legacy) {
        throw "Docker Compose is required."
    }
    & docker-compose -f docker-compose.production.yml @Arguments
    if ($LASTEXITCODE -ne 0) { throw "docker-compose failed" }
}

function Wait-Health($Url, $TimeoutSeconds) {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        try {
            $response = Invoke-RestMethod -Uri $Url -TimeoutSec 5
            if ($response.status -eq "ok") {
                return
            }
        } catch {
            Start-Sleep -Seconds 2
        }
    } while ((Get-Date) -lt $deadline)
    throw "Hermes health check timed out: $Url"
}

function Build-FrontendIfPresent {
    $frontendDir = $null
    if (Test-Path -LiteralPath "frontend\package.json") {
        $frontendDir = "frontend"
    } elseif (Test-Path -LiteralPath "package.json") {
        $frontendDir = "."
    }

    if (-not $frontendDir) {
        Write-Step "No npm frontend detected; skipping frontend build"
        return
    }

    $manager = "npm"
    $installArgs = @("install")
    $buildArgs = @("run", "build")

    Push-Location $frontendDir
    try {
        if (Test-Path -LiteralPath "package-lock.json") {
            $manager = "npm"
            $installArgs = @("ci")
        } elseif (Test-Path -LiteralPath "pnpm-lock.yaml") {
            $manager = "pnpm"
            $installArgs = @("install", "--frozen-lockfile")
        } elseif (Test-Path -LiteralPath "yarn.lock") {
            $manager = "yarn"
            $installArgs = @("install", "--frozen-lockfile")
            $buildArgs = @("run", "build")
        } elseif ((Test-Path -LiteralPath "bun.lockb") -or (Test-Path -LiteralPath "bun.lock")) {
            $manager = "bun"
            $installArgs = @("install", "--frozen-lockfile")
            $buildArgs = @("run", "build")
        }

        $cmd = Get-Command $manager -ErrorAction SilentlyContinue
        if (-not $cmd) {
            throw "$manager is required because $frontendDir uses $manager."
        }

        Write-Step "Building frontend in $frontendDir with $manager"
        & $manager @installArgs
        if ($LASTEXITCODE -ne 0) { throw "npm dependency install failed" }
        & $manager @buildArgs
        if ($LASTEXITCODE -ne 0) { throw "frontend build failed" }
    } finally {
        Pop-Location
    }
}

Write-Step "Preparing usable MOXI deployment"
Ensure-EnvFile
Ensure-EnvValue "POSTGRES_DB" "moxi"
Ensure-EnvValue "POSTGRES_USER" "moxi"

$envContent = Get-Content -LiteralPath ".env" -Raw
if ($envContent -match "(?m)^POSTGRES_PASSWORD=\s*$" -or $envContent -notmatch "(?m)^POSTGRES_PASSWORD=") {
    Ensure-EnvValue "POSTGRES_PASSWORD" (New-Secret)
}

Ensure-EnvValue "HERMES_ENV" "production"
Ensure-EnvValue "HERMES_HOST" "127.0.0.1"
Ensure-EnvValue "HERMES_PORT" "8787"

New-Item -ItemType Directory -Force -Path "data", "data/postgres", "data/hermes", "logs", "logs/hermes", "obsidian-vault" | Out-Null

if ($Mode -eq "domain" -and [string]::IsNullOrWhiteSpace($Domain)) {
    throw "Domain mode requires -Domain, for example: -Mode domain -Domain moxi.example.com"
}

Build-FrontendIfPresent

Write-Step "Starting PostgreSQL and Hermes"
Invoke-Compose @("up", "-d", "--build")

Write-Step "Waiting for Hermes health"
Wait-Health "http://127.0.0.1:8787/health" $TimeoutSeconds

Write-Step "Deployment is usable"
Write-Host "Hermes health: http://127.0.0.1:8787/health"
Write-Host "Hermes ready:  http://127.0.0.1:8787/ready"
Write-Host "Capabilities:   http://127.0.0.1:8787/capabilities"
if ($Mode -eq "domain") {
    Write-Host "Next domain step: configure DNS, HTTPS, and Nginx for https://$Domain/"
} else {
    Write-Host "Local production mode is active. Public callbacks remain disabled unless a reviewed gateway is configured."
}
