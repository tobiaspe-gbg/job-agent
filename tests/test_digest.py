from pathlib import Path

from job_agent.digest import render_digest, write_digest


def test_render_digest_table_fields():
    rows = [
        {
            "title": "Servitör",
            "url": "https://example.com/job/1",
            "employer": "Cafe",
            "location": "Göteborg",
            "role_matched": "waiting staff at restaurants",
            "source": "af",
            "relevance_score": 88,
            "found_at": "2026-10-18T12:00:00+00:00",
            "keyword_score": 3,
            "distance_km": 4.2,
        }
    ]
    html = render_digest(rows)
    assert "<table" in html
    assert "First found" in html
    assert "Keyword hits" in html
    assert "Distance" in html
    assert "Servitör" in html
    assert "https://example.com/job/1" in html
    assert "af" in html
    assert "88" in html
    assert "3" in html
    assert "4.2 km" in html
    assert "2026-10-18 12:00" in html


def test_write_digest(tmp_path: Path):
    path = write_digest(tmp_path, [])
    assert path.exists()
    assert "No new matching jobs" in path.read_text(encoding="utf-8")
