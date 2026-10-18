from pathlib import Path

from job_agent.digest import write_digest


def test_digest_visible_in_browser(tmp_path: Path):
    pytest = __import__("pytest")
    playwright = pytest.importorskip("playwright.sync_api")

    rows = [
        {
            "title": "Hotellreceptionist",
            "url": "https://example.com/job/2",
            "employer": "Hotel",
            "location": "Göteborg",
            "role_matched": "front-desk at hotels or bars",
            "source": "blocket",
            "relevance_score": 75,
            "found_at": "2026-10-18T10:00:00+00:00",
            "keyword_score": 2,
            "distance_km": 3.5,
        }
    ]
    path = write_digest(tmp_path, rows)
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(path.as_uri())
        assert page.get_by_role("table").is_visible()
        assert page.get_by_text("Hotellreceptionist").is_visible()
        assert page.get_by_role("link", name="Hotellreceptionist").get_attribute("href") == (
            "https://example.com/job/2"
        )
        assert page.get_by_text("blocket").is_visible()
        assert page.get_by_text("3.5 km").is_visible()
        browser.close()
