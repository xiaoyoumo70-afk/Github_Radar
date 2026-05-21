$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Pyproject = Join-Path $Root "pyproject.toml"
$Version = "0.1.0"
$content = Get-Content $Pyproject -Raw
if ($content -match 'version\s*=\s*"([^"]+)"') { $Version = $Matches[1] }

$NodeVersion = $env:NODE_VERSION
if (-not $NodeVersion) { $NodeVersion = "22.22.2" }
$PythonVersion = $env:PYTHON_VERSION
if (-not $PythonVersion) { $PythonVersion = "3.11.9" }

$Name = "github-radar-$Version-windows-x64-bundled"
$Dist = Join-Path $Root "dist"
$Build = Join-Path $Dist $Name
$Cache = Join-Path $Root "packaging\.cache"
$Runtime = Join-Path $Build "runtime"

if (Test-Path $Build) { Remove-Item $Build -Recurse -Force }
New-Item -ItemType Directory -Force -Path $Build,$Runtime,$Cache | Out-Null

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

# Download and bundle Node.js Windows x64 portable.
$NodeZip = Join-Path $Cache "node-v$NodeVersion-win-x64.zip"
$NodeUrl = "https://nodejs.org/dist/v$NodeVersion/node-v$NodeVersion-win-x64.zip"
if (-not (Test-Path $NodeZip)) {
  Write-Host "Downloading Node.js $NodeVersion..."
  Invoke-WebRequest -Uri $NodeUrl -OutFile $NodeZip
}
Expand-Archive -Path $NodeZip -DestinationPath $Runtime -Force
$NodeDir = Join-Path $Runtime "node"
if (Test-Path $NodeDir) { Remove-Item $NodeDir -Recurse -Force }
Rename-Item (Join-Path $Runtime "node-v$NodeVersion-win-x64") $NodeDir

# Download and bundle Python embeddable runtime.
$PyZipName = "python-$PythonVersion-embed-amd64.zip"
$PyZip = Join-Path $Cache $PyZipName
$PyUrl = "https://www.python.org/ftp/python/$PythonVersion/$PyZipName"
if (-not (Test-Path $PyZip)) {
  Write-Host "Downloading Python embeddable $PythonVersion..."
  Invoke-WebRequest -Uri $PyUrl -OutFile $PyZip
}
$PyDir = Join-Path $Runtime "python"
New-Item -ItemType Directory -Force -Path $PyDir | Out-Null
Expand-Archive -Path $PyZip -DestinationPath $PyDir -Force

# Enable import from app root and site-packages in pythonXX._pth.
$Pth = Get-ChildItem $PyDir -Filter "python*._pth" | Select-Object -First 1
if ($Pth) {
@'
.
Lib
Lib\site-packages
..\..
import site
'@ | Set-Content -Encoding ASCII $Pth.FullName
}
New-Item -ItemType Directory -Force -Path (Join-Path $PyDir "Lib\site-packages") | Out-Null

# Install dependencies into embedded Python. This requires network once at build time.
$PyExe = Join-Path $PyDir "python.exe"
$GetPip = Join-Path $Cache "get-pip.py"
if (-not (Test-Path $GetPip)) {
  Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $GetPip
}
& $PyExe $GetPip --no-warn-script-location
& $PyExe -m pip install --no-cache-dir --target (Join-Path $PyDir "Lib\site-packages") `
  "pydantic>=2.0" "pydantic-settings>=2.0" "typer>=0.9" "rich>=13.0" "requests>=2.31" "python-dotenv>=1.0"

@'
@echo off
setlocal
set APP_DIR=%~dp0
if "%PORT%"=="" set PORT=4420
set PATH=%APP_DIR%runtime\node;%APP_DIR%runtime\python;%PATH%
set PYTHONPATH=%APP_DIR%;%APP_DIR%runtime\python\Lib\site-packages
cd /d "%APP_DIR%"
start "" "http://localhost:%PORT%"
"%APP_DIR%runtime\node\node.exe" "%APP_DIR%server.mjs"
'@ | Set-Content -Encoding ASCII (Join-Path $Build "GitHub-Radar.bat")

@'
@echo off
setlocal
set APP_DIR=%~dp0
set PATH=%APP_DIR%runtime\python;%PATH%
set PYTHONPATH=%APP_DIR%;%APP_DIR%runtime\python\Lib\site-packages
cd /d "%APP_DIR%"
"%APP_DIR%runtime\python\python.exe" -c "from app.cli import main; main()" %*
'@ | Set-Content -Encoding ASCII (Join-Path $Build "github-radar-cli.bat")

@"
# GitHub Radar Windows Bundled

This build bundles:

- Node.js runtime
- Python embeddable runtime
- Python dependencies used by GitHub Radar

## Run UI

Double-click:

```bat
GitHub-Radar.bat
```

Open: http://localhost:4420

## Run CLI

```bat
github-radar-cli.bat --help
```

## Configure

Copy `.env.example` to `.env` and fill in:

- `GITHUB_TOKEN`
- `LLM_BASE_URL`
- `LLM_MODEL`
- `OBSIDIAN_VAULT`

Secrets and analyzed artifacts are intentionally not bundled.
"@ | Set-Content -Encoding UTF8 (Join-Path $Build "README-FIRST.md")

$Zip = Join-Path $Dist "$Name.zip"
if (Test-Path $Zip) { Remove-Item $Zip -Force }
Compress-Archive -Path $Build -DestinationPath $Zip -Force
Write-Output $Zip
