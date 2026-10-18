from job_agent.sources.base import JobAd, merge_ads


def test_merge_by_source_id_and_url():
    ads = [
        JobAd("af", "1", "A", "", "", "https://x/1", ""),
        JobAd("af", "1", "A2", "", "", "https://x/1", ""),
        JobAd("blocket", "9", "B", "", "", "https://y/9", ""),
        JobAd("af", "2", "C", "", "", "https://y/9/", ""),
    ]
    merged = merge_ads(ads)
    urls = {a.url.rstrip("/").lower() for a in merged}
    assert len(merged) == 2
    assert "https://x/1" in urls
    assert "https://y/9" in urls
