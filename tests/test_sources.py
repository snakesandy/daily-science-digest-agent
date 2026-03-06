from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import feedparser

from digest.sources.arxiv import ArxivSource
from digest.sources.nature import NatureSource
from digest.sources.quanta import QuantaSource

FIXTURES = Path(__file__).parent / "fixtures"


def test_quanta_parses_feed():
    feed_xml = (FIXTURES / "quanta_feed.xml").read_text()
    since = datetime(2026, 3, 4, 0, 0, tzinfo=timezone.utc)

    with patch("digest.sources.quanta.feedparser") as mock_fp:
        mock_fp.parse.return_value = feedparser.parse(feed_xml)
        source = QuantaSource()
        articles = source.fetch(since)

    # Should get 4 articles (2 Mar 5 articles + 1 Mar 4 article + 1 podcast, old Feb one filtered)
    assert len(articles) == 4
    # Check podcast is detected
    podcast = [a for a in articles if a.content_type == "podcast"]
    assert len(podcast) == 1
    assert "Joy of Why" in podcast[0].title


def test_quanta_filters_old_articles():
    feed_xml = (FIXTURES / "quanta_feed.xml").read_text()
    since = datetime(2026, 3, 5, 0, 0, tzinfo=timezone.utc)

    with patch("digest.sources.quanta.feedparser") as mock_fp:
        mock_fp.parse.return_value = feedparser.parse(feed_xml)
        source = QuantaSource()
        articles = source.fetch(since)

    # Only Mar 5 articles
    assert all(a.published.day == 5 for a in articles)


def test_nature_parses_feed():
    feed_xml = (FIXTURES / "nature_feed.xml").read_text()
    since = datetime(2026, 3, 2, 0, 0, tzinfo=timezone.utc)

    with patch("digest.sources.nature.feedparser") as mock_fp:
        mock_fp.parse.return_value = feedparser.parse(feed_xml)
        source = NatureSource()
        articles = source.fetch(since)

    # 3 articles from Mar 2+ (2 real + 1 podcast), old Feb one filtered
    assert len(articles) == 3
    podcast = [a for a in articles if a.content_type != "article"]
    assert len(podcast) == 1


def test_nature_filters_old_articles():
    feed_xml = (FIXTURES / "nature_feed.xml").read_text()
    since = datetime(2026, 3, 4, 0, 0, tzinfo=timezone.utc)

    with patch("digest.sources.nature.feedparser") as mock_fp:
        mock_fp.parse.return_value = feedparser.parse(feed_xml)
        source = NatureSource()
        articles = source.fetch(since)

    assert len(articles) == 1
    assert "quantum" in articles[0].title.lower()


def test_arxiv_parses_feed():
    feed_xml = (FIXTURES / "arxiv_feed.xml").read_text()
    since = datetime(2026, 3, 2, 0, 0, tzinfo=timezone.utc)

    with patch("digest.sources.arxiv.feedparser") as mock_fp:
        mock_fp.parse.return_value = feedparser.parse(feed_xml)
        source = ArxivSource()
        articles = source.fetch(since)

    # 2 recent articles, old one filtered
    assert len(articles) == 2
    # arXiv title cleaning
    assert "arXiv:" not in articles[0].title


def test_arxiv_deduplicates_urls():
    feed_xml = (FIXTURES / "arxiv_feed.xml").read_text()
    since = datetime(2026, 3, 2, 0, 0, tzinfo=timezone.utc)
    parsed = feedparser.parse(feed_xml)

    with patch("digest.sources.arxiv.feedparser") as mock_fp:
        # Return same feed for all 4 category feeds — should still dedupe
        mock_fp.parse.return_value = parsed
        source = ArxivSource()
        articles = source.fetch(since)

    urls = [a.url for a in articles]
    assert len(urls) == len(set(urls))
