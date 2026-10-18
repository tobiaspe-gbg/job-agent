from __future__ import annotations

import html
from datetime import date, datetime
from pathlib import Path

TH = (
    "border:1px solid #ccc;padding:8px 10px;text-align:left;vertical-align:top;"
    "background:#f3f3f3;font-weight:normal;"
)
TD = "border:1px solid #ccc;padding:8px 10px;text-align:left;vertical-align:top;"


def _fmt_found_at(value: str | None) -> str:
    if not value:
        return "-"
    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return html.escape(value)


def _fmt_distance(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.1f} km"


def _fmt_score(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.0f}"


def _fmt_hits(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{int(value)}"


def _row_get(row, key: str):
    if hasattr(row, "keys"):
        return row[key] if key in row.keys() else None
    return row.get(key)


HEADERS = [
    "Title",
    "Employer",
    "Location",
    "Matched role",
    "Score",
    "Source",
    "First found",
    "Keyword hits",
    "Distance",
]


def render_digest_table(rows: list) -> str:
    head = "".join(f'<th style="{TH}">{h}</th>' for h in HEADERS)
    body_rows: list[str] = []
    for row in rows:
        title = html.escape(_row_get(row, "title") or "")
        url = html.escape(_row_get(row, "url") or "")
        title_cell = (
            f'<a href="{url}" style="color:#0645ad;">{title}</a>' if url else title
        )
        cells = [
            title_cell,
            html.escape(_row_get(row, "employer") or ""),
            html.escape(_row_get(row, "location") or ""),
            html.escape(_row_get(row, "role_matched") or ""),
            _fmt_score(_row_get(row, "relevance_score")),
            html.escape(_row_get(row, "source") or ""),
            _fmt_found_at(_row_get(row, "found_at")),
            _fmt_hits(_row_get(row, "keyword_score")),
            _fmt_distance(_row_get(row, "distance_km")),
        ]
        body_rows.append(
            "<tr>" + "".join(f'<td style="{TD}">{c}</td>' for c in cells) + "</tr>"
        )
    if body_rows:
        table_body = "\n".join(body_rows)
    else:
        table_body = (
            f'<tr><td style="{TD}" colspan="{len(HEADERS)}">'
            "No new matching jobs today.</td></tr>"
        )
    return (
        f'<table cellpadding="0" cellspacing="0" border="0" '
        f'style="border-collapse:collapse;width:100%;font-size:14px;font-family:Georgia,serif;">'
        f"\n<thead><tr>{head}</tr></thead>\n<tbody>\n{table_body}\n</tbody>\n</table>"
    )


def render_digest(rows: list, day: date | None = None) -> str:
    day = day or date.today()
    table = render_digest_table(rows)
    return (
        "<!DOCTYPE html>\n<html><head><meta charset='utf-8'>"
        f"<title>Job digest {day.isoformat()}</title></head>"
        '<body style="font-family:Georgia,serif;margin:24px;color:#111;line-height:1.4;">'
        f'<h1 style="font-size:22px;font-weight:normal;">Job digest — {day.isoformat()}</h1>'
        f"{table}"
        "</body></html>\n"
    )


def render_plain_text(rows: list, day: date | None = None) -> str:
    day = day or date.today()
    lines = [f"Job digest — {day.isoformat()}", ""]
    if not rows:
        lines.append("No new matching jobs today.")
        return "\n".join(lines)
    for i, row in enumerate(rows, 1):
        title = _row_get(row, "title") or ""
        url = _row_get(row, "url") or ""
        lines.append(f"{i}. {title}")
        lines.append(f"   Employer: {_row_get(row, 'employer') or '-'}")
        lines.append(f"   Location: {_row_get(row, 'location') or '-'}")
        lines.append(f"   Matched role: {_row_get(row, 'role_matched') or '-'}")
        lines.append(f"   Score: {_fmt_score(_row_get(row, 'relevance_score'))}")
        lines.append(f"   Source: {_row_get(row, 'source') or '-'}")
        lines.append(f"   First found: {_fmt_found_at(_row_get(row, 'found_at'))}")
        lines.append(f"   Keyword hits: {_fmt_hits(_row_get(row, 'keyword_score'))}")
        lines.append(f"   Distance: {_fmt_distance(_row_get(row, 'distance_km'))}")
        if url:
            lines.append(f"   URL: {url}")
        lines.append("")
    return "\n".join(lines)


def write_digest(outbox_dir: Path, rows: list, day: date | None = None) -> Path:
    day = day or date.today()
    outbox_dir.mkdir(parents=True, exist_ok=True)
    path = outbox_dir / f"{day.isoformat()}.html"
    path.write_text(render_digest(rows, day), encoding="utf-8")
    return path
