# ─────────────────────────────────────────────────────────────
# reset.ps1 - Full wipe and rebuild
# Run from your project root folder
# ─────────────────────────────────────────────────────────────

Write-Host "Stopping all containers..." -ForegroundColor Cyan
docker compose down --remove-orphans

Write-Host "Removing old images..." -ForegroundColor Cyan
docker rmi hiring_backend hiring_frontend -f 2>$null

Write-Host "Pruning build cache..." -ForegroundColor Cyan
docker builder prune -f

Write-Host "Rebuilding from scratch..." -ForegroundColor Cyan
docker compose build --no-cache backend

Write-Host "Starting infrastructure first..." -ForegroundColor Cyan
docker compose up -d mysql redis zookeeper kafka
Write-Host "Waiting 20s for MySQL/Kafka to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 20

Write-Host "Starting backend..." -ForegroundColor Cyan
docker compose up -d backend

Write-Host "Watching backend logs (Ctrl+C to stop watching)..." -ForegroundColor Green
docker compose logs -f backend
