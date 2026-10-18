from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

import yaml

from job_agent.config import Settings, load_settings
from job_agent.cv import extract_cv_text
from job_agent import db
from job_agent.digest import write_digest
from job_agent.geo import within_radius
from job_agent.mail import load_recipient, send_digest_email
from job_agent.match import cv_skill_terms, loose_keyword_gate, score_with_llm
from job_agent.sources.arbetsformedlingen import fetch_roles as fetch_af
from job_agent.sources.base import merge_ads
from job_agent.sources.blocket import fetch_roles as fetch_blocket

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def load_roles(path: Path) -> list[dict[str, Any]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return list(data.get("roles") or [])


def run_pipeline(settings: Settings | None = None) -> Path | None:
    settings = settings or load_settings()
    roles = load_roles(settings.roles_file)
    cv_text = extract_cv_text(settings.cv_dir) if settings.cv_dir.exists() else ""
    cv_terms = cv_skill_terms(cv_text) if cv_text else []

    ads = []
    if settings.enable_af:
        ads.extend(fetch_af(roles, settings.fetch_max_per_query))
    if settings.enable_blocket:
        ads.extend(fetch_blocket(roles, settings.fetch_max_per_query))

    ads = merge_ads(ads)
    logger.info("Fetched %d unique ads", len(ads))

    ads = within_radius(
        ads,
        home_lat=settings.home_lat,
        home_lon=settings.home_lon,
        radius_km=settings.radius_km,
    )
    logger.info("After %s km radius filter: %d", settings.radius_km, len(ads))

    gated = loose_keyword_gate(ads, roles, cv_terms)
    logger.info("After keyword gate: %d", len(gated))

    keyword_map = { (ad.source, ad.source_id): kw for ad, kw in gated }
    gated_ads = [ad for ad, _ in gated]
    scored = score_with_llm(
        gated_ads,
        roles,
        cv_text,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        base_url=settings.llm_base_url,
    )

    conn = db.connect(settings.db_path)
    for ad, llm_score in scored:
        kw = keyword_map.get((ad.source, ad.source_id), 0.0)
        db.upsert_job(
            conn,
            ad,
            keyword_score=kw,
            llm_score=llm_score,
            relevance_score=llm_score,
        )

    pending = db.pending_digest(conn, settings.score_threshold)
    path = write_digest(settings.outbox_dir, pending)
    if pending:
        _maybe_send_email(settings, pending)
        db.mark_emailed(conn, [(r["source"], r["source_id"]) for r in pending])
    purged = db.purge_older_than(conn, 30)
    conn.close()
    logger.info("Wrote digest %s (%d jobs); purged %d old rows", path, len(pending), purged)
    return path


def _maybe_send_email(settings: Settings, rows: list) -> None:
    if not settings.enable_email:
        logger.info("Email disabled (ENABLE_EMAIL=0)")
        return
    recipient = load_recipient(settings.email_file)
    if not recipient:
        logger.warning("No recipient in %s — skipping email", settings.email_file)
        return
    if settings.resend is None and settings.smtp is None:
        logger.warning(
            "No mail transport configured (set RESEND_API_KEY or SMTP_HOST/SMTP_FROM) — skipping email"
        )
        return
    try:
        send_digest_email(
            rows=rows,
            recipient=recipient,
            resend=settings.resend,
            smtp=settings.smtp if settings.resend is None else None,
        )
    except Exception:
        logger.exception("Failed to send digest email — digest file was still written")


def _load_dotenv() -> None:
    import os

    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def main() -> None:
    _load_dotenv()
    run_pipeline()


if __name__ == "__main__":
    main()
    sys.exit(0)
