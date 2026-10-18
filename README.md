# Job Finder Agent

Daily wide search of Swedish jobs from Arbetsförmedlingen (API) and Blocket Jobb (Playwright), kept only if within **30 km of Prebendegatan 6, Göteborg**, then hybrid-scored against roles in `roles.yaml` and PDFs in `CV/`. Results land in SQLite (`data/jobs.db`) and an HTML digest stub in `outbox/`.

## Setup

```bash
cp .env.example .env
cp .email.example .email
# set OPENROUTER_API_KEY (or ANTHROPIC_API_KEY) for Claude scoring
# put the digest recipient address in .email
# set RESEND_API_KEY in .env to send mail (preferred); SMTP_* works as fallback
uv sync --extra dev
uv run playwright install chromium
```

## Run once

```bash
uv run job-agent
```

## Docker

```bash
./scripts/start.sh   # Mac/Linux
./scripts/stop.sh
# Windows: scripts\start.bat / scripts\stop.bat or start.ps1 / stop.ps1
```

## Note on Blocket Jobb

Blocket Jobb was shut down in December 2024. The Blocket source remains wired (fixture-tested); live fetches may return nothing until the site or a replacement is available. Disable with `ENABLE_BLOCKET=0`.

## Docs

See [docs/PLAN.md](docs/PLAN.md).
