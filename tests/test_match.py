from job_agent.match import loose_keyword_gate
from job_agent.sources.base import JobAd


ROLES = [
    {
        "name": "waiting staff at restaurants",
        "synonyms": ["servitör", "waiter"],
    },
    {
        "name": "front-desk at hotels or bars",
        "synonyms": ["receptionist"],
    },
]


def test_loose_keyword_gate_keeps_synonym_hits():
    ads = [
        JobAd("af", "1", "Servitör sökes", "A", "Malmö", "https://x/1", "Vi söker servitör"),
        JobAd("af", "2", "Java developer", "B", "Stockholm", "https://x/2", "Spring Boot"),
    ]
    kept = loose_keyword_gate(ads, ROLES)
    assert len(kept) == 1
    assert kept[0][0].source_id == "1"
    assert kept[0][1] >= 1


def test_loose_keyword_gate_or_match():
    ads = [
        JobAd("af", "3", "Receptionist", "C", "Göteborg", "https://x/3", "Hotel front desk"),
    ]
    kept = loose_keyword_gate(ads, ROLES)
    assert len(kept) == 1
    assert kept[0][0].role_matched == "front-desk at hotels or bars"
