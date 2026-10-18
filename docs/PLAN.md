# Job Finder Agent — Plan

## Decisions (locked)

- **Job sources (v1):** (1) Arbetsförmedlingen JobSearch API; (2) Blocket Jobb via Playwright scrape. Shared normalizer into one pipeline after fetch.
- **Blocket status:** Blocket Jobb shut down December 2024; live scrapes may return empty. Parser/fixtures remain; set `ENABLE_BLOCKET=0` to skip.
- **Initial search (wide):** Many synonym queries per role (Swedish + English), pagination, dedupe within and across sources.
- **Email:** HTML + plain-text digest table emailed via SMTP to the address in `.email`. Also written to `outbox/`.
- **Scoring:** Hybrid — loose keyword OR-gate, then LLM relevance score. Volume comes from wide fetch.
- **CV:** PDF(s) in `CV/` parsed to plain text.
- **Roles:** automotive assembly; breakfast/bar hostess; event staff; housekeeping; front-desk; waiting staff.
- **Location:** Only jobs within **30 km** of Prebendegatan 6, Göteborg (haversine on workplace coordinates). Ads without coordinates are dropped.

## Architecture

Daily runner fetches from AF + Blocket → merge/dedupe → **30 km geo filter** → loose keyword gate → LLM score → SQLite → HTML outbox stub.

## Data model

Table `jobs` with PK `(source, source_id)`, scores, `found_at`, `emailed_at`. 30-day purge by `found_at`. Never re-digest if `emailed_at` is set. Also dedupe by canonical URL within a run.

## Pipeline

1. Load roles + CV text.
2. Wide fetch both sources with synonym queries; normalize to `JobAd` (incl. lat/lon when available).
3. Keep only ads within `RADIUS_KM` (default 30) of home coords.
4. Loose keyword OR-gate.
5. LLM score; keep `>= SCORE_THRESHOLD` (default 60).
6. Upsert; select unscored-for-digest rows that pass.
7. Write `outbox/YYYY-MM-DD.html`; set `emailed_at`.
8. Delete rows older than 30 days.

## Out of scope (for now)

- Real SMTP
- Boards beyond AF + Blocket Jobb
- Web UI
