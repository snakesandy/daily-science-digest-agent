from datetime import datetime, timezone

from digest.filter import filter_articles, score_relevance
from digest.models import Article


def _make_article(**kwargs):
    defaults = dict(
        title="Test Article",
        url="https://example.com/test",
        source="quanta",
        published=datetime(2026, 3, 5, tzinfo=timezone.utc),
        categories=[],
        description="",
        content_type="article",
    )
    defaults.update(kwargs)
    return Article(**defaults)


def test_filter_keeps_articles():
    articles = [_make_article(title="Quantum Discovery")]
    result = filter_articles(articles)
    assert len(result) == 1


def test_filter_excludes_podcasts():
    articles = [_make_article(content_type="podcast")]
    assert filter_articles(articles) == []


def test_filter_excludes_videos():
    articles = [_make_article(content_type="video")]
    assert filter_articles(articles) == []


def test_filter_excludes_podcast_in_url():
    articles = [_make_article(url="https://example.com/podcast/episode-1")]
    assert filter_articles(articles) == []


def test_filter_excludes_video_in_title():
    articles = [_make_article(title="Watch: New Physics Video")]
    assert filter_articles(articles) == []


def test_score_relevance_high_for_ai():
    article = _make_article(
        title="New AI Breakthrough in Deep Learning",
        description="A neural network achieves new results",
        categories=["Computer Science"],
    )
    score = score_relevance(article)
    assert score > 0


def test_score_relevance_high_for_physics():
    article = _make_article(
        title="Quantum Physics Discovery",
        categories=["Physics"],
    )
    score = score_relevance(article)
    assert score > 0


def test_score_relevance_zero_for_unrelated():
    article = _make_article(
        title="New Cooking Recipe",
        description="A delicious pasta dish",
        categories=["Food"],
    )
    score = score_relevance(article)
    assert score == 0


def test_score_capped_at_10():
    article = _make_article(
        title="AI quantum physics math deep learning neural network algorithm",
        description="machine learning computer science topology algebra geometry",
        categories=["Physics", "Mathematics", "Computer Science"],
    )
    score = score_relevance(article)
    assert score <= 10.0
