$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

$forbiddenPaths = @(
    ".env",
    "data",
    "logs",
    "obsidian-vault"
)

foreach ($path in $forbiddenPaths) {
    if (Test-Path $path) {
        $tracked = git ls-files -- $path
        if ($tracked) {
            throw "Forbidden runtime path is tracked: $path"
        }
    }
}

$secretPattern = "sk-[A-Za-z0-9_-]{20,}|BEGIN (RSA|OPENSSH|PRIVATE) KEY|(password|secret|token|api[_-]?key)\s*[:=]\s*['`"][^'`"]{12,}['`"]"
$allowList = @(
    ".env.example",
    "README.md",
    "scripts/check-repo-hygiene.ps1"
)

$files = git ls-files |
    Where-Object {
        $_ -notmatch "^\.git/" -and
        $_ -notmatch "\.(png|jpg|jpeg|gif|webp|ico|bmp|sqlite|db)$" -and
        (Test-Path $_)
    }

$hits = @()
foreach ($file in $files) {
    if ($allowList -contains $file) {
        continue
    }

    $matches = Select-String -Path $file -Pattern $secretPattern -AllMatches -ErrorAction SilentlyContinue
    foreach ($match in $matches) {
        $hits += "${file}:$($match.LineNumber)"
    }
}

if ($hits.Count -gt 0) {
    $hits | ForEach-Object { Write-Error "Possible secret: $_" }
    throw "Repository hygiene check failed: possible secrets found."
}

Write-Host "Repository hygiene checks passed."
