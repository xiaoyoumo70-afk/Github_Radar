$ErrorActionPreference = "Stop"
$AppDir = Resolve-Path (Join-Path $PSScriptRoot "..")
if (-not $env:PORT) { $env:PORT = "4420" }
Set-Location $AppDir
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
  Write-Error "Node.js 20+ is required. Install from https://nodejs.org/"
}
Start-Process "http://localhost:$env:PORT"
node server.mjs
