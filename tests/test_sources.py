from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import feedparser

from digest.sources.quanta import QuantaSource
from digest.sources.scientific_american import ScientificAmericanSource

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


class FakeResponse:
    status_code = 200
    def __init__(self, text):
        self.text = text
    def raise_for_status(self):
        pass


def test_sciam_parses_json_ld():
    html = (FIXTURES / "sciam_page.html").read_text()
    since = datetime(2026, 3, 4, 0, 0, tzinfo=timezone.utc)

    with patch("digest.sources.scientific_american.httpx.get") as mock_get:
        mock_get.return_value = FakeResponse(html)
        source = ScientificAmericanSource()
        articles = source.fetch(since)

    # Should get 3 articles (2 real + 1 climate), podcast excluded by URL
    assert len(articles) == 3
    urls = [a.url for a in articles]
    assert not any("/podcast/" in u for u in urls)


def test_sciam_excludes_old_articles():
    html = (FIXTURES / "sciam_page.html").read_text()
    since = datetime(2026, 3, 5, 0, 0, tzinfo=timezone.utc)

    with patch("digest.sources.scientific_american.httpx.get") as mock_get:
        mock_get.return_value = FakeResponse(html)
        source = ScientificAmericanSource()
        articles = source.fetch(since)

    # Only Mar 5 articles
    assert all(a.published.day == 5 for a in articles)
