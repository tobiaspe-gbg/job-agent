from job_agent.geo import haversine_km, within_radius
from job_agent.sources.base import JobAd

HOME_LAT = 57.705034
HOME_LON = 11.910129


def test_haversine_same_point():
    assert haversine_km(HOME_LAT, HOME_LON, HOME_LAT, HOME_LON) < 0.01


def test_within_radius_keeps_gothenburg_drops_far():
    near = JobAd(
        "af",
        "1",
        "Near",
        "",
        "Göteborg",
        "https://x/1",
        "",
        lat=57.7089,
        lon=11.9746,  # central Göteborg ~4 km
    )
    far = JobAd(
        "af",
        "2",
        "Far",
        "",
        "Malmö",
        "https://x/2",
        "",
        lat=55.6050,
        lon=13.0038,
    )
    no_coords = JobAd("af", "3", "Unknown", "", "", "https://x/3", "")
    kept = within_radius([near, far, no_coords], home_lat=HOME_LAT, home_lon=HOME_LON, radius_km=30)
    assert [a.source_id for a in kept] == ["1"]
    assert kept[0].distance_km is not None
    assert kept[0].distance_km < 10
