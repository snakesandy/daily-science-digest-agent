from __future__ import annotations

from datetime import datetime, timezone

from digest.filter import score_relevance
from digest.models import Article

PRIORITY_KEYWORDS = {
    "discovery", "breakthrough", "new", "first", "invention",
    "implications", "novel", "unprecedented", "revolutionary",
    "surprising", "unexpected",
}


def rank_and_select(articles: list[Article], top_n: int = 10) -> list[Article]:
    now = datetime.now(timezone.utc)
    for article in articles:
        article.relevance_score = _compute_score(article, now)
    articles.sort(key=lambda a: a.relevance_score, reverse=True)
    return articles[:top_n]


def _compute_score(article: Article, now: datetime) -> float:
    relevance = score_relevance(article)

    hours_old = max((now - article.published).total_seconds() / 3600, 0)
    recency_bonus = max(3.0 - hours_old / 8.0, 0.0)

    text = f"{article.title} {article.description}".lower()
    priority_hits = sum(1 for kw in PRIORITY_KEYWORDS if kw in text)
    priority_bonus = min(priority_hits * 1.0, 5.0)

    return relevance + recency_bonus + priority_bonus
