@echo off
cd /d "%~dp0.."
docker compose up -d --build
echo job-agent started (docker compose)
