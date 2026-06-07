param(
  [string]$Destination = "public-ai-brief-export",
  [string[]]$ExtraBlockedTerms = @()
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$source = Join-Path $repoRoot "public-ai-brief"
$target = Join-Path $repoRoot $Destination

if (-not (Test-Path $source)) {
  throw "public-ai-brief directory not found: $source"
}

if (Test-Path $target) {
  Remove-Item -LiteralPath $target -Recurse -Force
}

Copy-Item -LiteralPath $source -Destination $target -Recurse

$blocked = @(
  "Hermes",
  "BaiLongma",
  ([string][char]0x767D + [string][char]0x9F99 + [string][char]0x9A6C),
  "bailongma",
  "TrendRadar",
  "bairui.chat",
  "38.76.190.53",
  "supermoxi"
) + $ExtraBlockedTerms

$files = Get-ChildItem -LiteralPath $target -Recurse -File
$allowedAttribution = @(
  "https://github.com/LUTAO581314/hermes-"
)

$matches = foreach ($file in $files) {
  $lineNumber = 0
  Get-Content -LiteralPath $file.FullName | ForEach-Object {
    $lineNumber += 1
    $line = $_
    $scanLine = $line
    foreach ($allowed in $allowedAttribution) {
      $scanLine = $scanLine.Replace($allowed, "[ALLOWED_REPO_SOURCE]")
    }
    foreach ($term in $blocked) {
      if ($scanLine.IndexOf($term, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) {
        [pscustomobject]@{
          Path = $file.FullName
          LineNumber = $lineNumber
          Line = $line
        }
        break
      }
    }
  }
}
if ($matches) {
  $matches | ForEach-Object {
    "{0}:{1}: {2}" -f $_.Path, $_.LineNumber, $_.Line.Trim()
  }
  throw "Blocked private terms found in exported public AI brief."
}

Write-Host "Exported white-label AI brief to: $target"
