$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

$Py = $env:PYTHON
if (-not $Py) { $Py = "python" }

$ver = & $Py -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ([version]$ver -lt [version]"3.11") {
  Write-Warning "Building sidecar with Python $ver, but pyproject.toml declares >=3.11. Release builds should use Python 3.11+."
}

try {
  & $Py -m PyInstaller --version | Out-Null
} catch {
  throw "PyInstaller is not installed. Install with: $Py -m pip install pyinstaller"
}

$Out = Join-Path $Root "dist-sidecar\win"
$Build = Join-Path $Root "build"
$Spec = Join-Path $Root "github-radar-cli.spec"
if (Test-Path $Out) { Remove-Item $Out -Recurse -Force }
if (Test-Path (Join-Path $Build "github-radar-cli")) { Remove-Item (Join-Path $Build "github-radar-cli") -Recurse -Force }
if (Test-Path $Spec) { Remove-Item $Spec -Force }
New-Item -ItemType Directory -Force -Path $Out | Out-Null

& $Py -m PyInstaller `
  --clean `
  --onefile `
  --name github-radar-cli `
  --distpath $Out `
  --workpath $Build `
  --paths $Root `
  --paths (Join-Path $Root "github_radar\analyze") `
  --collect-submodules github_radar `
  --collect-submodules app `
  --hidden-import pydantic `
  --hidden-import pydantic_settings `
  --hidden-import dotenv `
  --hidden-import rich `
  --hidden-import typer `
  (Join-Path $Root "desktop\python_sidecar_entry.py")

& (Join-Path $Out "github-radar-cli.exe") version
Write-Output (Join-Path $Out "github-radar-cli.exe")
