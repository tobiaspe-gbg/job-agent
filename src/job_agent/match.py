from __future__ import annotations

import json
import logging
import re
from typing import Any

from job_agent.sources.base import JobAd

logger = logging.getLogger(__name__)


def all_synonyms(roles: list[dict[str, Any]]) -> list[str]:
    out: list[str] = []
    for role in roles:
        out.extend(role.get("synonyms") or [])
    return out


def loose_keyword_gate(
    ads: list[JobAd],
    roles: list[dict[str, Any]],
    cv_terms: list[str] | None = None,
) -> list[tuple[JobAd, float]]:
    """Keep ads where any synonym (or CV term) appears in title/description."""
    terms = [t.lower() for t in all_synonyms(roles)]
    if cv_terms:
        terms.extend(t.lower() for t in cv_terms if len(t) >= 4)

    kept: list[tuple[JobAd, float]] = []
    for ad in ads:
        hay = f"{ad.title}\n{ad.description}".lower()
        hits = sum(1 for t in terms if t in hay)
        if hits == 0:
            continue
        if not ad.role_matched:
            ad.role_matched = _best_role(ad, roles)
        kept.append((ad, float(hits)))
    return kept


def _best_role(ad: JobAd, roles: list[dict[str, Any]]) -> str:
    hay = f"{ad.title}\n{ad.description}".lower()
    best_name = roles[0]["name"] if roles else ""
    best_hits = -1
    for role in roles:
        hits = sum(1 for s in (role.get("synonyms") or []) if s.lower() in hay)
        if hits > best_hits:
            best_hits = hits
            best_name = role["name"]
    return best_name


def cv_skill_terms(cv_text: str, limit: int = 40) -> list[str]:
    words = re.findall(r"[A-Za-zÅÄÖåäö]{4,}", cv_text.lower())
    seen: set[str] = set()
    out: list[str] = []
    for w in words:
        if w in seen:
            continue
        seen.add(w)
        out.append(w)
        if len(out) >= limit:
            break
    return out


def score_with_llm(
    ads: list[JobAd],
    roles: list[dict[str, Any]],
    cv_text: str,
    *,
    api_key: str,
    model: str,
    base_url: str | None = None,
) -> list[tuple[JobAd, float]]:
    if not ads:
        return []
    if not api_key:
        logger.warning("No LLM API key; assigning keyword-only proxy scores")
        return [(ad, 50.0) for ad in ads]

    from anthropic import Anthropic

    client_kwargs: dict[str, Any] = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url
    client = Anthropic(**client_kwargs)
    role_names = [r["name"] for r in roles]
    results: list[tuple[JobAd, float]] = []

    for i, ad in enumerate(ads, 1):
        prompt = (
            "Score job relevance 0-100 for this candidate.\n"
            f"Roles of interest: {role_names}\n"
            f"CV excerpt:\n{cv_text[:3000]}\n\n"
            f"Job title: {ad.title}\n"
            f"Employer: {ad.employer}\n"
            f"Location: {ad.location}\n"
            f"Description:\n{ad.description[:2500]}\n\n"
            'Reply JSON only: {"score": <number>, "reason": "<short>"}'
        )
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}],
            )
            content = "".join(
                block.text for block in resp.content if getattr(block, "type", None) == "text"
            )
            score = _parse_score(content or "{}")
            logger.info("Scored %d/%d %s/%s -> %.0f", i, len(ads), ad.source, ad.source_id, score)
        except Exception:
            logger.exception("LLM score failed for %s/%s", ad.source, ad.source_id)
            score = 0.0
        results.append((ad, score))
    return results


def _parse_score(content: str) -> float:
    content = content.strip()
    try:
        data = json.loads(content)
        return float(data.get("score", 0))
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", content, re.S)
        if not m:
            return 0.0
        data = json.loads(m.group(0))
        return float(data.get("score", 0))
