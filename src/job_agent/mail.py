from __future__ import annotations

import logging
import re
import smtplib
from dataclasses import dataclass
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import httpx

from job_agent.digest import render_digest, render_plain_text

logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
RESEND_URL = "https://api.resend.com/emails"


@dataclass(frozen=True)
class SmtpConfig:
    host: str
    port: int
    user: str
    password: str
    from_addr: str
    use_tls: bool = True


@dataclass(frozen=True)
class ResendConfig:
    api_key: str
    from_addr: str


def load_recipient(email_file: Path) -> str | None:
    if not email_file.exists():
        return None
    for raw in email_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line and not line.startswith("@"):
            key, _, val = line.partition(":")
            if key.strip().lower() in {"to", "recipient", "email"}:
                line = val.strip()
        if EMAIL_RE.match(line):
            return line
    return None


def send_digest_email(
    *,
    rows: list,
    recipient: str,
    day: date | None = None,
    resend: ResendConfig | None = None,
    smtp: SmtpConfig | None = None,
) -> None:
    day = day or date.today()
    subject = f"Job digest — {day.isoformat()} ({len(rows)} jobs)"
    html_body = render_digest(rows, day)
    text_body = render_plain_text(rows, day)

    if resend is not None:
        _send_resend(
            api_key=resend.api_key,
            from_addr=resend.from_addr,
            recipient=recipient,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
        )
        return
    if smtp is not None:
        _send_smtp(
            smtp=smtp,
            recipient=recipient,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
        )
        return
    raise ValueError("No email transport configured (Resend or SMTP)")


def _send_resend(
    *,
    api_key: str,
    from_addr: str,
    recipient: str,
    subject: str,
    html_body: str,
    text_body: str,
) -> None:
    logger.info("Sending digest email to %s via Resend", recipient)
    resp = httpx.post(
        RESEND_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "from": from_addr,
            "to": [recipient],
            "subject": subject,
            "html": html_body,
            "text": text_body,
        },
        timeout=30.0,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"Resend error {resp.status_code}: {resp.text}")
    logger.info("Email sent to %s (Resend id=%s)", recipient, resp.json().get("id"))


def _send_smtp(
    *,
    smtp: SmtpConfig,
    recipient: str,
    subject: str,
    html_body: str,
    text_body: str,
) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp.from_addr
    msg["To"] = recipient
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    logger.info("Sending digest email to %s via %s:%s", recipient, smtp.host, smtp.port)
    with smtplib.SMTP(smtp.host, smtp.port, timeout=30) as server:
        if smtp.use_tls:
            server.starttls()
        if smtp.user:
            server.login(smtp.user, smtp.password)
        server.sendmail(smtp.from_addr, [recipient], msg.as_string())
    logger.info("Email sent to %s", recipient)
