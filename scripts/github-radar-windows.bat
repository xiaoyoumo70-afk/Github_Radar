@echo off
setlocal
set APP_DIR=%~dp0\..
if "%PORT%"=="" set PORT=4420
cd /d "%APP_DIR%"
where node >nul 2>nul
if errorlevel 1 (
  echo [GitHub Radar] Node.js is required. Please install Node.js 20+.
  pause
  exit /b 1
)
start "" "http://localhost:%PORT%"
node server.mjs
