from datetime import datetime, timezone

from digest.models import Article
from digest.ranker import rank_and_select


def _make_article(title="Test", description="", categories=None, hours_ago=0):
    pub = datetime(2026, 3, 5, 12 - hours_ago, 0, tzinfo=timezone.utc)
    return Article(
        title=title,
        url=f"https://example.com/{title.lower().replace(' ', '-')}",
        source="quanta",
        published=pub,
        categories=categories or [],
        description=description,
        content_type="article",
    )


def test_returns_top_10():
    articles = [_make_article(title=f"Article {i}") for i in range(20)]
    result = rank_and_select(articles, top_n=10)
    assert len(result) == 10


def test_returns_fewer_if_not_enough():
    articles = [_make_article(title=f"Article {i}") for i in range(3)]
    result = rank_and_select(articles, top_n=10)
    assert len(result) == 3


def test_high_relevance_ranked_first():
    low = _make_article(title="Cooking Recipe", description="A delicious meal")
    high = _make_article(
        title="New Quantum Discovery Breakthrough",
        description="Physicists found a novel quantum effect",
        categories=["Physics"],
    )
    result = rank_and_select([low, high], top_n=2)
    assert result[0].title == high.title


def test_priority_keywords_boost():
    normal = _make_article(title="Physics Research", categories=["Physics"])
    boosted = _make_article(
        title="Breakthrough Discovery in Physics",
        categories=["Physics"],
    )
    result = rank_and_select([normal, boosted], top_n=2)
    assert result[0].title == boosted.title
