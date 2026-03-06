from __future__ import annotations

from datetime import datetime, timezone

from digest.filter import score_relevance
from digest.models import Article

PRIORITY_KEYWORDS = {
    "breakthrough", "discovery", "new", "first", "invention",
    "novel", "unprecedented", "revolutionary", "advance",
    "solved", "proves", "disproves", "innovation",
    "state-of-the-art", "outperforms",
}

# Curated editorial sources get a strong bonus over raw preprints
SOURCE_BONUS = {
    "quanta": 8.0,
    "nature": 6.0,
    "arxiv": 0.0,
}

# Cap total score for arXiv to prevent keyword-dense abstracts from dominating
ARXIV_SCORE_CAP = 10.0


def rank_and_select(articles: list[Article], top_n: int = 10) -> list[Article]:
    now = datetime.now(timezone.utc)
    for article in articles:
        article.relevance_score = _compute_score(article, now)
    articles.sort(key=lambda a: a.relevance_score, reverse=True)
    return articles[:top_n]


def _compute_score(article: Article, now: datetime) -> float:
    relevance = score_relevance(article)

    hours_old = max((now - article.published).total_seconds() / 3600, 0)
    recency_bonus = max(3.0 - hours_old / 56.0, 0.0)

    text = f"{article.title} {article.description}".lower()
    priority_hits = sum(1 for kw in PRIORITY_KEYWORDS if kw in text)
    priority_bonus = min(priority_hits * 1.0, 5.0)

    source_bonus = SOURCE_BONUS.get(article.source, 0.0)

    score = relevance + recency_bonus + priority_bonus + source_bonus

    if article.source == "arxiv":
        score = min(score, ARXIV_SCORE_CAP)

    return score
