$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

$Image = $env:IMAGE
if (-not $Image) { $Image = "github-radar:0.1.0" }

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  throw "Docker Desktop is required. Please install and start Docker Desktop."
}

docker build -t $Image .
New-Item -ItemType Directory -Force -Path "dist" | Out-Null
docker save $Image -o "dist/github-radar-0.1.0-container-windows-docker.tar"

Write-Host "Built image: $Image"
Write-Host "Exported: dist/github-radar-0.1.0-container-windows-docker.tar"
