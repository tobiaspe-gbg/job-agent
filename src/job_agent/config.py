from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from job_agent.geo import DEFAULT_RADIUS_KM, HOME_LAT, HOME_LON
from job_agent.mail import ResendConfig, SmtpConfig

ROOT = Path(__file__).resolve().parents[2]


def _env_bool(name: str, default: bool = True) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    root: Path
    data_dir: Path
    outbox_dir: Path
    cv_dir: Path
    roles_file: Path
    email_file: Path
    db_path: Path
    llm_api_key: str
    llm_model: str
    llm_base_url: str | None
    score_threshold: int
    fetch_max_per_query: int
    enable_af: bool
    enable_blocket: bool
    enable_email: bool
    home_lat: float
    home_lon: float
    radius_km: float
    resend: ResendConfig | None
    smtp: SmtpConfig | None


def load_settings() -> Settings:
    root = Path(os.getenv("JOB_AGENT_ROOT", str(ROOT)))
    data_dir = root / os.getenv("DATA_DIR", "data")
    outbox_dir = root / os.getenv("OUTBOX_DIR", "outbox")
    cv_dir = root / os.getenv("CV_DIR", "CV")
    roles_file = root / os.getenv("ROLES_FILE", "roles.yaml")
    email_file = root / os.getenv("EMAIL_FILE", ".email")
    data_dir.mkdir(parents=True, exist_ok=True)
    outbox_dir.mkdir(parents=True, exist_ok=True)

    openrouter = os.getenv("OPENROUTER_API_KEY", "").strip()
    anthropic = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if openrouter:
        llm_api_key = openrouter
        llm_base_url = "https://openrouter.ai/api"
        llm_model = os.getenv("CLAUDE_MODEL", "anthropic/claude-haiku-4.5")
    else:
        llm_api_key = anthropic
        llm_base_url = None
        llm_model = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5")

    resend_key = os.getenv("RESEND_API_KEY", "").strip()
    resend: ResendConfig | None = None
    if resend_key:
        resend = ResendConfig(
            api_key=resend_key,
            from_addr=os.getenv("RESEND_FROM", "Job Finder <onboarding@resend.dev>").strip(),
        )

    smtp_host = os.getenv("SMTP_HOST", "").strip()
    smtp_from = os.getenv("SMTP_FROM", "").strip()
    smtp: SmtpConfig | None = None
    if smtp_host and smtp_from:
        smtp = SmtpConfig(
            host=smtp_host,
            port=int(os.getenv("SMTP_PORT", "587")),
            user=os.getenv("SMTP_USER", "").strip(),
            password=os.getenv("SMTP_PASSWORD", "").strip(),
            from_addr=smtp_from,
            use_tls=_env_bool("SMTP_TLS", True),
        )

    return Settings(
        root=root,
        data_dir=data_dir,
        outbox_dir=outbox_dir,
        cv_dir=cv_dir,
        roles_file=roles_file,
        email_file=email_file,
        db_path=data_dir / "jobs.db",
        llm_api_key=llm_api_key,
        llm_model=llm_model,
        llm_base_url=llm_base_url,
        score_threshold=int(os.getenv("SCORE_THRESHOLD", "60")),
        fetch_max_per_query=int(os.getenv("FETCH_MAX_PER_QUERY", "100")),
        enable_af=_env_bool("ENABLE_AF", True),
        enable_blocket=_env_bool("ENABLE_BLOCKET", True),
        enable_email=_env_bool("ENABLE_EMAIL", True),
        home_lat=float(os.getenv("HOME_LAT", str(HOME_LAT))),
        home_lon=float(os.getenv("HOME_LON", str(HOME_LON))),
        radius_km=float(os.getenv("RADIUS_KM", str(DEFAULT_RADIUS_KM))),
        resend=resend,
        smtp=smtp,
    )
