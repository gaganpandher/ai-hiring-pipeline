@echo off
:: ─────────────────────────────────────────────────────────────
:: AI Hiring Pipeline – Windows Launcher
:: Double-click this file to start the project
:: ─────────────────────────────────────────────────────────────

echo Starting AI Hiring Pipeline...
echo.

:: Check Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running.
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

:: Run the PowerShell setup script
powershell -ExecutionPolicy Bypass -File "%~dp0scripts\setup.ps1"

pause
