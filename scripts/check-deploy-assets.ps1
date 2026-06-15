$ErrorActionPreference = "Stop"

$required = @(
    "infra/hermes/env.example",
    "infra/hermes/systemd/bairui-hermes.service",
    "infra/hermes/scripts/deploy-hermes.sh",
    "infra/sonic/config.cfg",
    "scripts/deploy-usable.ps1",
    "scripts/deploy-usable.sh",
    "scripts/check-server-prereqs.ps1",
    "scripts/verify-server-deployment.ps1",
    "scripts/verify-postgres-production.ps1",
    "scripts/commercial-go-no-go.ps1",
    "scripts/export-commercial-handoff-bundle.ps1",
    "scripts/run-server-trial-acceptance.ps1",
    "docker-compose.production.yml",
    ".env.example"
)

foreach ($path in $required) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Missing deployment asset: $path"
    }
}

$parts = @()
foreach ($path in $required) {
    $parts += Get-Content -LiteralPath $path -Raw
}
$combined = $parts -join "`n"

if ($combined -match "BEGIN (RSA|OPENSSH) PRIVATE KEY") {
    throw "Deployment assets must not contain private keys."
}

if ($combined -notmatch "bairui") {
    throw "Deployment assets must include bairui branding."
}

[pscustomobject]@{
    status = "ok"
    mode = "deployment-assets"
    message = "bairui deployment assets are present."
}
