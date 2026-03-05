from __future__ import annotations

from digest.models import Article

EXCLUDED_KEYWORDS = {
    "podcast", "video", "multimedia", "episode", "listen", "watch",
    "webinar", "livestream",
}

TOPIC_KEYWORDS = {
    "ai", "artificial intelligence", "machine learning", "deep learning",
    "neural network", "large language model", "llm", "transformer",
    "mathematics", "math", "algebra", "geometry", "topology", "number theory",
    "proof", "conjecture", "theorem",
    "physics", "quantum", "particle", "cosmology", "astrophysics",
    "relativity", "black hole", "dark matter", "dark energy", "gravitational",
    "computer science", "algorithm", "computation",
}


def filter_articles(articles: list[Article]) -> list[Article]:
    return [a for a in articles if _is_valid_article(a)]


def score_relevance(article: Article) -> float:
    text = f"{article.title} {article.description} {' '.join(article.categories)}".lower()
    category_hits = sum(1 for kw in TOPIC_KEYWORDS if kw in {c.lower() for c in article.categories})
    text_hits = sum(1 for kw in TOPIC_KEYWORDS if kw in text)
    return min(category_hits * 2.0 + text_hits * 0.5, 10.0)


def _is_valid_article(article: Article) -> bool:
    if article.content_type != "article":
        return False
    text = f"{article.title} {article.url}".lower()
    return not any(kw in text for kw in EXCLUDED_KEYWORDS)
