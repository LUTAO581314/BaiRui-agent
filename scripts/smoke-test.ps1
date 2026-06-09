$ErrorActionPreference = "Stop"

$required = @(
    "README.md",
    "docs/00-product-blueprint.md",
    "docs/17-three-pillar-commercial-project-plan.md",
    "Dockerfile",
    "docker-compose.production.yml",
    ".env.example"
)

foreach ($path in $required) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Missing required skeleton file: $path"
    }
}

[pscustomobject]@{
    status = "ok"
    mode = "skeleton"
    message = "MOXI Hermes repository framework is present; runtime source is intentionally pending."
}
