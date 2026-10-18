from __future__ import annotations

from dataclasses import dataclass


@dataclass
class JobAd:
    source: str
    source_id: str
    title: str
    employer: str
    location: str
    url: str
    description: str
    role_matched: str = ""
    lat: float | None = None
    lon: float | None = None
    distance_km: float | None = None


def merge_ads(ads: list[JobAd]) -> list[JobAd]:
    """Dedupe by (source, source_id), then by canonical url."""
    by_key: dict[tuple[str, str], JobAd] = {}
    for ad in ads:
        by_key[(ad.source, ad.source_id)] = ad

    by_url: dict[str, JobAd] = {}
    for ad in by_key.values():
        url = ad.url.rstrip("/").lower()
        if url in by_url:
            continue
        by_url[url] = ad
    return list(by_url.values())
