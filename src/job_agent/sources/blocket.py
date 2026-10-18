from __future__ import annotations

import logging
import re
import time
from typing import Any
from urllib.parse import quote, urljoin

from job_agent.sources.base import JobAd

logger = logging.getLogger(__name__)

BASE_URL = "https://jobb.blocket.se"
SEARCH_PATH = "/lediga-jobb"

# Selectors isolated here so site markup changes are easy to fix.
CARD_SELECTOR = "article a[href*='/lediga-jobb/'], a[href*='/annons/']"
TITLE_SELECTOR = "h1, h2"
EMPLOYER_SELECTOR = "[data-testid='employer'], .employer, .company"
LOCATION_SELECTOR = "[data-testid='location'], .location"
DESC_SELECTOR = "[data-testid='description'], .job-description, article, main"


def parse_listing_html(html: str, role: str, base_url: str = BASE_URL) -> list[JobAd]:
    """Parse Blocket search results HTML into JobAds (title/url from cards)."""
    from playwright.sync_api import sync_playwright

    ads: list[JobAd] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(html, wait_until="domcontentloaded")
        links = page.query_selector_all(CARD_SELECTOR)
        seen: set[str] = set()
        for link in links:
            href = link.get_attribute("href") or ""
            title = (link.inner_text() or "").strip()
            if not href or not title:
                continue
            url = urljoin(base_url, href)
            if url in seen:
                continue
            seen.add(url)
            source_id = _id_from_url(url)
            ads.append(
                JobAd(
                    source="blocket",
                    source_id=source_id,
                    title=title.split("\n")[0].strip(),
                    employer="",
                    location="",
                    url=url,
                    description=title,
                    role_matched=role,
                )
            )
        browser.close()
    return ads


def parse_listing_html_simple(html: str, role: str, base_url: str = BASE_URL) -> list[JobAd]:
    """Regex/simple parse for fixtures without launching a browser."""
    ads: list[JobAd] = []
    seen: set[str] = set()
    for match in re.finditer(
        r'<a[^>]+href="([^"]*(?:/lediga-jobb/|/annons/)[^"]*)"[^>]*>(.*?)</a>',
        html,
        flags=re.I | re.S,
    ):
        href, inner = match.group(1), match.group(2)
        title = re.sub(r"<[^>]+>", " ", inner)
        title = re.sub(r"\s+", " ", title).strip()
        if not title:
            continue
        url = urljoin(base_url, href)
        if url in seen:
            continue
        seen.add(url)
        ads.append(
            JobAd(
                source="blocket",
                source_id=_id_from_url(url),
                title=title,
                employer="",
                location="",
                url=url,
                description=title,
                role_matched=role,
            )
        )
    return ads


def _id_from_url(url: str) -> str:
    m = re.search(r"/(\d+)(?:/?$|\?)", url)
    if m:
        return m.group(1)
    return re.sub(r"\W+", "_", url)[-64:]


def fetch_roles(
    roles: list[dict[str, Any]],
    max_per_query: int,
    *,
    live: bool = True,
) -> list[JobAd]:
    if not live:
        return []

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.error("Playwright not installed; skipping Blocket")
        return []

    ads: list[JobAd] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        for role in roles:
            name = role["name"]
            for synonym in role.get("synonyms") or []:
                url = f"{BASE_URL}{SEARCH_PATH}?q={quote(synonym)}"
                logger.info("Blocket search: role=%s q=%s", name, synonym)
                try:
                    resp = page.goto(url, wait_until="domcontentloaded", timeout=20000)
                    if resp is None or resp.status >= 400:
                        logger.warning(
                            "Blocket unavailable for q=%s status=%s",
                            synonym,
                            None if resp is None else resp.status,
                        )
                        continue
                    html = page.content()
                    batch = parse_listing_html_simple(html, name)
                    ads.extend(batch[:max_per_query])
                    time.sleep(0.5)
                except Exception:
                    logger.exception("Blocket search failed for q=%s", synonym)
        browser.close()
    return ads
