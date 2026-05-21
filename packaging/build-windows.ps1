$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Pyproject = Join-Path $Root "pyproject.toml"
$Version = "0.1.0"
$content = Get-Content $Pyproject -Raw
if ($content -match 'version\s*=\s*"([^"]+)"') { $Version = $Matches[1] }
$Name = "github-radar-$Version-windows-x64"
$Build = Join-Path $Root "dist\$Name"
if (Test-Path $Build) { Remove-Item $Build -Recurse -Force }
New-Item -ItemType Directory -Force -Path $Build | Out-Null

$ExcludeDirs = @(".pytest_cache", "__pycache__", "dist", "artifacts")
$ExcludeFiles = @(".env", ".ui-settings.json", "*.pyc")
Get-ChildItem $Root -Force | Where-Object {
  $n = $_.Name
  -not ($ExcludeDirs -contains $n) -and -not ($ExcludeFiles -contains $n)
} | ForEach-Object {
  Copy-Item $_.FullName -Destination $Build -Recurse -Force
}
New-Item -ItemType Directory -Force -Path (Join-Path $Build "artifacts") | Out-Null
Copy-Item (Join-Path $Root ".env.example") (Join-Path $Build ".env.example") -Force

@'
# GitHub Radar Windows Portable

## Requirements
- Node.js 20+
- Python 3.10+ for analysis CLI (`python -m app.cli ...`)
- Optional: Obsidian CLI if you want vault writeback

## Run UI
Double-click:

```bat
scripts\github-radar-windows.bat
```

Then open: http://localhost:4420

## Configure
Copy `.env.example` to `.env` and fill in:
- `GITHUB_TOKEN`
- `LLM_BASE_URL`
- `LLM_MODEL`
- `OBSIDIAN_VAULT`

Secrets are intentionally not bundled.
'@ | Set-Content -Encoding UTF8 (Join-Path $Build "README-FIRST.md")

$Zip = Join-Path $Root "dist\$Name.zip"
if (Test-Path $Zip) { Remove-Item $Zip -Force }
Compress-Archive -Path $Build -DestinationPath $Zip -Force
Write-Output $Zip
