$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root
npm install
npm run sidecar:windows
npm run desktop:pack:windows
