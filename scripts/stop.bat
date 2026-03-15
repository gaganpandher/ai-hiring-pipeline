@echo off
:: Stops all AI Hiring Pipeline Docker containers
echo Stopping all services...
docker compose down
echo Done.
pause
