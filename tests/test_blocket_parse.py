from pathlib import Path

from job_agent.sources.blocket import parse_listing_html_simple

FIXTURE = Path(__file__).parent / "fixtures" / "blocket_listing.html"


def test_parse_blocket_fixture():
    html = FIXTURE.read_text(encoding="utf-8")
    ads = parse_listing_html_simple(html, "waiting staff at restaurants")
    assert len(ads) == 2
    assert ads[0].source == "blocket"
    assert "Servitör" in ads[0].title
    assert ads[0].source_id == "12345"
    assert ads[1].source_id == "67890"
