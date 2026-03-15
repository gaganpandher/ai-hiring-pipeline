$ErrorActionPreference = "Stop"

function Log  { param($msg) Write-Host "[setup] $msg" -ForegroundColor Cyan }
function Ok   { param($msg) Write-Host "[  OK ] $msg" -ForegroundColor Green }
function Warn { param($msg) Write-Host "[ WARN] $msg" -ForegroundColor Yellow }
function Err  { param($msg) Write-Host "[ERROR] $msg" -ForegroundColor Red; exit 1 }

Log "Checking prerequisites..."

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Err "Docker not found. Install Docker Desktop first."
}

try {
    docker compose version | Out-Null
}
catch {
    Err "Docker Compose not found. It comes bundled with Docker Desktop."
}

Ok "Docker found"

$rootDir = Split-Path -Parent $PSScriptRoot

if (-not (Test-Path "$rootDir\.env")) {
    Err ".env file not found at $rootDir\.env - please create it first."
}

Ok ".env found"

Log "Building Docker images (this may take a few minutes)..."
Set-Location $rootDir
docker compose build --parallel
Ok "Images built"

Log "Starting MySQL, Redis, Kafka, Zookeeper..."
docker compose up -d mysql redis zookeeper kafka

Log "Waiting 20 seconds for services to be healthy..."
Start-Sleep -Seconds 20
Ok "Infrastructure up"

Log "Starting Kafka UI..."
docker compose up -d kafka-ui
Ok "Kafka UI up -> http://localhost:8080"

Log "Starting FastAPI backend..."
docker compose up -d backend
Start-Sleep -Seconds 5

try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/health" -Method Get
    Ok "Backend up -> http://localhost:8000/api/docs (status: $($health.status))"
}
catch {
    Warn "Backend health check failed - it may still be starting up"
}

Log "Starting React frontend..."
docker compose up -d frontend
Start-Sleep -Seconds 3
Ok "Frontend up -> http://localhost:3000"

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  AI Hiring Pipeline is running!                " -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  React App    -> " -NoNewline
Write-Host "http://localhost:3000" -ForegroundColor Cyan
Write-Host "  FastAPI Docs -> " -NoNewline
Write-Host "http://localhost:8000/api/docs" -ForegroundColor Cyan
Write-Host "  Kafka UI     -> " -NoNewline
Write-Host "http://localhost:8080" -ForegroundColor Cyan
Write-Host "  MySQL        -> " -NoNewline
Write-Host "localhost:3306  (hiring_user / hiring_pass)" -ForegroundColor Cyan
Write-Host "  Redis        -> " -NoNewline
Write-Host "localhost:6379" -ForegroundColor Cyan
Write-Host ""
Write-Host "  View logs:  " -NoNewline
Write-Host "docker compose logs -f backend" -ForegroundColor Yellow
Write-Host "  Stop all:   " -NoNewline
Write-Host "docker compose down" -ForegroundColor Yellow
Write-Host ""