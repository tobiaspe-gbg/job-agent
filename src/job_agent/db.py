from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from job_agent.sources.base import JobAd


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    init_schema(conn)
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            source TEXT NOT NULL,
            source_id TEXT NOT NULL,
            title TEXT NOT NULL,
            employer TEXT,
            location TEXT,
            url TEXT NOT NULL,
            description TEXT,
            role_matched TEXT,
            keyword_score REAL,
            llm_score REAL,
            relevance_score REAL,
            distance_km REAL,
            found_at TEXT NOT NULL,
            emailed_at TEXT,
            PRIMARY KEY (source, source_id)
        )
        """
    )
    cols = {row[1] for row in conn.execute("PRAGMA table_info(jobs)")}
    if "distance_km" not in cols:
        conn.execute("ALTER TABLE jobs ADD COLUMN distance_km REAL")
    conn.commit()


def upsert_job(
    conn: sqlite3.Connection,
    ad: JobAd,
    *,
    keyword_score: float,
    llm_score: float,
    relevance_score: float,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO jobs (
            source, source_id, title, employer, location, url, description,
            role_matched, keyword_score, llm_score, relevance_score, distance_km, found_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source, source_id) DO UPDATE SET
            title=excluded.title,
            employer=excluded.employer,
            location=excluded.location,
            url=excluded.url,
            description=excluded.description,
            role_matched=excluded.role_matched,
            keyword_score=excluded.keyword_score,
            llm_score=excluded.llm_score,
            relevance_score=excluded.relevance_score,
            distance_km=excluded.distance_km
        """,
        (
            ad.source,
            ad.source_id,
            ad.title,
            ad.employer,
            ad.location,
            ad.url,
            ad.description,
            ad.role_matched,
            keyword_score,
            llm_score,
            relevance_score,
            ad.distance_km,
            now,
        ),
    )
    conn.commit()


def pending_digest(conn: sqlite3.Connection, min_score: float) -> list[sqlite3.Row]:
    cur = conn.execute(
        """
        SELECT * FROM jobs
        WHERE emailed_at IS NULL AND relevance_score >= ?
        ORDER BY relevance_score DESC
        """,
        (min_score,),
    )
    return list(cur.fetchall())


def recent_digest(conn: sqlite3.Connection, min_score: float) -> list[sqlite3.Row]:
    """Jobs already scored for today's digest (including emailed), for re-render."""
    cur = conn.execute(
        """
        SELECT * FROM jobs
        WHERE relevance_score >= ?
        ORDER BY relevance_score DESC
        """,
        (min_score,),
    )
    return list(cur.fetchall())


def mark_emailed(conn: sqlite3.Connection, keys: list[tuple[str, str]]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn.executemany(
        "UPDATE jobs SET emailed_at = ? WHERE source = ? AND source_id = ?",
        [(now, source, source_id) for source, source_id in keys],
    )
    conn.commit()


def purge_older_than(conn: sqlite3.Connection, days: int = 30) -> int:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    cur = conn.execute("DELETE FROM jobs WHERE found_at < ?", (cutoff,))
    conn.commit()
    return cur.rowcount
