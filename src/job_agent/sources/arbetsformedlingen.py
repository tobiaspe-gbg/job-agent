from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote

import httpx

from job_agent.sources.base import JobAd

logger = logging.getLogger(__name__)

SEARCH_URL = "https://jobsearch.api.jobtechdev.se/search"
PAGE_SIZE = 100


def _location(hit: dict[str, Any]) -> str:
    addr = hit.get("workplace_address") or {}
    parts = [addr.get("municipality"), addr.get("region"), addr.get("city")]
    return ", ".join(p for p in parts if p) or ""


def _coords(hit: dict[str, Any]) -> tuple[float | None, float | None]:
    addr = hit.get("workplace_address") or {}
    coords = addr.get("coordinates")
    # AF returns [longitude, latitude]
    if isinstance(coords, (list, tuple)) and len(coords) >= 2:
        lon, lat = coords[0], coords[1]
        if lon is None or lat is None:
            return None, None
        return float(lat), float(lon)
    return None, None


def _normalize(hit: dict[str, Any], role: str) -> JobAd:
    desc = (hit.get("description") or {}).get("text") or ""
    employer = (hit.get("employer") or {}).get("name") or ""
    lat, lon = _coords(hit)
    return JobAd(
        source="af",
        source_id=str(hit["id"]),
        title=hit.get("headline") or "",
        employer=employer,
        location=_location(hit),
        url=hit.get("webpage_url") or f"https://arbetsformedlingen.se/platsbanken/annonser/{hit['id']}",
        description=desc,
        role_matched=role,
        lat=lat,
        lon=lon,
    )


def fetch_query(client: httpx.Client, query: str, role: str, max_results: int) -> list[JobAd]:
    ads: list[JobAd] = []
    offset = 0
    while len(ads) < max_results:
        limit = min(PAGE_SIZE, max_results - len(ads))
        resp = client.get(
            SEARCH_URL,
            params={"q": query, "limit": limit, "offset": offset},
            timeout=30.0,
        )
        resp.raise_for_status()
        data = resp.json()
        hits = data.get("hits") or []
        if not hits:
            break
        for hit in hits:
            ads.append(_normalize(hit, role))
        offset += len(hits)
        total = (data.get("total") or {}).get("value", 0)
        if offset >= total:
            break
    return ads


def fetch_roles(roles: list[dict[str, Any]], max_per_query: int) -> list[JobAd]:
    ads: list[JobAd] = []
    with httpx.Client(headers={"Accept": "application/json"}) as client:
        for role in roles:
            name = role["name"]
            for synonym in role.get("synonyms") or []:
                logger.info("AF search: role=%s q=%s", name, synonym)
                try:
                    ads.extend(fetch_query(client, synonym, name, max_per_query))
                except httpx.HTTPError:
                    logger.exception("AF search failed for q=%s", synonym)
    return ads


def search_url(query: str) -> str:
    return f"{SEARCH_URL}?q={quote(query)}&limit=1"
