from __future__ import annotations

import math

from job_agent.sources.base import JobAd

# Prebendegatan 6, Göteborg (approx; street coords near Prebendegatan 2)
HOME_LAT = 57.705034
HOME_LON = 11.910129
DEFAULT_RADIUS_KM = 30.0

EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    rlat1, rlon1, rlat2, rlon2 = map(math.radians, (lat1, lon1, lat2, lon2))
    dlat = rlat2 - rlat1
    dlon = rlon2 - rlon1
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def within_radius(
    ads: list[JobAd],
    *,
    home_lat: float = HOME_LAT,
    home_lon: float = HOME_LON,
    radius_km: float = DEFAULT_RADIUS_KM,
) -> list[JobAd]:
    """Keep ads with coordinates within radius_km of home. Drop ads without coords."""
    kept: list[JobAd] = []
    for ad in ads:
        if ad.lat is None or ad.lon is None:
            continue
        dist = haversine_km(home_lat, home_lon, ad.lat, ad.lon)
        if dist <= radius_km:
            ad.distance_km = dist
            kept.append(ad)
    return kept
