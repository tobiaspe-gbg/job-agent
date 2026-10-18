from pathlib import Path

from job_agent import db
from job_agent.sources.base import JobAd


def test_upsert_dedup_and_pending(tmp_path: Path):
    conn = db.connect(tmp_path / "jobs.db")
    ad = JobAd("af", "1", "Servitör", "Cafe", "Malmö", "https://af/1", "servitör")
    db.upsert_job(conn, ad, keyword_score=2, llm_score=80, relevance_score=80)
    db.upsert_job(conn, ad, keyword_score=3, llm_score=85, relevance_score=85)

    rows = db.pending_digest(conn, 60)
    assert len(rows) == 1
    assert rows[0]["relevance_score"] == 85

    db.mark_emailed(conn, [("af", "1")])
    assert db.pending_digest(conn, 60) == []


def test_cross_source_keys(tmp_path: Path):
    conn = db.connect(tmp_path / "jobs.db")
    db.upsert_job(
        conn,
        JobAd("af", "1", "A", "", "", "https://af/1", ""),
        keyword_score=1,
        llm_score=70,
        relevance_score=70,
    )
    db.upsert_job(
        conn,
        JobAd("blocket", "1", "B", "", "", "https://blocket/1", ""),
        keyword_score=1,
        llm_score=70,
        relevance_score=70,
    )
    assert len(db.pending_digest(conn, 60)) == 2
