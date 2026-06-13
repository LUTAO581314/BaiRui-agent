$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$targets = @(
    "web/bairui-console/index.html",
    "web/bairui-console/app.js",
    "web/bairui-console/styles.css",
    "src/hermes/frontend_contract.py"
)

$baiLongMaCn = [string]([char]0x767D) + [string]([char]0x9F99) + [string]([char]0x9A6C)
$xiaoBaiLongCn = [string]([char]0x5C0F) + [string]([char]0x767D) + [string]([char]0x9F99)

$forbiddenPublicBrands = @(
    "Hermes",
    "MOXI",
    "Moxi",
    "moxi",
    "BaiLongma",
    $baiLongMaCn,
    $xiaoBaiLongCn,
    "xiaoyuanda666-ship-it"
)

$violations = @()

foreach ($relativePath in $targets) {
    $path = Join-Path $repoRoot $relativePath
    if (-not (Test-Path -LiteralPath $path)) {
        $violations += "missing public brand scan target: $relativePath"
        continue
    }

    $content = Get-Content -LiteralPath $path -Raw -Encoding UTF8
    foreach ($brand in $forbiddenPublicBrands) {
        if ($content.Contains($brand)) {
            $violations += "forbidden public brand '$brand' found in $relativePath"
        }
    }
}

if ($violations.Count -gt 0) {
    $violations | ForEach-Object { Write-Error $_ }
    throw "Public brand scan failed."
}

Write-Host "Public brand scan passed."
