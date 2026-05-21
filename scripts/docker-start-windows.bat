@echo off
setlocal
cd /d "%~dp0\.."
where docker >nul 2>nul
if errorlevel 1 (
  echo Docker Desktop is required. Please install and start Docker Desktop.
  exit /b 1
)
docker compose up -d --build
echo GitHub Radar is starting: http://localhost:4420
pause
